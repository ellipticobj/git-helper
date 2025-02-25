# git helper
im tired of doing git add . git commit -m "" git push all the time and im too lazy to make a macro  
this is made for myself and not you

## usage:
```
usage: meower [-h] [-n] [-u UPSTREAM] [-d] [-f] [-q] [-v] [--allow-empty] [--pull] [--pull-no-rebase] [--update-submodules] [message]

helps to stages all changes, commits, and pushes, with args

positional arguments:
  message               commit message, overrides --no-message

options:
  -h, --help            show this help message and exit
  -n, --allow-empty-message, --no-message
                        allows empty commit message, has to be provided if no message is given
  -u, --upstream UPSTREAM
                        upstream branch to push to
  -d, --dry-run, --dry  prints out the commands that will be run without actually running them
  -f, --force           force push
  -q, --quiet           quiet
  -v, --verbose         verbose
  --allow-empty         allows empty commit
  --pull                runs git pull before pushing before pushing
  --pull-no-rebase      runs git pull --no-rebase before pushing, overrides --pull
  --update-submodules   update submodules recursively
```
