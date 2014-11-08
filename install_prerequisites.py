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


def check_or_install(cmds, urls, update):
  """Tries to run commands to see if the command exists.

  If not, automatically install it.
  """
  for cmd, exitcode in cmds:
    try:
      logging.info('%s', ' '.join(cmd))
      p = subprocess.Popen(
          cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
      p.communicate()
      if p.returncode != exitcode:
        break
    except OSError:
      break
  else:
    return

  for url in urls:
    sys.stdout.write('Warning: installing %s\n' % url)
    cmd = ['go', 'get']
    if update:
      cmd.append('-u')
    cmd.append(url)
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out = p.communicate()[0]
    if p.returncode:
      sys.stderr.write(out)


def install_prerequisites(update):
  to_install = [
    ([(['errcheck', '-h'], 2)], ['github.com/kisielk/errcheck']),
    (
      [
        (['go', 'tool', 'cover', '-h'], 1),
        (['go', 'tool', 'vet', '-h'], 1),
        (['goimports', '-h'], 2),
      ],
      [
        'code.google.com/p/go.tools/cmd/cover',
        'code.google.com/p/go.tools/cmd/vet',
        'code.google.com/p/go.tools/cmd/goimports',
      ],
    ),
    ([(['gocov', '-h'], 2)], ['github.com/axw/gocov/gocov']),
    ([(['golint', '-h'], 2)], ['github.com/golang/lint/golint']),
    ([(['goveralls', '-h'], 2)], ['github.com/mattn/goveralls']),
  ]
  threads = []
  for cmds, urls in to_install:
    t = threading.Thread(
        name=urls[0], target=check_or_install, args=(cmds, urls, update))
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
  parser.add_option(
      '-u', '--update', action='store_true', help='Use go get -u')
  options, args = parser.parse_args()
  if args:
    parser.error('Unknown args: %s' % args)
  logging.basicConfig(
      level=logging.DEBUG if options.verbose else logging.ERROR,
      format='%(levelname)-5s: %(message)s')

  return install_prerequisites(options.update)


if __name__ == '__main__':
  sys.exit(main())
