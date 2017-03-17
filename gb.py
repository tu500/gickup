#!/usr/bin/python3

import os
import argparse
import subprocess
import urllib.request
import json
import re
import sys
from datetime import datetime

import helpers


def get_repo_list_ssh(serveraddress, serverbasepath, settings):
    # some heuristic, open for a better approach

    newrepos = {}

    dirlist = subprocess.check_output(['ssh', serveraddress, 'find', serverbasepath, '-type', 'd']).decode()
    for line in dirlist.splitlines():
        if line.endswith('/objects'):
            # got a repo, calculate url, localpath, check if exists
            serverpath = line[:-len('/objects')]
            url = '{}:{}'.format(serveraddress, serverpath)
            localpath = os.path.join(settings['localbasepath'], serveraddress, serverpath[len(serverbasepath)+1:])
            if not url in settings['repos']:
                newrepos[url] = localpath

    return newrepos

def get_repo_list_github(username, settings):
    newrepos = {}

    response = urllib.request.urlopen('https://api.github.com/users/{}/repos'.format(username))
    data = response.read().decode()
    repos = json.loads(data)
    for repo in repos:
        localpath = os.path.join(settings['localbasepath'], 'github.com', username, repo['name'])
        newrepos[repo['git_url']] = localpath

    return newrepos


def generate_backup_path_from_url(repourl):
    match = re.match(r'^(\w+)://(.*)$', repourl)

    if match:
        uri_type = match.group(1)
        target = match.group(2)
    else:
        target = repourl

        # try to decude type
        if os.path.exists(repourl):
            uri_type = 'file'
        elif ':' in repourl:
            uri_type = 'ssh'
        else:
            uri_type = 'http'

    if uri_type == 'file':
        if os.path.isabs(repourl):
            # make relative
            return repourl[1:]
        else:
            return repourl

    elif uri_type == 'ssh':
        # user@domain:path -> user@domain/path
        return repourl.replace(':', os.path.sep, 1)

    else:
        return repourl


def run_updaterepolist(args, settings):
    if args.target is None:
        newrepos = {}

        # for every server do a 'find' to search git repos
        for serveraddress, serverbasepath in settings['servers']:
            newrepos.update(get_repo_list_ssh(serveraddress, serverbasepath, settings))

        # for every github user query the api to find all the user's repos
        for username in settings['github_users']:
            newrepos.update(get_repo_list_github(username, settings))

    elif args.type == 'ssh' or (args.type == 'auto' and ':' in args.target):
        newrepos = get_repo_list_ssh(*args.target.split(':', 1), settings=settings)

    else:
        newrepos = get_repo_list_github(args.target, settings)


    # ask whether to really add found repos
    print('New repos:')
    for k, v in newrepos.items():
        print('Repo {} backed up in {}'.format(k,v))
    b = helpers.query_yes_no('Add and sync new repos?')

    if b:
        print('Saving new repos.')
        for k, v in newrepos.items():
            init_repo(k, v)
            settings['repos'][k] = v
        helpers.savesettings(args.configfile, settings)
    else:
        print('Not saving new repos.')



def run_dobackup(args, settings):
    if args.localpath is not None:
        repos = [helpers.Repo(args.localpath)]
    else:
        repos = [helpers.Repo(v) for v in settings['repos'].values()]

    for repo in repos:
        print('Syncing {}'.format(repo.git_dir))
        repo.fetch(
            refspec='refs/heads/*:refs/heads/backup/{}/*'.format(
                datetime.now().strftime(settings['dateformat'])
            ))


def init_repo(url, localpath):
    assert os.path.isabs(localpath)
    repo = helpers.Repo(localpath)
    repo.init(bare=True)
    repo.new_remote(name='origin', url=url)


def run_addrepo(args, settings):
    bpath = args.backuppath
    if bpath is None:
        bpath = generate_backup_path_from_url(args.repourl)
    if not os.path.isabs(bpath):
        bpath = os.path.join(settings['localbasepath'], bpath)

    init_repo(args.repourl, bpath)

    settings['repos'][args.repourl] = bpath
    helpers.savesettings(args.configfile, settings)

