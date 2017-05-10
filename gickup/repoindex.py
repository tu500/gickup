# Copyright (C)  2017  Philip Matura
#
# This file is part of Gickup.
#
# Gickup is free software: you can redistribute it and/or modify it under the
# terms of the GNU Affero General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# Gickup is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU Affero General Public License for more
# details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Gickup. If not, see <http://www.gnu.org/licenses/>.

import os
import json
import subprocess
import urllib.request

from . import gblib


def register_type(type_str):
    def internal(cls):
        cls.uri_type = type_str
        RepoIndex._repo_index_by_type[type_str] = cls
        return cls
    return internal


class RepoIndex(object):
    _repo_index_by_type = {}

    uri_type = None

    def __init__(self, url):
        self.url = url

    def get_list(self, settings):
        raise NotImplementedError('Abstract method')

    def get_settings_tuple(self):
        return (self.uri_type, self.url)

    @staticmethod
    def CreateFromType(uri_type, target):

        if not uri_type in RepoIndex._repo_index_by_type:
            raise ValueError('Unknown url type {} for "{}"'.format(uri_type, target))

        return RepoIndex._repo_index_by_type[uri_type](target)

    @staticmethod
    def CreateFromUrl(url):

        uri_type, target = gblib.url_split_type_target(url)

        if not uri_type in RepoIndex._repo_index_by_type:
            raise ValueError('Unknown url type {} in "{}"'.format(uri_type, url))

        return RepoIndex._repo_index_by_type[uri_type](target)


@register_type('ssh')
class RepoIndexSSH(RepoIndex):

    def __init__(self, url):
        super(RepoIndexSSH, self).__init__(url)
        self.serveraddress, self.serverbasepath = url.split(':', 1)

    def get_list(self, settings):

        newrepos = {}

        dirlist = subprocess.check_output(['ssh', self.serveraddress, 'find', self.serverbasepath, '-type', 'd']).decode()
        for line in dirlist.splitlines():
            if line.endswith('/objects'):
                # got a repo, calculate url, localpath, check if exists
                serverpath = line[:-len('/objects')]
                url = '{}:{}'.format(self.serveraddress, serverpath)
                localpath = os.path.join(settings['localbasepath'], self.serveraddress, serverpath[len(self.serverbasepath)+1:])
                newrepos[url] = localpath

        return newrepos

@register_type('github')
class RepoIndexGithub(RepoIndex):

    def get_list(self, settings):

        newrepos = {}
        username = self.url

        response = urllib.request.urlopen('https://api.github.com/users/{}/repos'.format(username))
        data = response.read().decode()
        repos = json.loads(data)
        for repo in repos:
            localpath = os.path.join(settings['localbasepath'], 'github.com', username, repo['name'])
            newrepos[repo['git_url']] = localpath

        return newrepos
