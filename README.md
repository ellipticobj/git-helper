# meow
im tired of doing git add . git commit -m "" git push all the time and im too lazy to make a macro  
this is made for myself and not you

development takes place on the dev branch, main is for prod

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
