import os
import sys
import subprocess
from argparse import ArgumentParser
from typing import List

VERSION = "0.1.6"

def runcmd(args: List[str], cont: bool, dry: bool = False) -> None:
    cwd = os.getcwd()
    if dry:
        print(subprocess.list2cmdline(args))
        return None

    try:
        print(f"running command: {subprocess.list2cmdline(args)} from {cwd} ...")
        subprocess.run(args, check=True, cwd=cwd)
        print(" done")
    except subprocess.CalledProcessError as e:
        print(
            f"error: command '{subprocess.list2cmdline(args)}' failed with exit code {e.returncode}."
        )
        if not cont:
            sys.exit(e.returncode)

def initparser(parser: ArgumentParser) -> None:
    '''initializes parser commands'''
    parser.add_argument("message", nargs='?', help="commit message, overrides --no-message")
    parser.add_argument("-v", "--version", required=False, dest="ver", action='store_true', help="displays version number")
    parser.add_argument("-n", "--allow-empty-message", "--no-message", dest="nomsg", required=False, action='store_true', help="allows empty commit message, has to be provided if no message is given")
    parser.add_argument("-u", "--set-upstream", "--upstream", nargs=2, dest="upstream", required=False, help="upstream branch to push to. takes two arguments: remote, branch")
    parser.add_argument("-d", "--dry-run", "--dry", dest="dry", required=False, action="store_true", help="prints out the commands that will be run without actually running them")
    parser.add_argument("-c", "--continue", required=False, dest="cont", action='store_true', help="continues even if there are errors")
    parser.add_argument("-f", "--force", required=False, action='store_true', help="force push")
    parser.add_argument("-q", "--quiet", required=False, action='store_true', help="quiet")
    parser.add_argument("-a", "--add", required=False, dest="addfiles", nargs="+", help="select specific files to stage")
    parser.add_argument("-ve", "--verbose", required=False, action='store_true', help="verbose")
    parser.add_argument("--allow-empty", dest="empty", required=False, action='store_true', help="allows empty commit")
    parser.add_argument("-np", "--no-push", action='store_true', required=False, dest="nopush", help="does not push")
    parser.add_argument("--tags", action='store_true', help="push tags with commits")
    parser.add_argument("--diff", action='store_true', help="show diff before committing")
    parser.add_argument("--pull", action="store_true", help="runs git pull before pushing before pushing")
    parser.add_argument("--pull-no-rebase", dest="norebase", action="store_true", help="runs git pull --no-rebase before pushing, overrides --pull")
    parser.add_argument("--update-submodules", action="store_true", help="update submodules recursively")
    parser.add_argument("--stash", action='store_true', help="Stash changes before pull")
    parser.add_argument("--status", action='store_true', dest='status', help='runs git status before running commands')
    # parser.add_argument("--config", help="Use custom config file") TODO

def main() -> None:
    parser: ArgumentParser = ArgumentParser(
        prog="meow",
        description="automatically stages, commits and pushes, with options",
    )
    initparser(parser)

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    if len(sys.argv) >= 2:
        if sys.argv[1].strip() == "meow": # :3
            print("meoww :3")
            sys.exit(1)

    args = parser.parse_args()

    if args.ver:
        print(f"meow version {VERSION}\nhttps://github.com/ellipticobj/meower")
        sys.exit(1)

    # validation
    if not args.nomsg and not args.message:
        parser.error("commit message required (use --no-message, or provide message)")
        sys.exit(1)

    verbose = args.verbose and not args.quiet

    if args.status: # status
        runcmd(['git', 'status'], args.cont, args.dry)

    if args.update_submodules: # submodule update
        runcmd(["git", "submodule", "update", "--init", "--recursive"], cont=args.cont, dry=args.dry)

    if args.stash: # stash before pull
        runcmd(["git", "stash"], args.cont, args.dry)

    # pull command
    gpullc: List[str] = ["git", "pull"]
    if args.norebase:
        gpullc.append("--no-rebase")
    if args.pull:
        runcmd(gpullc, cont=args.cont, dry=args.dry)
    
    if args.stash:
        runcmd(["git", "stash", "pop"], cont=args.cont, dry=args.dry)

    # add command
    gac: List[str] = ["git", "add", "."]

    if args.addfiles:  # selective staging
        gac = ["git", "add"] + args.add_files
    
    if verbose:
        gac.append("--verbose")

    runcmd(gac, cont=args.cont, dry=args.dry)

    # diff
    if args.diff:
        runcmd(["git", "diff", "--staged"], args.cont, args.dry)

    # commit command
    gcc: List[str] = ["git", "commit"]

    if args.message:
        msg = args.message
        gcc += ["-m", msg]

    if args.nomsg:
        gcc.append("--allow-empty-message")

    if args.empty:
        gcc.append("--allow-empty")

    if args.quiet:
        gcc.append("--quiet")
    elif verbose:
        gcc.append("--verbose")
    
    runcmd(gcc, cont=args.cont, dry=args.dry)

    # push command
    if not args.nopush:
        gpc = ["git", "push"]
        if args.tags:  # tag pushing
            gpc.append("--tags")
        if args.upstream:
            try:
                remote, branch = args.upstream.split("/", 1)
                gpc += ["--set-upstream", remote, branch]
            except ValueError:
                parser.error("upstream must be in format remote branch")
        if args.force:
            gpc.append("--force")
        if args.quiet:
            gpc.append("--quiet")
        elif verbose:
            gpc.append("--verbose")
        
        runcmd(gpc, cont=args.cont, dry=args.dry)
    elif not args.dry:
        print("skipping push...")

    # end
    if not args.dry:
        print("done")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("user interrputed")
