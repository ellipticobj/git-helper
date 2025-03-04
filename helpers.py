from sys import exit
from tqdm import tqdm
from loggers import error, info
from typing import List, Tuple, Optional
from argparse import ArgumentParser, _ArgumentGroup, Namespace

'''
helpers
'''

def completebar(pbar: tqdm, totalsteps: int) -> None:
    '''fills up pbar and makes it green'''
    pbar.n = totalsteps
    pbar.colour = 'green'
    pbar.refresh()

def validateargs(args: Namespace) -> None:
    '''validate argument combinations'''
    if not args.amend and not args.nomsg and not args.message:
        error("error: commit message required (use --amend, --no-message, or provide message)")
        exit(1)

def initcommands(parser: ArgumentParser) -> None:
    '''initialize commands with commands.'''
    # core functionality
    parser.add_argument("message", nargs='*', help="commit message (overrides --no-message)")
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
    advancedgrp.add_argument("--report", action='store_true', help="generate and output a report after everything is run") # TODO: add option to save to file, and to specify filename

def parseupstreamargs(
        args: Namespace, 
        pushcmd: List[str]
        ) -> List[str]:
    '''parses args for --set-upstream'''
    pushl = pushcmd
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
    return pushl

def _getcommitcommand(args: Namespace) -> List[str]:
    '''private function to get the git commit command'''
    commit: List[str] = ["git", "commit"]

    if args.message:
        message = " ".join(args.message) if isinstance(args.message, list) else args.message
        commit.extend(["-m", message])

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

def _getpullcommand(args: Namespace) -> List[str]:
    '''private function to get the git pull command'''
    pullargs: List[str] = ["git", "pull"]
    if args.norebase:
        pullargs.append("--no-rebase")
    return pullargs

def pushcommand(
        args: Namespace,
        progressbar: Optional[tqdm]
        ) -> Tuple[int, List[str]]:
    '''adds flags to the push command'''
    info("pushing to remote", progressbar)
    if not args.nopush:
        pushcmd: List[str] = ["git", "push"]
        if args.tags:
            pushcmd.append("--tags")
        if args.upstream:
            pushcmd = parseupstreamargs(args, pushcmd)
        if args.force:
            pushcmd.append("--force-with-lease")
        if args.quiet:
            pushcmd.append("--quiet")
        elif args.verbose:
            pushcmd.append("--verbose")
        return 1, pushcmd
    return 1, []

def statuscommand(
        args: Namespace, 
        progressbar: Optional[tqdm]
        ) -> Tuple[int, List[str]]:
    '''gets command for git status check'''
    # status check
    if args.status:
        info(f"{args.__class__.__name__} status check", progressbar)
        cmd: List[str] = ["git", "status"]
        if progressbar: 
            progressbar.update(1)
        return 1, cmd
    return 0, []

def submodulesupdatecommand(
        args: Namespace, 
        progressbar: Optional[tqdm]
        ) -> Tuple[int, List[str]]:
    '''gets command for submodule update'''
    if args.updatesubmodules:
        info("\nupdating submodules", progressbar)
        cmd: List[str] = ["git", "submodule", "update", "--init", "--recursive"]
        if progressbar:
            progressbar.update(1)
        return 1, cmd
    return 0, []

def stashcommand(
        args: Namespace, 
        progressbar: Optional[tqdm]
        ) -> Tuple[int, List[str]]:
    '''gets command for git stash'''
    if args.stash:
        info("\nstashing changes", progressbar)
        cmd: List[str] = ["git", "stash"]
        if progressbar:
            progressbar.update(1)
        return 1, cmd
    return 0, []

def pullcommand(
        args: Namespace, 
        progressbar: Optional[tqdm]
        ) -> Tuple[int, List[str]]:
    '''gets command for git pull'''
    if args.pull or args.norebase:
        info("\npulling from remote", progressbar)
        args.mainpbar = progressbar  # attach progress bar to args (if needed)
        if progressbar:
            progressbar.update(1)
        return 1, _getpullcommand(args)
    return 0, []

def stagecommand(
        args: Namespace, 
        progressbar: Optional[tqdm]
        ) -> Tuple[int, List[str]]:
    '''gets command for git add'''
    info("\nstaging changes", progressbar)
    cmd: List[str] = ["git", "add", *args.add] if args.add else ["git", "add", "."]
    if args.verbose and not args.quiet:
        cmd.append("--verbose")
    if progressbar:
        progressbar.update(1)
    return 1, cmd

def diffcommand(
        args: Namespace, 
        progressbar: Optional[tqdm]
        ) -> Tuple[int, List[str]]:
    '''gets command for git diff'''
    if args.diff:
        info("\nshowing diff", progressbar)
        cmd: List[str] = ["git", "diff", "--staged"]
        return 1, cmd
    return 0, []

def commitcommand(
        args: Namespace, 
        progressbar: Optional[tqdm]
        ) -> Tuple[int, List[str]]:
    '''gets command for git commit'''
    info("\ncommitting", progressbar)
    cmd: List[str] = _getcommitcommand(args)
    if progressbar:
        progressbar.update(1)
    return 1, cmd

def pulldiffcommand(
        args: Namespace,
        progressbar: Optional[tqdm]
        ) -> Tuple[int, List[str]]:
    '''Get command to show diff after pull'''
    info("changes: ", progressbar)
    return 1, ["git", "diff", "--numstat", "HEAD@{1}", "HEAD"]

def getgitcommands(
        gitcommand: str, 
        commandarguments: List[str]
        ) -> Tuple[List[str], List[str]]:
    if gitcommand == "add":
        precmd = []
        cmd = ["git", "add"] + (commandarguments or ["."])
    elif gitcommand == "commit":
        precmd = ["git", "add", "."]
        cmd = ["git", "commit"] + (["-m"] + commandarguments if commandarguments else [])
    # elif gitcommand == "push": # TODO: finish this
    #     pass
    # elif gitcommand == "pull":
    #     pass
    # elif gitcommand == "clone":
    #     pass
    else:
        precmd = []
        cmd = ["git", gitcommand] + commandarguments
    
    return precmd, cmd