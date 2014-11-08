#!/usr/bin/env python
# Copyright 2014 Marc-Antoine Ruel. All rights reserved.
# Use of this source code is governed under the Apache License, Version 2.0
# that can be found in the LICENSE file.

"""Runs complete presubmit checks on this package.

Some of these checks are actually not recommended to be run on automated checks
by their author so it is recommended to not be too strict about it.

Automatically integrates with coveralls.io when run on travis-ci.org.
"""

import glob
import logging
import optparse
import os
import shutil
import subprocess
import sys
import tempfile
import time


THIS_FILE = os.path.abspath(__file__)
THIS_DIR = os.path.dirname(THIS_FILE)


def call(cmd, reldir):
  logging.info('cwd=%-16s; %s', reldir, ' '.join(cmd))
  proc = subprocess.Popen(
      cmd, cwd=os.path.join(THIS_DIR, reldir),
      stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
  # Simplify our life by injecting cmd into Popen instance.
  proc.cmd = cmd
  return proc


def drain(proc):
  """Drains one subprocess.Popen created by call()."""
  if not proc:
    return 'Process failed'
  out = proc.communicate()[0]
  if proc.returncode:
    return out, proc.cmd
  return None, None


def go_dirs():
  """Returns the list of directories with .go files that are not tests."""
  out = []
  for r, d, f in os.walk(os.path.realpath('.')):
    for i in xrange(len(d) - 1, -1, -1):
      if d[i].startswith(('.', '_')):
        del d[i]
    if any(i.endswith('.go') and not i.endswith('_test.go') for i in f):
      out.append(r)
  return out


def get_test_dirs():
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
  for gopath in os.environ['GOPATH'].split(os.pathsep):
    root = os.path.realpath(os.path.join(gopath, 'src'))
    if os.path.isdir(root):
      return os.path.relpath(p, root)
  return os.path.realpath(p)


### Checks.


def build(tags):
  """Builds everything inside the current directory via 'go build ./...'."""
  extra = []
  for t in tags:
    extra.extend(('-tag', t))
  return subprocess.call(['go', 'build'] + extra + ['./...'])


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


def run_checks(root, tags, run_golint, run_govet):
  start = time.time()
  extra = []
  for t in tags or []:
    extra.extend(('--tag', t))
  procs = [
    call([sys.executable, THIS_FILE, '--build'] + extra, root),
    call([sys.executable, THIS_FILE, '--errcheck'], root),
    call([sys.executable, THIS_FILE, '--goimports'], root),
    call([sys.executable, THIS_FILE, '--gofmt'], root),
  ]

  # Add tests manually instead of using './...'. The reason is that it permits
  # running all the tests concurrently, which saves a lot of time when there's
  # many packages.
  test_dirs = get_test_dirs()
  for t in test_dirs:
    procs.append(call(['go', 'test', '-race', GOPATH_src_rel(t)], root))

  # There starts the cheezy part that may return false positives. I'm sorry
  # David.
  if run_golint:
    procs.append(call([sys.executable, THIS_FILE, '--golint'], root))
  if run_govet:
    procs.append(call([sys.executable, THIS_FILE, '--govet'], root))

  # Coverage is tricker. Only run it on travis.
  run_coverage = bool(os.environ.get('TRAVIS_JOB_ID'))
  tmpdir = None
  profile_path = None
  try:
    if run_coverage:
      tmpdir = tempfile.mkdtemp(prefix='presubmit_coverage')
      for i, t in enumerate(test_dirs):
        cmd = [
          'go', 'test', '-covermode=count', '-coverpkg', './...',
          '-coverprofile=' + os.path.join(tmpdir, 'test%d.cov' % i),
          GOPATH_src_rel(t),
        ]
        procs.append(call(cmd, root))

    # Collect the results of all the tests that ran concurrently.
    failed = False
    for p in procs:
      out, cmd = drain(p)
      if out:
        failed = True
        print('%s' % ' '.join(cmd))
        print('  ' + l for l in out.splitlines())

    if run_coverage:
      # Merge the profiles. Very hacky.
      profile_path = os.path.join(tmpdir, 'profile.cov')
      with open(profile_path, 'wb') as out:
        out.write('mode: count\n')
        for i in glob.glob(os.path.join(tmpdir, 'test*.cov')):
          with open(i, 'rb') as f:
            # Strip the first line.
            out.write(''.join(f.read().splitlines(True)[1:]))
  finally:
    if profile_path:
      # Make sure to have registered to https://coveralls.io first!
      if os.environ.get('TRAVIS_JOB_ID'):
        if subprocess.call(['goveralls', '-coverprofile=%s' % profile_path]):
          failed = True
      else:
        subprocess.call(['go', 'tool', 'cover', '-func', profile_path])
    if tmpdir:
      shutil.rmtree(tmpdir)

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

  return run_checks(os.path.dirname(THIS_DIR), [], run_golint, run_govet)


if __name__ == '__main__':
  sys.exit(main())
