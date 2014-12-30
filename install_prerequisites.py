#!/usr/bin/env python
# Copyright 2014 Marc-Antoine Ruel. All rights reserved.
# Use of this source code is governed under the Apache License, Version 2.0
# that can be found in the LICENSE file.

"""Installs all packages needed at runtime by presubmit.py."""

import logging
import optparse
import subprocess
import sys


def install_prerequisites(update):
  to_install = [
    (['errcheck', '-h'], 2, 'github.com/kisielk/errcheck'),
    (['go', 'tool', 'cover', '-h'], 1, 'golang.org/x/tools/cmd/cover'),
    (['go', 'tool', 'vet', '-h'], 1, 'golang.org/x/tools/cmd/vet'),
    (['gocov', '-h'], 2, 'github.com/axw/gocov/gocov'),
    (['goimports', '-h'], 2, 'golang.org/x/tools/cmd/goimports'),
    (['golint', '-h'], 2, 'github.com/golang/lint/golint'),
    (['goveralls', '-h'], 2, 'github.com/mattn/goveralls'),
  ]
  urls = []
  for cmd, exitcode, url in to_install:
    try:
      logging.info('%s', ' '.join(cmd))
      p = subprocess.Popen(
          cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
      p.communicate()
      if p.returncode == exitcode:
        continue
    except OSError:
      pass
    urls.append(url)

  out = 0
  if urls:
    urls.sort()
    print('Installing:')
    print('\n'.join('  ' + url for url in urls))
    cmd = ['go', 'get']
    if update:
      cmd.append('-u')
    cmd.extend(urls)
    out = subprocess.call(cmd)
  if not out:
    print('Prerequisites check completed.')
  else:
    print('Prerequisites installation failed.')
  return out


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
