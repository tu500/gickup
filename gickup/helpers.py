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

import subprocess
import sys
import os
import json

#DEFAULT_HOME_DIR = os.path.join(os.path.expanduser('~'), '.gickup')
DEFAULT_SETTINGS = {
    'settings_version': 1,
    'repos': {},
    'localbasepath': None,
    'repo_indices': [
        # ('uri_type', 'target'),
    ],
    'dateformat': '%Y-%m-%d/%H-%M-%S',
}


def savesettings(settings_file_path, settings):
    if not os.path.exists(settings_file_path):
        print('Creating settings file `{}`.'.format(settings_file_path))
    if not os.path.exists(os.path.dirname(settings_file_path)):
        os.makedirs(os.path.dirname(settings_file_path))
    with open(settings_file_path, 'w') as f:
        json.dump(settings, f, sort_keys=True, indent=4, separators=(',', ': '))


def loadsettings(settings_file_path):
    with open(settings_file_path, 'r') as f:
        return json.load(f)


def makelocaldir(localbasepath):
    if not os.path.exists(localbasepath):
        print('Creating local backup directory')
        os.makedirs(localbasepath)


def first_file_existing(filenames, default=None, default_first=False):
    for f in filenames:
        if os.path.exists(f):
            return f
    if default_first:
        return filenames[0]
    return default

def get_backup_dir_candidates():
    l = []
    if 'XDG_DATA_HOME' in os.environ:
        l.append(os.path.join(os.environ['XDG_DATA_HOME'], 'gickup'))
    if 'XDG_CONFIG_HOME' in os.environ:
        l.append(os.path.join(os.environ['XDG_CONFIG_HOME'], 'gickup'))
    l.append(os.path.join('~', '.gickup', 'backup'))
    return [os.path.expanduser(i) for i in l]

def get_config_file_candidates():
    l = []
    if 'XDG_CONFIG_HOME' in os.environ:
        l.append(os.path.join(os.environ['XDG_CONFIG_HOME'], 'gickup.conf'))
    l.append(os.path.join('~', '.gickup', 'settings'))
    return [os.path.expanduser(i) for i in l]


def query_yes_no(question, default="yes"):
    """
    Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        May be any valid answer or None (meaning an explicit answer is required
        of the user).

    Return True or False depending on the user's choice.
    """
    valid = {
            "yes": True,
            "y":   True,
            "no":  False,
            "n":   False
        }
    if default is None:
        prompt = " [y/n] "
    elif default in valid:
        b = valid[default]
        prompt = " [Y/n] " if b else " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n")
