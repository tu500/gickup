#!/usr/bin/python

import sys
import subprocess
import os
import json
import urllib2
from os import path
from datetime import datetime

HOME_DIR = path.join(path.expanduser('~'), '.gitbackup')
SETTINGS_FILE = path.join(HOME_DIR, 'settings')

settings = {
    'repos': {},
    'localbasepath': path.join(HOME_DIR, 'backup'),
    'servers': [
        # ('user@server.example.com', 'serverbasepath'),
    ],
    'github_users': [
        # 'username',
    ],
    'dateformat': '%Y-%m-%d/%H-%M-%S',
}


class Repo(object):
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


def query_yes_no(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is one of "yes" or "no".
    """
    valid = {"yes": True,   "y": True,  "ye": True,
             "no": False,     "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = raw_input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n")


def savesettings():
    if not os.path.exists(HOME_DIR):
        os.makedirs(HOME_DIR)
    with open(SETTINGS_FILE, 'wb') as f:
        json.dump(settings, f, sort_keys=True, indent=4, separators=(',', ': '))


def loadsettings():
    global settings
    try:
        with open(SETTINGS_FILE, 'rb') as f:
            settings = json.load(f)
    except:
        print('Found no settings file, using defaults.')
        savesettings()


def makelocaldir():
    if not os.path.exists(settings['localbasepath']):
        print('Creating local backup directory')
        os.makedirs(settings['localbasepath'])


def get_repo_list_ssh(serveraddress, serverbasepath):
    newrepos = {}

    dirlist = subprocess.check_output(['ssh', serveraddress, 'find', serverbasepath, '-type', 'd'])
    for line in dirlist.splitlines():
        if line.endswith('/objects'):
            # got a repo, calculate url, localpath, check if exists
            serverpath = line[:-len('/objects')]
            url = '{}:{}'.format(serveraddress, serverpath)
            localpath = os.path.join(settings['localbasepath'], serveraddress, serverpath[len(serverbasepath)+1:])
            if not url in settings['repos']:
                newrepos[url] = localpath

    return newrepos

def get_repo_list_github(username):
    newrepos = {}

    response = urllib2.urlopen('https://api.github.com/users/{}/repos'.format(username))
    data = response.read()
    repos = json.loads(data)
    for repo in repos:
        localpath = os.path.join(settings['localbasepath'], 'github.com', username, repo['name'])
        newrepos[repo['git_url']] = localpath

    return newrepos


def updaterepolist():
    newrepos = {}

    # for every server do a 'find' to search git repos
    for serveraddress, serverbasepath in settings['servers']:
        newrepos.update(get_repo_list_ssh(serveraddress, serverbasepath))

    # for every github user query the api to find all the user's repos
    for username in settings['github_users']:
        newrepos.update(get_repo_list_github(username))

    # ask whether to really add found repos
    print('New repos:')
    for k, v in newrepos.iteritems():
        print('Repo {} backed up in {}'.format(k,v))
    b = query_yes_no('Add and sync new repos?')

    if b:
        print('Saving new repos.')
        for k, v in newrepos.iteritems():
            addrepo(k, v)
        savesettings()
    else:
        print('Not saving new repos.')


def addrepo(url, localpath):
    p = os.path.abspath(localpath)
    repo = Repo(p)
    repo.init(bare=True)
    repo.new_remote(name='origin', url=url)
    settings['repos'][url] = p


def getrepos():
    # return Repo object for all configured repos
    return [Repo(v) for v in settings['repos'].itervalues()]


def dobackup():
    repos = getrepos()

    for repo in repos:
        print('Syncing {}'.format(repo.git_dir))
        repo.fetch(
            refspec='refs/heads/*:refs/heads/backup/{}/*'.format(
                datetime.now().strftime(settings['dateformat'])
            ))


def add_github_user():
    settings['github_users'].append(sys.argv[2])
    settings['github_users'] = list(set(settings['github_users']))
    savesettings()


def main():
    loadsettings()
    makelocaldir()

    if len(sys.argv) == 1:
        print('Available commands:')
        print('  updaterepolist')
        print('  addrepo remote-url localpath')
        print('  add_github_user username')
        print('  dobackup')
        print('  setconfig key value')
    elif sys.argv[1] == 'addrepo':
        addrepo(sys.argv[2], os.path.join(settings['localbasepath'], sys.argv[3]))
        savesettings()
    elif sys.argv[1] == 'updaterepolist':
        updaterepolist()
    elif sys.argv[1] == 'add_github_user':
        add_github_user()
    elif sys.argv[1] == 'dobackup':
        dobackup()
    elif sys.argv[1] == 'setconfig':
        print('New setting:')
        print('{} = {}'.format(sys.argv[2], sys.argv[3]))
        b = query_yes_no('Apply?')
        if b:
            settings[sys.argv[2]] = sys.argv[3]
            savesettings()
            print('Saving.')
        else:
            print('Not saving.')

if __name__ == '__main__':
    main()
