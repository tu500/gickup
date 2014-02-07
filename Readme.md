GitBackup Python Script
=======================

A rudimentary backup script for multiple git repos. It does its job...

Features
--------

* Scan servers for git repos to auto-add them (using `ssh find`)
* Save all remote branches into local branches `backup/<date>/<name>`

How to use
----------

* Run `gb.py` once
* Modify settings in `~/.gitbackup/settings`
* `gb.py updaterepolist` will scan the configured servers for git repos
* `gb.py addrepo` will add a specific repo to be backed up (takes relative path)
* `gb.py dobackup` will start a backup of all repos

Settings
--------

* `dateformat` formatstring used to save remote branches into
  (`backup/<date>/<name>`)
* `localbasepath` directory where backups will be located by default
* `repos` configured repos and respective backup directories
* `servers` tuples of server-url (with user part) and server-path which will be
  scaned for new repos by updaterepolist.
