#!/bin/bash
# Original source: https://gist.github.com/hailiang/0f22736320abe6be71ce
#
# The script does automatic checking on a Go package and its sub-packages, including:
# 1. gofmt         (http://golang.org/cmd/gofmt/)
# 2. goimports     (https://github.com/bradfitz/goimports)
# 3. golint        (https://github.com/golang/lint)
# 4. go vet        (http://golang.org/cmd/vet)
# 5. race detector (http://blog.golang.org/race-detector)
# 6. test coverage (http://blog.golang.org/cover)
#
# This script assumes the current working directory is the package to test.

set -e

# Run test coverage on each subdirectories and merge the coverage profile.
echo "mode: count" > profile.cov
# Standard go tooling behavior is to ignore dirs with leading underscores
for dir in $(find . -maxdepth 10 -not -path './.git*' -not -path '*/_*' -type d); do
  if ls $dir/*.go &> /dev/null; then
    go test -covermode=count -coverprofile=$dir/profile.tmp $dir
    if [ -f $dir/profile.tmp ]; then
      cat $dir/profile.tmp | tail -n +2 >> profile.cov
      rm $dir/profile.tmp
    fi
  fi
done
go tool cover -func profile.cov
# Make sure to have registered to https://coveralls.io first!
goveralls -coverprofile=profile.cov

# Runs tests a second time, this time in race detector mode.
go test -race ./...

# Formatting checks.
test -z "$(gofmt -l -s -w .  | tee /dev/stderr)"
test -z "$(goimports -l -w . | tee /dev/stderr)"

# TODO(maruel): These two may not be of interest generally:
test -z "$(golint .          | tee /dev/stderr)"
go vet ./...
