import os
import sys
import logging
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
            LOG.warning("no git token provided and MKDOCS_GIT_COMMITTERS_APIKEY environment variable is not defined")
        if self.config['enterprise_hostname'] and self.config['enterprise_hostname'] != '':
            self.apiendpoint = "https://" + self.config['enterprise_hostname'] + "/api/graphql"
        else:
            self.apiendpoint = "https://api.github.com/graphql"
        self.localrepo = Repo(".")
        self.branch = self.config['branch']
        return config

    def get_gituser_info(self, email, query):
        if not hasattr(self, 'auth_header'):
            # No auth token provided: return now
            return None
        r = requests.post(url=self.apiendpoint, json=query, headers=self.auth_header)
        if r.status_code == 200:
            res = r.json()
            LOG.debug("   GraphQL ret code=" + str(r.status_code) + " - JSON: " + str(res))
            if res.get('data'):
                if res['data']['search']['edges']:
                    if(len(res['data']['search']['edges']) == 1):
                        info = res['data']['search']['edges'][0]['node']
                        if info:
                            return {'login':info['login'], \
                                    'name':info['name'], \
                                    'url':info['url'], \
                                    'avatar':info['url']+".png" }
                        else:
                            return None
                    else:
                        LOG.info("   Found more than one user matching on GitHub - ignoring result")
                        return None
                else:
                    return None
            else:
                LOG.warning("   Error from GitHub GraphQL call: " + res['errors'][0]['message'])
                return None
        else:
            LOG.warning("   Error from GitHub GraphQL call: " + res['message'])
            return None

    def get_git_info(self, path):
        unique_authors = []
        seen_authors = []
        last_commit_date = ""
        LOG.debug("get_git_info for " + path)
        for c in Commit.iter_items(self.localrepo, self.localrepo.head, path):
            author_id = ""
            if not last_commit_date:
                # Use the last commit and get the date
                last_commit_date = time.strftime("%Y-%m-%d", time.gmtime(c.authored_date))
            c.author.email = c.author.email.lower()
            # Clean up the email address
            c.author.email = re.sub('\d*\+', '', c.author.email.replace("@users.noreply.github.com", ""))
            if not (c.author.email in self.authors) and not (c.author.name in self.authors):
                # Not in cache: let's ask GitHub
                #self.authors[c.author.email] = {}
                # First, search by email
                LOG.info("Get user info from GitHub with user's publicly visible profile email: " + c.author.email)
                info = self.get_gituser_info( c.author.email, \
                    { 'query': '{ search(type: USER, query: "in:email ' + c.author.email + '", first: 2) { edges { node { ... on User { login name url } } } } }' })
                if info:
                    LOG.info("      Found " + info['login'])
                    author_id = c.author.email
                else:
                    # If not found, search by name, expecting it to be GitHub user name
                    LOG.info("   User not found yet, trying with GitHub username used to login: " + c.author.name)
                    info = self.get_gituser_info( c.author.name, \
                        { 'query': '{ search(type: USER, query: "in:login ' + c.author.name + '", first: 2) { edges { node { ... on User { login name url } } } } }' })
                    if info:
                        LOG.info("      Found " + info['login'])
                        author_id = c.author.name
                    else:
                        # If not found, search by name
                        LOG.info("   User not found yet, search by  user's public profile name: " + c.author.name)
                        info = self.get_gituser_info( c.author.name, \
                            { 'query': '{ search(type: USER, query: "in:name ' + c.author.name + '", first: 2) { edges { node { ... on User { login name url } } } } }' })
                        if info:
                            LOG.info("      Found " + info['login'])
                            author_id = c.author.name
                        else:
                            # If not found, use local git info only and gravatar avatar
                            LOG.info("      Falling back to user info from local GIT for: " + c.author.name)
                            info = { 'login':c.author.name if c.author.name else '', \
                                'name':c.author.name if c.author.name else c.author.email, \
                                'url':'#', \
                                'avatar':'https://www.gravatar.com/avatar/' + hashlib.md5(c.author.email.encode('utf-8')).hexdigest() + '?d=identicon' }
                            author_id = c.author.name
            else:
                # Already in cache
                if c.author.email in self.authors:
                    info = self.authors[c.author.email]
                    author_id = c.author.email
                else:
                    info = self.authors[c.author.name]
                    author_id = c.author.name
            if (author_id not in seen_authors):
                LOG.debug("Adding " + author_id + " to unique authors for this page")
                self.authors[author_id] = info
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

    def on_post_build(self, config):
        LOG.info("git-committers: saving authors cache file")
        json_data = json.dumps(self.authors)
        os.makedirs(self.config['cache_dir'], exist_ok=True)
        f = open(self.config['cache_dir'] + "/authors.json", "w")
        f.write(json_data)
        f.close()

    def on_pre_build(self, config):
        if os.path.exists(self.config['cache_dir'] + "/authors.json"):
            LOG.info("git-committers: loading authors cache file")
            f = open(self.config['cache_dir'] + "/authors.json", "r")
            self.authors = json.loads(f.read())
            f.close()
