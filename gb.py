#!/usr/bin/python3

import os
import argparse
import shutil
from datetime import datetime

import helpers
import gblib


def run_updaterepolist(args, settings):
    if args.target is None:
        newrepos = {}

        # for every server do a 'find' to search git repos
        for serveraddress, serverbasepath in settings['servers']:
            newrepos.update(gblib.get_repo_list_ssh(serveraddress, serverbasepath, settings))

        # for every github user query the api to find all the user's repos
        for username in settings['github_users']:
            newrepos.update(gblib.get_repo_list_github(username, settings))

    elif args.type == 'ssh' or (args.type == 'auto' and ':' in args.target):
        newrepos = gblib.get_repo_list_ssh(*args.target.split(':', 1), settings=settings)

    else:
        newrepos = gblib.get_repo_list_github(args.target, settings)


    # only consider unknown repos
    newrepos = {url:path for url, path in newrepos.items() if not url in settings['repos']}


    if not newrepos:
        print('No unknown repos found.')
        return


    # ask whether to really add found repos
    print('New repos:')
    for k, v in newrepos.items():
        print('Repo {} backed up in {}'.format(k,v))
    b = helpers.query_yes_no('Add and initialize new repos?')

    if b:
        print('Saving new repos.')
        for k, v in newrepos.items():
            gblib.init_repo(k, v)
            settings['repos'][k] = v
        helpers.savesettings(args.configfile, settings)
    else:
        print('Not saving new repos.')


def run_dobackup(args, settings):
    if args.localpath:
        paths = [os.path.abspath(os.path.expanduser(p)) for p in args.localpath]
        repos = [gblib.Repo(p) for p in paths]
    else:
        repos = [gblib.Repo(v) for v in settings['repos'].values()]

    for repo in repos:
        print('Syncing {}'.format(repo.git_dir))
        repo.fetch(
            refspec='refs/heads/*:refs/heads/backup/{}/*'.format(
                datetime.now().strftime(settings['dateformat'])
            ))


def run_addrepo(args, settings):
    bpath = args.backuppath
    if bpath is not None:
        bpath = os.path.expanduser(bpath)
    else:
        bpath = gblib.generate_backup_path_from_url(args.repourl)

    if not os.path.isabs(bpath):
        bpath = os.path.join(settings['localbasepath'], bpath)

    url = args.repourl
    uri_type, target = gblib.url_split_type_target(url)

    if uri_type == 'file':
        url = os.path.abspath(os.path.expanduser(target))

    gblib.init_repo(url, bpath)

    settings['repos'][url] = bpath
    helpers.savesettings(args.configfile, settings)


def run_setconfig(args, settings):
    settings[args.name] = args.newvalue
    helpers.savesettings(args.configfile, settings)


def run_addserver(args, settings):
    v = tuple(args.serverurl.split(':', 1))

    if v in settings['servers']:
        print('Server already configured.')
    else:
        settings['servers'].append(v)
        helpers.savesettings(args.configfile, settings)


def run_add_github_user(args, settings):
    if args.username in settings['github_users']:
        print('Username already configured.')
    else:
        settings['github_users'].append(args.username)
        helpers.savesettings(args.configfile, settings)


def run_removerepo(args, settings):
    p = os.path.expanduser(args.backuppath)
    if not os.path.isabs(p):
        p = os.path.join(settings['localbasepath'], p)
    p = os.path.abspath(p)
    matching_repos = [(k,v) for k,v in settings['repos'].items() if v==p]

    if len(matching_repos) == 0:
        print('Repository {} not configured.'.format(p))
    elif len(matching_repos) > 1:
        print('Multiple repositories configured for {}.'.format(p))
    else:
        k,v = matching_repos[0]

        del settings['repos'][k]
        helpers.savesettings(args.configfile, settings)

        if args.delete_files:
            shutil.rmtree(p)


def run_removeserver(args, settings):
    v = args.serverurl.split(':', 1)

    if not v in settings['servers']:
        print('Server not configured.')
    else:
        settings['servers'].remove(v)
        helpers.savesettings(args.configfile, settings)


def run_remove_github_user(args, settings):
    if not args.username in settings['github_users']:
        print('Username not configured.')
    else:
        settings['github_users'].remove(args.username)
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
    parser_dobackup.add_argument('localpath', nargs='*', help='Local path of the repositories that should be backed up. Needs an initialized git repo at that location. Backs up the origin remote.')
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

    parser_removerepo = subparsers.add_parser('removerepo', help='Remove a configured repo')
    parser_removerepo.add_argument('backuppath', help='Local path configured for the repo to be removed.')
    parser_removerepo.add_argument('--delete-files', dest='delete_files', action='store_true', help='If given, also delete all files of this repo.')
    parser_removerepo.set_defaults(func=run_removerepo)

    parser_removeserver = subparsers.add_parser('removeserver', help='Remove a configured server')
    parser_removeserver.add_argument('serverurl', help='Should be of the form `[user@]example.com:serverpath`')
    parser_removeserver.set_defaults(func=run_removeserver)

    parser_remove_github_user = subparsers.add_parser('remove_github_user', help='Remove a configured github user')
    parser_remove_github_user.add_argument('username')
    parser_remove_github_user.set_defaults(func=run_remove_github_user)


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
