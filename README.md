Generic git pre-commit hook for Golang projects
-----------------------------------------------

`presubmit_impl.py` runs multiple tests on a go project to ensure code health.
It is designed to be called on commit. It:

  * Build all directories with .go files found
  * Run all test founds


Hook Installation
=================

To install the git pre-commit hook which runs `presubmit.py` automatically on
commit, run:

    ./install.py


Initial project setup
=====================

The normal workflow to setup git-hooks-go for a golang repository is:

    git submodule init
    git submodule add https://github.com/maruel/git-hooks-go
    ln -s git-hooks-go/presubmit.py
