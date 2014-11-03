#!/usr/bin/env python
# Copyright 2014 Marc-Antoine Ruel. All rights reserved.
# Use of this source code is governed under the Apache License, Version 2.0
# that can be found in the LICENSE file.

"""Runs complete presubmit checks on this package.

Some of these checks are actually not recommended to be run on automated checks
by their author so it is recommended to not be too strict about it.
"""

import logging
import optparse
import os
import subprocess
import sys
import time


THIS_FILE = os.path.abspath(__file__)
THIS_DIR = os.path.dirname(THIS_FILE)


def call(cmd, reldir):
  logging.info('cwd=%-16s; %s', reldir, ' '.join(cmd))
  return subprocess.Popen(
      cmd, cwd=os.path.join(THIS_DIR, reldir),
      stdout=subprocess.PIPE, stderr=subprocess.STDOUT)


def drain(proc):
  """Drains one subprocess.Popen created by call()."""
  if not proc:
    return 'Process failed'
  out = proc.communicate()[0]
  if proc.returncode:
    return out


def check_or_install(tool, *urls):
  """Tries to run a command to see if the command exists.

  If not, automatically install it.
  """
  try:
    return call(tool, THIS_DIR)
  except OSError:
    for url in urls:
      print('Warning: installing %s' % url)
      subprocess.check_call(['go', 'get', '-u', url])
    return call(tool, THIS_DIR)


def go_dirs():
  """Returns the list of directories with .go files that are not tests."""
  out = []
  for r, d, f in os.walk(os.path.realpath('.')):
    for i in xrange(len(d) - 1, -1, -1):
      if d[i].startswith('.'):
        del d[i]
    if any(i.endswith('.go') and not i.endswith('_test.go') for i in f):
      out.append(r)
  return out


def test_dirs():
  """Returns the list of directories with go test (*_test.go) files."""
  out = []
  for r, d, f in os.walk(os.path.realpath('.')):
    for i in xrange(len(d) - 1, -1, -1):
      if d[i].startswith('.'):
        del d[i]
    if any(i.endswith('_test.go') for i in f):
      out.append(r)
  return out


def GOPATH_src_rel(p):
  """Returns the path relative to $GOPATH/src."""
  root = os.path.realpath(os.path.join(os.environ['GOPATH'], 'src'))
  return os.path.relpath(p, root)


### Checks.


def build(tags):
  """Runs go build on all directories containing .go files."""
  extra = []
  for t in tags:
    extra.extend(('-tag', t))
  cmd = ['go', 'build'] + extra + [GOPATH_src_rel(d) for d in go_dirs()]
  return subprocess.call(cmd)


def errcheck():
  """Runs errcheck on all directories containing .go files."""
  # TODO(maruel): I don't know what happened around Oct 2014 but errcheck
  # became super slow.
  cmd = ['errcheck'] + [GOPATH_src_rel(d) for d in go_dirs()]
  return subprocess.call(cmd)


def gofmt():
  """Runs gofmt in check mode."""
  # TODO(maruel): Likely always redundant with goimports.
  # gofmt doesn't return non-zero even if some files need to be updated.
  out = subprocess.check_output(['gofmt', '-l', '-s', '.'])
  if out:
    print('These files are improperly formmatted. Please run: gofmt -w -s .')
    sys.stdout.write(out)
    return 1
  return 0


def goimports():
  """Runs goimports in check mode."""
  # goimports doesn't return non-zero even if some files need to be updated.
  out = subprocess.check_output(['goimports', '-l', '.'])
  if out:
    print('These files are improperly formmatted. Please run: goimports -w .')
    sys.stdout.write(out)
    return 1
  return 0


def golint():
  """Runs golint."""
  # golint doesn't return non-zero ever.
  out = subprocess.check_output(['golint'] + [d for d in go_dirs()])
  if out:
    print('These files are not golint free.')
    sys.stdout.write(out)
    return 1
  return 0


