import os
import sys
from pprint import pprint
from timeit import default_timer as timer
from datetime import datetime, timedelta

from mkdocs import utils as mkdocs_utils
from mkdocs.config import config_options, Config
from mkdocs.plugins import BasePlugin

from git import Repo, Commit
import requests, json
import time
import hashlib

class GitCommittersPlugin(BasePlugin):

    config_scheme = (
        ('enterprise_hostname', config_options.Type(mkdocs_utils.string_types, default='')),
        ('repository', config_options.Type(mkdocs_utils.string_types, default='')),
        ('branch', config_options.Type(mkdocs_utils.string_types, default='master')),
        ('docs_path', config_options.Type(mkdocs_utils.string_types, default='docs/')),
        ('token', config_options.Type(mkdocs_utils.string_types, default='')),
    )

    def __init__(self):
        self.total_time = 0
        self.branch = 'master'
        self.git_enabled = False
        self.authors = dict()

    def on_config(self, config):
        if 'MKDOCS_GIT_COMMITTERS_APIKEY' in os.environ:
            self.config['token'] = os.environ['MKDOCS_GIT_COMMITTERS_APIKEY']
        if self.config['token'] and self.config['token'] != '':
            self.git_enabled = True
            self.auth_header = {'Authorization': 'token ' + self.config['token'] }
            if self.config['enterprise_hostname'] and self.config['enterprise_hostname'] != '':
                self.apiendpoint = "https://" + self.config['enterprise_hostname'] + "/api/graphql"
            else:
                self.apiendpoint = "https://api.github.com/graphql"
            print("git-committers plugin: fetching git commits info...")
        self.localrepo = Repo(".")
        self.branch = self.config['branch']
        return config

    def get_gituser_info(self, email, query):
        if not self.git_enabled:
            return None
        r = requests.post(url=self.apiendpoint, json=query, headers=self.auth_header)
        res = r.json()
        if r.status_code == 200:
            if res.get('data'):
                if res['data']['search']['edges']:
                    info = res['data']['search']['edges'][0]['node']
                    return {'login':info['login'], \
                            'name':info['name'], \
                            'url':info['url'], \
                            'repos':info['url'], \
                            'avatar':info['url']+".png?size=24" }
                else:
                    return None
            else:
                print("Error: " + res['errors'][0]['message'])
                return None
        else:
            return None

    def get_git_info(self, path):
        unique_authors = []
        seen_authors = []
        last_commit_date = ""
        # print("get_git_info for " + path)
        for c in Commit.iter_items(self.localrepo, self.localrepo.head, path):
            if not last_commit_date:
                # Use the last commit and get the date
                last_commit_date = time.strftime("%Y-%m-%d", time.gmtime(c.authored_date))
            c.author.email = c.author.email.lower()
            if not (c.author.email in self.authors):
                # Not in cache: let's ask GitHub
                self.authors[c.author.email] = {}
                # First, search by email
                info = self.get_gituser_info( c.author.email, \
                    { 'query': '{ search(type: USER, query: "in:email ' + c.author.email + '", first: 1) { edges { node { ... on User { login name url } } } } }' })
                if info:
                    self.authors[c.author.email] = info
                else:
                    # If not found, search by name
                    info = self.get_gituser_info( c.author.name, \
                        { 'query': '{ search(type: USER, query: "in:name ' + c.author.name + '", first: 1) { edges { node { ... on User { login name url } } } } }' })
                    if info:
                        self.authors[c.author.email] = info
                    else:
                        # If not found, use local git info only and gravatar avatar
                        self.authors[c.author.email] = { 'login':'', \
                            'name':c.author.name if c.author.name else '', \
                            'url':'', \
                            'avatar':'https://www.gravatar.com/avatar/' + hashlib.md5(c.author.email.encode('utf-8')).hexdigest() + '?d=identicon' }
            if c.author.email not in seen_authors:
                seen_authors.append(c.author.email)
                unique_authors.append(self.authors[c.author.email])
                #print("  Author: "+ self.authors[c.author.email]['name'] + " ("+ str(self.authors[c.author.email]['email'])+ ")")

        return unique_authors, last_commit_date

    def on_page_context(self, context, page, config, nav):
        context['committers'] = []
        start = timer()
        git_path = self.config['docs_path'] + page.file.src_path
        authors, last_commit_date = self.get_git_info(git_path)
        if authors:
            context['committers'] = authors
        if last_commit_date:
            context['last_commit_date'] = last_commit_date
        end = timer()
        self.total_time += (end - start)

        return context
