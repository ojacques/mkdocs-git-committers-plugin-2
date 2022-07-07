import os
import sys
import logging
from pprint import pprint
from timeit import default_timer as timer
from datetime import datetime, timedelta

from mkdocs import utils as mkdocs_utils
from mkdocs.config import config_options, Config
from mkdocs.plugins import BasePlugin

from git import Git, Commit
import requests, json
import time
import hashlib
import re

LOG = logging.getLogger("mkdocs.plugins." + __name__)

class GitCommittersPlugin(BasePlugin):

    config_scheme = (
        ('enterprise_hostname', config_options.Type(str, default='')),
        ('repository', config_options.Type(str, default='')),
        ('branch', config_options.Type(str, default='master')),
        ('docs_path', config_options.Type(str, default='docs/')),
        ('token', config_options.Type(str, default='')),
        ('enabled', config_options.Type(bool, default=True)),
        ('cache_dir', config_options.Type(str, default='.cache/plugin/git-committers')),
    )

    def __init__(self):
        self.total_time = 0
        self.branch = 'master'
        self.enabled = True
        self.authors = dict()
        self.id_for_email = dict()
        self.auth_header = dict()
        self.repo_owner = ''
        self.repo_name = ''

    def on_config(self, config):
        self.enabled = self.config['enabled']
        if not self.enabled:
            LOG.info("git-committers plugin DISABLED")
            return config

        LOG.info("git-committers plugin ENABLED")
        if not self.config['token'] and 'MKDOCS_GIT_COMMITTERS_APIKEY' in os.environ:
            self.config['token'] = os.environ['MKDOCS_GIT_COMMITTERS_APIKEY']

        if self.config['token'] and self.config['token'] != '':
            self.auth_header = {'Authorization': 'token ' + self.config['token'] }
        else:
            LOG.warning("no git token provided in GH_TOKEN environment variable")
        if self.config['enterprise_hostname'] and self.config['enterprise_hostname'] != '':
            self.apiendpoint = "https://" + self.config['enterprise_hostname'] + "/api/graphql"
        else:
            self.apiendpoint = "https://api.github.com/graphql"
        self.localgit = Git(".")
        self.branch = self.config['branch']
        self.repo_owner, self.repo_name = self.config['repository'].split('/')
        return config

    def get_gitcommit_info(self, query):
        r = requests.post(url=self.apiendpoint, json=query, headers=self.auth_header)
        res = r.json()
        if r.status_code == 200:
            if res['data'] and res['data']['repository']:
                info = res['data']['repository']['object']['author']['user']
                if info:
                    return {'login':info['login'], \
                            'name':info['name'], \
                            'url':info['url'], \
                            'avatar':info['url']+".png" }
                else:
                    return None
            else:
                LOG.warning("Error from GitHub GraphQL call: " + res['errors'][0]['message'])
                return None
        else:
            return None

    
    def get_gituser_info(self, query):
        if not hasattr(self, 'auth_header'):
            # No auth token provided: return now
            return None
        r = requests.post(url=self.apiendpoint, json=query, headers=self.auth_header)
        res = r.json()
        if r.status_code == 200:
            if res.get('data'):
                if res['data']['search']['edges']:
                    info = res['data']['search']['edges'][0]['node']
                    if info:
                        return {'login':info['login'], \
                                'name':info['name'], \
                                'url':info['url'], \
                                'avatar':info['url']+".png" }
                    else:
                        return None
                else:
                    return None
            else:
                LOG.warning("Error from GitHub GraphQL call: " + res['errors'][0]['message'])
                return None
        else:
            return None

    def get_git_info(self, path, pre_run = False):
        if not self.enabled:
            return None
        unique_authors = []
        seen_authors = []
        last_commit_date = ""
        LOG.debug("get_git_info for " + path)

        for hexsha, email, name, timestamp in [x.split('|') for x in self.localgit.log('--pretty=%H|%ae|%an|%at','-m', '--follow', '--', path).split('\n')]:
            author_id = ""
            if not last_commit_date:
                # Use the last commit and get the date
                last_commit_date = time.strftime("%Y-%m-%d", time.gmtime(int(timestamp)))
            email = email.lower()
            
            if email in self.id_for_email:
                # Already in cache
                author_id = self.id_for_email[email]
                info = self.authors[author_id]
            elif email in self.authors and not pre_run:
                # No chance with git requests once pre-run is over
                author_id = email
                info = self.authors[author_id]
            else:
                # Not in cache: let's ask GitHub
                #self.authors[email] = {}
                LOG.info("Get user info from GitHub for: " + email + " based on commit " + hexsha)
                info = self.get_gitcommit_info( { 'query': """
                        {
                            repository(owner: \"""" + self.repo_owner + '", name: "' + self.repo_name + """\") {
                                    object(oid: \"""" + hexsha + """\") {
                                    ... on Commit {
                                        author {
                                            user {
                                                login
                                                name
                                                url
                                            }
                                        }
                                    }
                                }
                            }
                        }"""})
                if not info:
                    # If not found, search by email
                    LOG.info("Commit-based search failed, falling back on user-based search")
                    info = self.get_gituser_info( { 'query': '{ search(type: USER, query: "in:email ' + email + '", first: 1) { edges { node { ... on User { login name url } } } } }' })
                    if not info:
                        # If not found, search by name
                        LOG.debug("   User not found by email, search by name: " + name)
                        info = self.get_gituser_info( { 'query': '{ search(type: USER, query: "in:name ' + name + '", first: 1) { edges { node { ... on User { login name url } } } } }' })
                        if not info:
                            # If not found, search by name, expecting it to be GitHub user name
                            LOG.debug("   User not found yet, trying with GitHub username: " + name)
                            info = self.get_gituser_info( { 'query': '{ search(type: USER, query: "in:user ' + name + '", first: 1) { edges { node { ... on User { login name url } } } } }' })
                if info:
                    LOG.debug("      Found!")
                    author_id = info['login']
                    self.id_for_email[email] = author_id
                    if author_id in self.authors:
                        # Another email of a known user
                        self.authors[author_id]['emails'].append(email)
                    else:
                        info['emails'] = [email]
                        self.authors[author_id] = info
                else:
                    # If not found, use local git info only and gravatar avatar
                    author_id = email
                    info = { 'login':name if name else '', \
                        'name':name if name else email, \
                        'url':'#', \
                        'avatar':'https://www.gravatar.com/avatar/' + hashlib.md5(email.encode('utf-8')).hexdigest() + '?d=identicon', \
                        'emails':[email] }
                    self.authors[author_id] = info

            if (author_id not in seen_authors):
                LOG.debug("Adding " + author_id + " to unique authors for this page")
                seen_authors.append(author_id)
                unique_authors.append(self.authors[author_id])

        LOG.debug("Contributors for page " + path + ": " + str(unique_authors))
        return unique_authors, last_commit_date

    def on_page_context(self, context, page, config, nav):
        context['committers'] = []
        if not self.enabled:
            return context
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

    def on_pre_build(self, config):
        if os.path.exists(self.config['cache_dir'] + "/authors.json"):
            LOG.info("git-committers: loading authors cache file")
            f = open(self.config['cache_dir'] + "/authors.json", "r")
            self.authors = json.loads(f.read())
            for id, info in self.authors.items():
                for email in info['emails']:
                    self.id_for_email[email] = id
            f.close()
        # Should execute for all files at build, to guarantee consistent output
        for dirpath, dirnames, filenames in os.walk(self.config['docs_path']):
            for filename in [f for f in filenames if f.endswith(".md")]:
                self.get_git_info(os.path.join(dirpath, filename), pre_run = True)
        
        LOG.info("git-committers: saving authors cache file")
        json_data = json.dumps(self.authors)
        os.makedirs(self.config['cache_dir'], exist_ok=True)
        f = open(self.config['cache_dir'] + "/authors.json", "w")
        f.write(json_data)
        f.close()