def govet():
  """Runs go tool vet."""
  # govet is very noisy about "composite literal uses unkeyed fields" which
  # cannot be turned off so strip these and ignore the return code.
  proc = subprocess.Popen(
      ['go', 'tool', 'vet', '-all', '.'],
      stdout=subprocess.PIPE)
  out = '\n'.join(
      l for l in proc.communicate()[0].splitlines()
      if not l.endswith(' composite literal uses unkeyed fields'))
  if out:
    print(out)
    return 1
  return 0


def test():
  """Runs go test on all directories containing go test files."""
  cmd = ['go', 'test', '-cover'] + [GOPATH_src_rel(d) for d in test_dirs()]
  return subprocess.call(cmd)


def run_checks(root, tags, run_golint, run_govet):
  start = time.time()
  procs = [
    check_or_install(['errcheck'], 'github.com/kisielk/errcheck'),
    check_or_install(
        ['goimports', '.'],
        'code.google.com/p/go.tools/cmd/cover',
        'code.google.com/p/go.tools/cmd/goimports',
        'code.google.com/p/go.tools/cmd/vet'),
    check_or_install(['golint'], 'github.com/golang/lint/golint'),
  ]
  while procs:
    drain(procs.pop(0))
  logging.info('Prerequisites check completed.')

  extra = []
  for t in tags or []:
    extra.extend(('--tag', t))
  procs = [
    call([sys.executable, THIS_FILE, '--build'] + extra, root),
    call([sys.executable, THIS_FILE, '--test'], root),
    call([sys.executable, THIS_FILE, '--errcheck'], root),
    call([sys.executable, THIS_FILE, '--goimports'], root),
    call([sys.executable, THIS_FILE, '--gofmt'], root),
  ]
  # There starts the cheezy part that may return false positives. I'm sorry
  # David.
  if run_golint:
    procs.append(call([sys.executable, THIS_FILE, '--golint'], root))
  if run_govet:
    procs.append(call([sys.executable, THIS_FILE, '--govet'], root))

  failed = False
  for p in procs:
    out = drain(p)
    if out:
      failed = True
      print out

  end = time.time()
  if failed:
    print('Presubmit checks failed in %1.3fs!' % (end-start))
    return 1
  print('Presubmit checks succeeded in %1.3fs!' % (end-start))
  return 0


def main(run_golint=True, run_govet=True):
  parser = optparse.OptionParser(description=sys.modules[__name__].__doc__)
  parser.add_option(
      '-v', '--verbose', action='store_true', help='Logs what is being run')
  parser.add_option(
      '--build', action='store_true', help=optparse.SUPPRESS_HELP)
  parser.add_option(
      '--errcheck', action='store_true', help=optparse.SUPPRESS_HELP)
  parser.add_option(
      '--gofmt', action='store_true', help=optparse.SUPPRESS_HELP)
  parser.add_option(
      '--goimports', action='store_true', help=optparse.SUPPRESS_HELP)
  parser.add_option(
      '--golint', action='store_true', help=optparse.SUPPRESS_HELP)
  parser.add_option(
      '--govet', action='store_true', help=optparse.SUPPRESS_HELP)
  parser.add_option(
      '--tag', action='append', default=[], help=optparse.SUPPRESS_HELP)
  parser.add_option(
      '--test', action='store_true', help=optparse.SUPPRESS_HELP)
  options, args = parser.parse_args()
  if args:
    parser.error('Unknown args: %s' % args)
  logging.basicConfig(
      level=logging.DEBUG if options.verbose else logging.ERROR,
      format='%(levelname)-5s: %(message)s')
  if options.build:
    return build(options.tag)
  if options.errcheck:
    return errcheck()
  if options.gofmt:
    return gofmt()
  if options.goimports:
    return goimports()
  if options.golint:
    return golint()
  if options.govet:
    return govet()
  if options.test:
    return test()

  return run_checks(os.path.dirname(THIS_DIR), [], run_golint, run_govet)


if __name__ == '__main__':
  sys.exit(main())
