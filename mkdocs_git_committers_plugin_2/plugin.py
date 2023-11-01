import os
import logging
from pprint import pprint
from timeit import default_timer as timer
from datetime import datetime, timedelta

from mkdocs import utils as mkdocs_utils
from mkdocs.config import config_options, Config
from mkdocs.plugins import BasePlugin

from git import Repo, Commit
import requests, json
from requests.exceptions import HTTPError
import time

from mkdocs_git_committers_plugin_2.exclude import exclude

LOG = logging.getLogger("mkdocs.plugins." + __name__)

class GitCommittersPlugin(BasePlugin):

    config_scheme = (
        ('enterprise_hostname', config_options.Type(str, default='')),
        ('repository', config_options.Type(str, default='')),
        ('branch', config_options.Type(str, default='master')),
        ('docs_path', config_options.Type(str, default='docs/')),
        ('enabled', config_options.Type(bool, default=True)),
        ('cache_dir', config_options.Type(str, default='.cache/plugin/git-committers')),
        ("exclude", config_options.Type(list, default=[])),
        ('token', config_options.Type(str, default='')),
    )

    def __init__(self):
        self.total_time = 0
        self.branch = 'master'
        self.enabled = True
        self.authors = dict()
        self.cache_page_authors = dict()
        self.exclude = list()
        self.cache_date = ''

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
            LOG.warning("git-committers plugin now requires a GitHub token. Set it under 'token' mkdocs.yml config or MKDOCS_GIT_COMMITTERS_APIKEY environment variable.")
        if not self.config['repository']:
            LOG.error("git-committers plugin: repository not specified")
            return config
        if self.config['enterprise_hostname'] and self.config['enterprise_hostname'] != '':
            self.githuburl = "https://" + self.config['enterprise_hostname'] + "/api/graphql"
        else:
            self.githuburl = "https://api.github.com/graphql"
        self.localrepo = Repo(".")
        self.branch = self.config['branch']
        self.excluded_pages = self.config['exclude']
        return config

    # Get unique contributors for a given path using GitHub GraphQL API
    def get_contributors_to_path(self, path):
            # Query GraphQL API, and get a list of unique authors
            query = {
                    "query": """
                    {
                        repository(owner: "%s", name: "%s") {
                            object(expression: "%s") {
                                ... on Commit {
                                    history(first: 100, path: "%s") {
                                        nodes {
                                            author {
                                                user {
                                                    login
                                                    name
                                                    url
                                                    avatarUrl
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                    """ % (self.config['repository'].split('/')[0], self.config['repository'].split('/')[1], self.branch, path)
            }
            authors = []
            if not hasattr(self, 'auth_header'):
                    # No auth token provided: return now
                    return None
            LOG.info("git-committers: fetching contributors for " + path)
            LOG.debug("   from " + self.githuburl)
            r = requests.post(url=self.githuburl, json=query, headers=self.auth_header)
            res = r.json()
            #print(res)
            if r.status_code == 200:
                    if res.get('data'):
                            if res['data']['repository']['object']['history']['nodes']:
                                    for node in res['data']['repository']['object']['history']['nodes']:
                                            # If user is not None (GitHub user was deleted)
                                            if node['author']['user']:
                                                login = node['author']['user']['login']
                                                if login not in [author['login'] for author in authors]:
                                                        authors.append({'login': node['author']['user']['login'],
                                                                        'name': node['author']['user']['name'],
                                                                        'url': node['author']['user']['url'],
                                                                        'avatar': node['author']['user']['avatarUrl']})
                                    return authors
                            else:
                                    return []
                    else:
                            LOG.warning("git-committers: Error from GitHub GraphQL call: " + res['errors'][0]['message'])
                            return []
            else:
                    return []
            return []
        
    def list_contributors(self, path):
        if exclude(path.lstrip(self.config['docs_path']), self.excluded_pages):
            return None, None
        
        last_commit_date = ""
        path = path.replace("\\", "/")
        for c in Commit.iter_items(self.localrepo, self.localrepo.head, path):
            if not last_commit_date:
                # Use the last commit and get the date
                last_commit_date = time.strftime("%Y-%m-%d", time.gmtime(c.authored_date))

        # File not committed yet
        if last_commit_date == "":
            last_commit_date = datetime.now().strftime("%Y-%m-%d")
            return [], last_commit_date

        # Use the cache if present if cache date is newer than last commit date
        if path in self.cache_page_authors:
            if self.cache_date and time.strptime(last_commit_date, "%Y-%m-%d") < time.strptime(self.cache_date, "%Y-%m-%d"):
                return self.cache_page_authors[path]['authors'], self.cache_page_authors[path]['last_commit_date']

        authors=[]
        authors = self.get_contributors_to_path(path)
        
        self.cache_page_authors[path] = {'last_commit_date': last_commit_date, 'authors': authors}

        return authors, last_commit_date

    def on_page_context(self, context, page, config, nav):
        context['committers'] = []
        if not self.enabled:
            return context
        start = timer()
        git_path = self.config['docs_path'] + page.file.src_path
        authors, last_commit_date = self.list_contributors(git_path)
        if authors:
            context['committers'] = authors
        if last_commit_date:
            context['last_commit_date'] = last_commit_date
        end = timer()
        self.total_time += (end - start)

        return context

    def on_post_build(self, config):
        LOG.info("git-committers: saving page authors cache file")
        json_data = json.dumps({'cache_date': datetime.now().strftime("%Y-%m-%d"), 'page_authors': self.cache_page_authors})
        os.makedirs(self.config['cache_dir'], exist_ok=True)
        f = open(self.config['cache_dir'] + "/page-authors.json", "w")
        f.write(json_data)
        f.close()

    def on_pre_build(self, config):
        if os.path.exists(self.config['cache_dir'] + "/page-authors.json"):
            LOG.info("git-committers: found page authors cache file - loading it")
            f = open(self.config['cache_dir'] + "/page-authors.json", "r")
            cache = json.loads(f.read())
            self.cache_date = cache['cache_date']
            self.cache_page_authors = cache['page_authors']
            f.close()
