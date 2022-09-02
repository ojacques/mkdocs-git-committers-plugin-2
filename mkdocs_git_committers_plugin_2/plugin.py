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
from requests.exceptions import HTTPError
import time
import hashlib
import re
from bs4 import BeautifulSoup as bs

LOG = logging.getLogger("mkdocs.plugins." + __name__)

class GitCommittersPlugin(BasePlugin):

    config_scheme = (
        ('enterprise_hostname', config_options.Type(str, default='')),
        ('repository', config_options.Type(str, default='')),
        ('branch', config_options.Type(str, default='master')),
        ('docs_path', config_options.Type(str, default='docs/')),
        ('enabled', config_options.Type(bool, default=True)),
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

        if not self.config['repository']:
            LOG.error("git-committers plugin: repository not specified")
            return config
        if self.config['enterprise_hostname'] and self.config['enterprise_hostname'] != '':
            self.githuburl = "https://" + self.config['enterprise_hostname'] + "/"
        else:
            self.githuburl = "https://github.com/"
        self.localrepo = Repo(".")
        self.branch = self.config['branch']
        return config

    def list_contributors(self, path):
        last_commit_date = ""
        for c in Commit.iter_items(self.localrepo, self.localrepo.head, path):
            if not last_commit_date:
                # Use the last commit and get the date
                last_commit_date = time.strftime("%Y-%m-%d", time.gmtime(c.authored_date))

        url_contribs = self.githuburl + self.config['repository'] + "/contributors-list/" + self.config['branch'] + "/" + path
        LOG.info("Fetching contributors for " + path)
        LOG.debug("   from " + url_contribs)
        authors=[]
        try:
            response = requests.get(url_contribs)
            response.raise_for_status()
        except HTTPError as http_err:
            LOG.error(f'HTTP error occurred: {http_err}\n(404 is normal if file is not on GitHub yet or Git submodule)')
        except Exception as err:
            LOG.error(f'Other error occurred: {err}')
        else:
            html = response.text
            # Parse the HTML
            soup = bs(html, "lxml")
            lis = soup.find_all('li')
            for li in lis:
                a_tags = li.find_all('a')
                login = a_tags[0]['href'].replace("/", "")
                url = self.githuburl + login
                name = login
                img_tags = li.find_all('img')
                avatar = img_tags[0]['src']
                avatar = re.sub(r'\?.*$', '', avatar)
                authors.append({'login':login, 'name': name, 'url': url, 'avatar': avatar})

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
