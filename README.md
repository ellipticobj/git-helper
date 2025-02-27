# meow
A git workflow automation tool with color output, progress bars, and improved UI.

This tool simplifies the common git workflow (add, commit, push) with a single command.
- Color coded output to easily identify success/errors
- Progress tracking for commands
- Visual feedback for operations

development takes place on the dev branch, main is for prod

## Installation

```
# Install dependencies
pip install -r requirements.txt

# Install the tool
./install.sh
```

## usage:
```
usage: meow [-h] [-v] [-n] [-u UPSTREAM] [-d] [-f] [-q] [-ve] [--allow-empty] [-np] [--pull] [--pull-no-rebase] [--update-submodules] [message]

automatically stages, commits and pushes, with options

positional arguments:
  message               commit message, overrides --no-message

options:
  -h, --help            show this help message and exit
  -v, --version         displays version number
  -n, --allow-empty-message, --no-message
                        allows empty commit message, has to be provided if no message is given
  -u, --set-upstream, --upstream UPSTREAM
                        upstream branch to push to
  -d, --dry-run, --dry  prints out the commands that will be run without actually running them
  -f, --force           force push
  -q, --quiet           quiet
  -ve, --verbose        verbose
  --allow-empty         allows empty commit
  -np, --no-push        does not push
  --pull                runs git pull before pushing before pushing
  --pull-no-rebase      runs git pull --no-rebase before pushing, overrides --pull
  --update-submodules   update submodules recursively
```
