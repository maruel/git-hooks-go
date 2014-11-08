#!/usr/bin/env python
# Copyright 2014 Marc-Antoine Ruel. All rights reserved.
# Use of this source code is governed under the Apache License, Version 2.0
# that can be found in the LICENSE file.

"""Installs all packages needed at runtime by presubmit.py."""

import logging
import optparse
import subprocess
import sys
import threading


def check_or_install(tool, url, exitcode=1):
  """Tries to run a command to see if the command exists.

  If not, automatically install it.
  """
  try:
    logging.info('%s', ' '.join(tool))
    p = subprocess.Popen(
        tool, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    p.communicate()
    if p.returncode == exitcode:
      return
  except OSError:
    pass
  sys.stdout.write('Warning: installing %s\n' % url)
  subprocess.check_call(['go', 'get', '-u', url])


def install_prerequisites():
  to_install = [
    (['errcheck', '-h'], 'github.com/kisielk/errcheck', 2),
    (['goimports', '-h'], 'code.google.com/p/go.tools/cmd/goimports', 2),
    (['golint', '-h'], 'github.com/golang/lint/golint', 2),
    (['goveralls', '-h'], 'github.com/mattn/goveralls', 2),
    (['gocov', '-h'], 'github.com/axw/gocov/gocov', 2),
    (['go', 'tool', 'cover', '-h'], 'code.google.com/p/go.tools/cmd/cover', 1),
    (['go', 'tool', 'vet', '-h'], 'code.google.com/p/go.tools/cmd/vet', 1),
  ]
  threads = []
  for cmd, url, exitcode in to_install:
    t = threading.Thread(
        name=url, target=check_or_install, args=(cmd, url, exitcode))
    t.start()
    threads.append(t)
  for t in threads:
    t.join()
  print('Prerequisites check completed.')
  return 0


def main(run_golint=True, run_govet=True):
  parser = optparse.OptionParser(description=sys.modules[__name__].__doc__)
  parser.add_option(
      '-v', '--verbose', action='store_true', help='Logs what is being run')
  options, args = parser.parse_args()
  if args:
    parser.error('Unknown args: %s' % args)
  logging.basicConfig(
      level=logging.DEBUG if options.verbose else logging.ERROR,
      format='%(levelname)-5s: %(message)s')

  return install_prerequisites()


if __name__ == '__main__':
  sys.exit(main())
