standard git hook
-----------------

This is a set of pre-commit hooks to ensure code health on commit. It:

  * Build all directories with .go files found
  * Run all test founds

To install the git pre-commit hook which runs `presubmit.py` automatically on
commit, run:

    ./install.py

It is recommended to add this repository as a git-submodule to your golang
project.
