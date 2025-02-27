import os
import sys
import subprocess
from argparse import ArgumentParser
from typing import List

VERSION = "0.2.0"

def runcmd(args: List[str], cont: bool, dry: bool = False) -> None:
    """executes a the command, with error handling."""
    cwd = os.getcwd()
    if dry:
        print(subprocess.list2cmdline(args))
        return None

    try:
        print(f"    running command: {subprocess.list2cmdline(args)} from directory {cwd}...")
        subprocess.run(args, check=True, cwd=cwd)
        print("    done")
    except subprocess.CalledProcessError as e:
        print(f"\nerror: command '{subprocess.list2cmdline(args)}' failed with exit code {e.returncode}.")
        if not cont:
            sys.exit(e.returncode)

def initcommands(parser: ArgumentParser) -> None:
    """initialize commands with commands."""
    # core functionality
    parser.add_argument("message", nargs='?', help="commit message (overrides --no-message)")
    parser.add_argument("-a", "--add", dest="add_files", nargs="+", help="select specific files to stage")

    # commit options
    commit_group = parser.add_argument_group("commit options")
    commit_group.add_argument("--amend", action='store_true', help="amend previous commit")
    commit_group.add_argument("-n", "--no-message", dest="nomsg", action='store_true', help="allow empty commit message")
    commit_group.add_argument("--allow-empty", action='store_true', help="allow empty commit")
    commit_group.add_argument("--diff", action='store_true', help="show diff before committing")

    # push options
    push_group = parser.add_argument_group("push options")
    push_group.add_argument("-u", "--upstream", "--set-upstream", nargs='+', metavar="REMOTE/BRANCH", help="set upstream branch to push to (formats: REMOTE BRANCH or REMOTE/BRANCH)")
    push_group.add_argument("-f", "--force", action='store_true', help="force push")
    push_group.add_argument("--tags", action='store_true', help="push tags with commits")
    push_group.add_argument("-np", "--no-push", action='store_true', help="skip pushing")

    # pull options
    pull_group = parser.add_argument_group("pull options")
    pull_group.add_argument("--pull", action='store_true', help="run git pull before pushing")
    pull_group.add_argument("--pull-no-rebase", dest="no_rebase", action='store_true', help="run git pull --no-rebase (overrides --pull)")

    # general options
    general_group = parser.add_argument_group("general options")
    general_group.add_argument("-v", "--version", action='store_true', help="show version")
    general_group.add_argument("-d", "--dry-run", action='store_true', help="preview commands without execution")
    general_group.add_argument("-c", "--continue", dest="cont", action='store_true', help="continue after errors")
    general_group.add_argument("-q", "--quiet", action='store_true', help="suppress output")
    general_group.add_argument("-ve", "--verbose", action='store_true', help="verbose output")
    general_group.add_argument("--status", action='store_true', help="show git status before executing commands")

    # advanced options
    advanced_group = parser.add_argument_group("advanced options")
    advanced_group.add_argument("--update-submodules", action='store_true', help="update submodules recursively")
    advanced_group.add_argument("--stash", action='store_true', help="stash changes before pull")

def validateargs(args) -> None:
    """validate argument combinations"""
    if not args.amend and not args.nomsg and not args.message:
        raise ValueError("commit message required (use --amend, --no-message, or provide message)")

def printinfo() -> None:
    print(f"meow version {VERSION}\nhttps://github.com/ellipticobj/meower")
    sys.exit(1)

def pullhandler(args) -> None:
    """handles git pull operations"""
    pull = ["git", "pull"]
    if args.no_rebase:
        pull.append("--no-rebase")
    if args.pull:
        runcmd(pull, args.cont, args.dry_run)

def main() -> None:
    parser = ArgumentParser(prog="meow", description="Automate Git workflows with style")
    initcommands(parser)

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
    
    if len(sys.argv) > 1:
        if sys.argv[1].lower().strip() == "meow":
            print("meow meow :3")
        else:
            parser.print_help()
        sys.exit(1)

    args = parser.parse_args()

    if args.version:
        print(f"meow version {VERSION}\nhttps://github.com/ellipticobj/meower")
        sys.exit()

    try:
        validateargs(args)
    except ValueError as e:
        parser.error(str(e))

    # pipeline
    if args.status:
        runcmd(["git", "status"], args.cont, args.dry_run)

    if args.update_submodules:
        runcmd(["git", "submodule", "update", "--init", "--recursive"], args.cont, args.dry_run)

    if args.stash:
        runcmd(["git", "stash"], args.cont, args.dry_run)

    pullhandler(args)

    # stage
    add_cmd = ["git", "add", *args.add_files] if args.add_files else ["git", "add", "."]
    if args.verbose and not args.quiet:
        add_cmd.append("--verbose")
    runcmd(add_cmd, args.cont, args.dry_run)

    # diff
    if args.diff:
        runcmd(["git", "diff", "--staged"], args.cont, args.dry_run)

    # commit
    commit = ["git", "commit"]

    if args.message:
        commit.extend(["-m", args.message])
    elif args.nomsg:
        commit.append("--allow-empty-message")
    
    if args.amend:
        commit.append("--amend")

    if args.allow_empty:
        commit.append("--allow-empty")
    
    if args.quiet:
        commit.append("--quiet")
    elif args.verbose:
        commit.append("--verbose")
    runcmd(commit, args.cont, args.dry_run)

    # push
    if not args.no_push:
        push_cmd = ["git", "push"]
        if args.tags:
            push_cmd.append("--tags")

        if args.upstream:
            push_cmd.extend(["--set-upstream", args.upstream[0], args.upstream[1]])

        if args.force:
            push_cmd.append("--force")

        if args.quiet:
            push_cmd.append("--quiet")
        elif args.verbose:
            push_cmd.append("--verbose")
        
        runcmd(push_cmd, args.cont, args.dry_run)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("execution stopped")