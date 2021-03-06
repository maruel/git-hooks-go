#!/usr/bin/env python
# Copyright 2014 Marc-Antoine Ruel. All rights reserved.
# Use of this source code is governed under the Apache License, Version 2.0
# that can be found in the LICENSE file.

"""Installs git pre-commit hook on the repository one directory above."""

import os
import shutil
import subprocess
import sys


THIS_DIR = os.path.dirname(os.path.abspath(__file__))


def main():
  os.chdir(THIS_DIR)
  returncode = subprocess.call([sys.executable, 'install_prerequisites.py'])
  if returncode:
    return returncode

  try:
    parent = os.path.dirname(THIS_DIR)
    git_dir = subprocess.check_output(
        ['git', 'rev-parse', '--git-dir'],
        cwd=parent).strip()
    git_dir = os.path.normpath(os.path.join(parent, git_dir))
  except subprocess.CalledProcessError:
    print >> sys.stderr, 'Failed to find parent git repository root'
    return 1

  git_hook_dir = os.path.join(git_dir, 'hooks')
  precommit_dest = os.path.join(git_hook_dir, 'pre-commit')
  if os.path.isfile(precommit_dest):
    # Better be safe than sorry.
    print >> sys.stderr, '%s already exist, aborting' % precommit_dest
    return 1

  if sys.platform == 'win32':
    # This means it'll get stale on Windows.
    shutil.copyfile(os.path.join(THIS_DIR, 'pre-commit'), precommit_dest)
  else:
    relpath = os.path.relpath(THIS_DIR, git_hook_dir)
    os.symlink(os.path.join(relpath, 'pre-commit'), precommit_dest)
  print('Installed %s' % precommit_dest)
  return 0


if __name__ == '__main__':
  sys.exit(main())
