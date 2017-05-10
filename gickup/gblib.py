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
import subprocess
import re


class Repo(object):
    git_dir = None

    def __init__(self, path):
        self.git_dir = path

    def fetch(self, refspec='', remote='origin'):
        l = self._get_git_args()
        l += ['fetch', remote, refspec]
        subprocess.check_call(l)

    def init(self, bare=True):
        if not os.path.exists(self.git_dir):
            os.makedirs(self.git_dir)

        l = self._get_git_args()
        l += ['init']
        if bare:
            l += ['--bare']
        subprocess.check_call(l)

    def new_remote(self, name, url):
        l = self._get_git_args()
        l += ['remote', 'add', name, url]
        subprocess.check_call(l)

    def _get_git_args(self):
        return ['git', '--git-dir', self.git_dir]


def url_split_type_target(url):
    match = re.match(r'^(\w+)://(.*)$', url)

    if match:
        uri_type = match.group(1)
        target = match.group(2)

    else:
        target = url

        # try to decude type
        if os.path.exists(url):
            uri_type = 'file'
        elif ':' in url:
            uri_type = 'ssh'
        else:
            uri_type = 'http'

    return uri_type, target


def generate_backup_path_from_url(repourl):
    uri_type, target = url_split_type_target(repourl)

    if uri_type == 'file':
        if os.path.isabs(repourl):
            # make relative
            return target[1:]
        else:
            return target

    elif uri_type == 'ssh':
        # user@domain:path -> user@domain/path
        return target.replace(':', os.path.sep, 1)

    else:
        return target


def init_repo(url, localpath):
    print(localpath)
    assert os.path.isabs(localpath)
    assert not os.path.exists(localpath) or not os.listdir(localpath)
    repo = Repo(localpath)
    repo.init(bare=True)
    repo.new_remote(name='origin', url=url)
