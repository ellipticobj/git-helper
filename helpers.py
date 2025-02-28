from sys import exit
from tqdm import tqdm
from time import sleep
from loggers import error
from colorama import Fore, Style
from typing import List, Optional
from argparse import ArgumentParser, _ArgumentGroup, Namespace

def completebar(pbar: tqdm, totalsteps: int) -> None:
    '''fills up pbar and makes it green'''
    pbar.n = totalsteps
    pbar.colour = 'green'
    pbar.refresh()

def progressbar(total: int, description: str, position: int, leave: bool, duration: float = 0.5) -> None:
    '''default progress bar'''
    with tqdm(total=total, desc=f"{Fore.CYAN}{description}{Style.RESET_ALL}", bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt}', position=position, leave=leave) as pbar:
        for _ in range(100):
            sleep(duration / total)
            pbar.update(1)

def validateargs(args: Namespace) -> None:
    '''validate argument combinations'''
    if not args.amend and not args.nomsg and not args.message:
        error("error: commit message required (use --amend, --no-message, or provide message)")
        exit(1)

def initcommands(parser: ArgumentParser) -> None:
    '''initialize commands with commands.'''
    # core functionality
    parser.add_argument("message", nargs='?', help="commit message (overrides --no-message)")
    parser.add_argument("-a", "--add", dest="add", nargs="+", help="select specific files to stage")

    # general options
    generalgrp: _ArgumentGroup = parser.add_argument_group("general options")
    generalgrp.add_argument("-v", "--version", action='store_true', help="show version")
    generalgrp.add_argument("-c", "--continue", dest="cont", action='store_true', help="continue after errors")
    generalgrp.add_argument("-q", "--quiet", action='store_true', help="suppress output")
    generalgrp.add_argument("-ve", "--verbose", action='store_true', help="verbose output")
    generalgrp.add_argument("--dry", dest = "dry", action='store_true', help="preview commands without execution")
    generalgrp.add_argument("--status", action='store_true', help="show git status before executing commands")

    # commit options
    commitgrp: _ArgumentGroup = parser.add_argument_group("commit options")
    commitgrp.add_argument("-n", "--no-message", dest="nomsg", action='store_true', help="allow empty commit message")
    commitgrp.add_argument("--allow-empty", dest="allowempty", action='store_true', help="allow empty commit")
    commitgrp.add_argument("--diff", action='store_true', help="show diff before committing")
    commitgrp.add_argument("--amend", action='store_true', help="amend previous commit")

    # push options
    pushgrp: _ArgumentGroup = parser.add_argument_group("push options")
    pushgrp.add_argument("-u", "--upstream", "--set-upstream", nargs='+', metavar="REMOTE/BRANCH", help="set upstream branch to push to (formats: REMOTE BRANCH or REMOTE/BRANCH)")
    pushgrp.add_argument("-f", "--force", action='store_true', help="force push")
    pushgrp.add_argument("-np", "--no-push", dest="nopush", action='store_true', help="skip pushing")
    pushgrp.add_argument("--tags", action='store_true', help="push tags with commits")

    # pull options
    pullgrp: _ArgumentGroup = parser.add_argument_group("pull options")
    pullgrp.add_argument("--pull", action='store_true', help="run git pull before pushing")
    pullgrp.add_argument("--pull-no-rebase", dest="norebase", action='store_true', help="run git pull --no-rebase (overrides --pull)")

    # advanced options
    advancedgrp: _ArgumentGroup = parser.add_argument_group("advanced options")
    advancedgrp.add_argument("--update-submodules", dest="updatesubmodules", action='store_true', help="update submodules recursively")
    advancedgrp.add_argument("--stash", action='store_true', help="stash changes before pull")

def commithelper(args: Namespace) -> List[str]:
    '''adds flags to the commit command'''
    commit: List[str] = ["git", "commit"]

    if args.message:
        commit.extend(["-m", args.message])
    elif args.nomsg:
        commit.append("--allow-empty-message")

    if args.amend:
        commit.append("--amend")

    if args.allowempty:
        commit.append("--allow-empty")

    if args.quiet:
        commit.append("--quiet")
    elif args.verbose:
        commit.append("--verbose")

    return commit

def pushhelper(args: Namespace) -> Optional[List[str]]:
    '''adds flags to the push command'''
    if not args.nopush:
        push: List[str] = ["git", "push"]
        if args.tags:
            push.append("--tags")

        if args.upstream:
            parseupstreamargs(args, push)

        if args.force:
            push.append("--force")

        if args.quiet:
            push.append("--quiet")
        elif args.verbose:
            push.append("--verbose")

        return push
    return None

def parseupstreamargs(args: Namespace, pushl: List[str]):
    '''parses args for --set-upstream'''
    if len(args.upstream) == 1 and '/' in args.upstream[0]:
        # use REMOTE/BRANCH format
        remote: str
        branch: str
        remote, branch = args.upstream[0].split('/')
        pushl.extend(["--set-upstream", remote, branch])
    elif len(args.upstream) == 2:
        # use REMOTE BRANCH format
        pushl.extend(["--set-upstream", args.upstream[0], args.upstream[1]])
    else:
        error("invalid upstream format. Use 'REMOTE BRANCH' or 'REMOTE/BRANCH'")
        exit(1)
