GitBackup Python Script
=======================

This is a script for backing up multiple git repos, keeping local timestamped
copies of all available branches.

Features
--------

* Save state of all remote branches into local branches by current date/time
* Keep track of backed up repositories, automatic batch backup of all known repos
* Scan servers for git repos to auto-add them (using `ssh find`)
* Scan github user for repos to auto-add them

How to use
----------

```sh
# Add new repo to backup list manually
gb.py addrepo ssh://user@example.com
gb.py addrepo https://github.com/user/example.git
gb.py addrepo /some/local/path

# Optionally specify a target directory
gb.py addrepo ssh://user@example.com /target/dir

# Add github users / ssh server to watch for new repos
gb.py add_github_user user
gb.py addserver user@example.com:remote/path

# Then scan for unknown repos
gb.py updaterepolist
...

# Or scan without configuring
gb.py updaterepolist --type github user
...
gb.py updaterepolist user@example.com:remote/path
...

# Now do a backup of all known repos
gb.py dobackup

# ... or a specific one
gb.py dobackup /local/backup/path
```

Settings
--------

* `dateformat` formatstring used to save remote branches into
  (`backup/<date>/<name>`)
* `localbasepath` directory where backups will be located by default
* `repos` configured repos and respective backup directories
* `servers` tuples of server-url (with user part) and server-path which will be
  scanned for new repos by updaterepolist.
* `github_users` a list of github usernames which will be scanned for new repos
  by updaterepolist.

See also
--------

* https://github.com/sciunto-org/gitbackup
* https://github-backup.branchable.com/