def run_setconfig(args, settings):
    settings[args.name] = args.newvalue
    helpers.savesettings(args.configfile, settings)

def run_addserver(args, settings):
    settings['servers'].append(tuple(args.serverurl.split(':', 1)))
    helpers.savesettings(args.configfile, settings)

def run_add_github_user(args, settings):
    if args.username in settings['github_users']:
        print('Username already configured.')
    else:
        settings['github_users'].append(args.username)
        helpers.savesettings(args.configfile, settings)


def main():

    parser = argparse.ArgumentParser(
            description='GitBackup')

    parser.add_argument('--config-file', dest='configfile', help='Configuration file')

    subparsers = parser.add_subparsers(title='Commands')

    parser_updaterepolist = subparsers.add_parser('updaterepolist', help='Check a target server for new, unknown repos. If no target is provided, all configured servers and github users are checked.')
    parser_updaterepolist.add_argument('target', nargs='?', help='May be of the form `[user@]example.com:serverpath` for a server you have ssh access to. Otherwise it is assumed to be a github username.')
    parser_updaterepolist.add_argument('--type', choices=['ssh','github'], default='auto', help='Force how the target value will be interpreted')
    parser_updaterepolist.set_defaults(func=run_updaterepolist)

    parser_dobackup = subparsers.add_parser('dobackup', help='Do a backup of a repository. If no explicit repo is provided, all configured repos will be backed up.')
    parser_dobackup.add_argument('localpath', nargs='?', help='Local path of the repository that should be backed up. Needs an initialized git repo at that location. Backs up the origin remote.')
    parser_dobackup.set_defaults(func=run_dobackup)


    parser_addrepo = subparsers.add_parser('addrepo', help='Add a new repository to the backup list')
    parser_addrepo.add_argument('repourl', help='Url of the repository to be backed up')
    parser_addrepo.add_argument('backuppath', nargs='?', help='Local path to where the repo should be backed up to. Default is <homedir>/backup/<servername>/<reponame>. Relative paths are interpreted relative to <localbasepath>, <homedir>/backup by default.')
    parser_addrepo.set_defaults(func=run_addrepo)

    parser_setconfig = subparsers.add_parser('setconfig', help='Set a config value')
    parser_setconfig.add_argument('name', choices=['dateformat', 'localbasepath'])
    parser_setconfig.add_argument('newvalue')
    parser_setconfig.set_defaults(func=run_setconfig)

    parser_addserver = subparsers.add_parser('addserver', help='Add a server to be checked for new repos')
    parser_addserver.add_argument('serverurl', help='Should be of the form `[user@]example.com:serverpath`')
    parser_addserver.set_defaults(func=run_addserver)

    parser_add_github_user = subparsers.add_parser('add_github_user', help='Add a github user to be checked for new repos')
    parser_add_github_user.add_argument('username')
    parser_add_github_user.set_defaults(func=run_add_github_user)


    args = parser.parse_args()

    if not hasattr(args, 'func'):
        parser.print_help()

    else:

        # set default config file
        if args.configfile is None:

            cf_candidates = helpers.get_config_file_candidates()
            cf = helpers.first_file_existing(cf_candidates)

            if cf is None:
                cf = cf_candidates[0]
                pass #TODO implicit, non existant

            args.configfile = cf

        else:

            args.configfile = os.path.expanduser(args.configfile)

            if not os.path.exists(cf):
                pass #TODO explicitly given, non existant

        # load settings / defaults
        try:
            settings = helpers.loadsettings(args.configfile)
        except FileNotFoundError:
            print('Found no settings file, using defaults.')
            settings = helpers.DEFAULT_SETTINGS

        # set default localbasepath
        if settings['localbasepath'] is None:
            settings['localbasepath'] = helpers.first_file_existing(
                    helpers.get_backup_dir_candidates(),
                    default_first=True
                )

        # run main func
        args.func(args, settings)

if __name__ == '__main__':
    main()
