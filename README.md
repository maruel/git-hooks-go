Generic git pre-commit hook for Golang projects
===============================================

`presubmit_impl.py` runs multiple tests on a go project to ensure code health.
It is designed to be called on commit. It:

  * [Build](https://golang.org/pkg/go/build/) all directories with .go files found
  * Run [all test found](https://golang.org/pkg/testing/)
  * Run [errcheck](https://github.com/kisielk/errcheck)
  * Run [gofmt](https://golang.org/cmd/gofmt/) and [goimports](https://godoc.org/code.google.com/p/go.tools/cmd/goimports) (redundant except for gofmt -s)
  * (optionally) Run [govet](https://godoc.org/code.google.com/p/go.tools/cmd/vet)
  * (optionally) Run [golint](https://github.com/golang/lint)


Hook Installation
-----------------

To install the git pre-commit hook which runs `presubmit.py` automatically on
commit, run:

    ./install.py


Initial project setup
---------------------

The normal workflow to setup git-hooks-go for a golang repository is:

    git submodule init
    git submodule add https://github.com/maruel/git-hooks-go
    ln -s git-hooks-go/presubmit.py
    git commit -a -m "Add git-hooks-go pre-commit git hook."
