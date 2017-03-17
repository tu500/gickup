import subprocess
import sys
import os
import json

#DEFAULT_HOME_DIR = os.path.join(os.path.expanduser('~'), '.gitbackup')
DEFAULT_SETTINGS = {
    'repos': {},
    'localbasepath': None,
    'servers': [
        # ('user@server.example.com', 'serverbasepath'),
    ],
    'github_users': [
        # 'username',
    ],
    'dateformat': '%Y-%m-%d/%H-%M-%S',
}


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
        l.append(os.path.join(os.environ['XDG_DATA_HOME'], 'gitbackup'))
    if 'XDG_CONFIG_HOME' in os.environ:
        l.append(os.path.join(os.environ['XDG_CONFIG_HOME'], 'gitbackup'))
    l.append(os.path.join('~', '.gitbackup', 'backup'))
    return [os.path.expanduser(i) for i in l]

def get_config_file_candidates():
    l = []
    if 'XDG_CONFIG_HOME' in os.environ:
        l.append(os.path.join(os.environ['XDG_CONFIG_HOME'], 'gitbackup.conf'))
    l.append(os.path.join('~', '.gitbackup', 'settings'))
    return [os.path.expanduser(i) for i in l]


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
        choice = input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n")
