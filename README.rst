Gickup
======

This is a script for backing up multiple git repos, keeping local timestamped
copies of all available branches.

Features
--------

* Save state of all remote branches into local branches by current date/time
* Keep track of backed up repositories, automatic batch backup of all known repos
* Configure repository "indices"

  * Scan servers for git repos to auto-add them (using ``ssh find``)
  * Scan github user for repos to auto-add them

How to use
----------

.. code:: bash

  # Add new repo to backup list manually
  gickup addrepo ssh://user@example.com
  gickup addrepo https://github.com/user/example.git
  gickup addrepo /some/local/path

  # Optionally specify a target directory
  gickup addrepo ssh://user@example.com /target/dir

  # Add github users / ssh server to watch for new repos
  gickup addindex --type github user
  gickup addindex github://anotheruser
  gickup addindex user@example.com:remote/path

  # Then scan for unknown repos
  gickup updaterepolist
  ...

  # Or scan without configuring
  gickup updaterepolist --type github user
  ...
  gickup updaterepolist user@example.com:remote/path
  ...

  # Now do a backup of all known repos
  gickup dobackup

  # ... or a specific one
  gickup dobackup /local/backup/path

Settings
--------

``dateformat``
  formatstring used to save remote branches into (``backup/<date>/<name>``)

``localbasepath``
  directory where backups will be located by default

``repos``
  configured repos and respective backup directories

``servers``
  tuples of server-url (with user part) and server-path which will be scanned
  for new repos by updaterepolist.

``github_users``
  a list of github usernames which will be scanned for new repos by
  updaterepolist.

Why "Gickup"?
-------------

Well, every project needs a name and https://github.com/sciunto-org/gitbackup
beat me to the obvious one.

On this occasion: Thank you to the one who gave me the suggestion.

License
-------

Gickup is licensed under the AGPLv3 or later, see ``LICENSE.txt``.

Apart from that I'm open to discussion. If you need a different license feel
free to contact me.

See also
--------

* https://github.com/sciunto-org/gitbackup
* https://github-backup.branchable.com/
