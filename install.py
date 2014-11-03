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
  try:
    git_dir = subprocess.check_output(
        ['git', 'rev-parse', '--git-dir'],
        cwd=os.path.dirname(THIS_DIR)).strip()
  except subprocess.CalledProcessError:
    print >> sys.stderr, 'Failed to find parent git repository root'
    return 1

  git_hook_dir = os.path.join(git_dir, 'hooks')
  precommit_dest = os.path.join(git_hook_dir, 'pre-commit')
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
