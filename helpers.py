from sys import exit
from time import time
from os import getcwd
from tqdm import tqdm
from colorama import Style, Fore
from contextlib import contextmanager
from typing import List, Tuple, Optional, Dict
from argparse import ArgumentParser, _ArgumentGroup, Namespace
from loggers import error, info, success, printcmd, printoutput
from loaders import startloadinganimation, stoploadinganimation
from subprocess import list2cmdline, run as runsubprocess, CompletedProcess, CalledProcessError

'''
helpers
'''

MinimalNamespace = Namespace(
    cont=False, 
    dry=False, 
    verbose=True, 
    quiet=False, 
    mainpbar=None
)

GITCOMMANDMESSAGES: Dict[str, str] = {
    'log': 'q to exit: ',
    'add': 'staging...',
    'push': 'pushing...',
    'pull': 'pulling...',
    'clone': 'cloning...',
    'fetch': 'fetching...',
    'branch': 'branching...',
    'commit': 'committing...',
    'diff': 'showing diffs...',
    'status': 'checking repo status...'
}

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
        pbar: Optional[tqdm]
        ) -> Tuple[int, List[str]]:
    '''adds flags to the push command'''
    info("pushing to remote", pbar)
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
        pbar: Optional[tqdm]
        ) -> Tuple[int, List[str]]:
    '''gets command for git status check'''
    # status check
    if args.status:
        info(f"{args.__class__.__name__} status check", pbar)
        cmd: List[str] = ["git", "status"]
        if pbar: 
            pbar.update(1)
        return 1, cmd
    return 0, []

def submodulesupdatecommand(
        args: Namespace, 
        pbar: Optional[tqdm]
        ) -> Tuple[int, List[str]]:
    '''gets command for submodule update'''
    if args.updatesubmodules:
        info("\nupdating submodules", pbar)
        cmd: List[str] = ["git", "submodule", "update", "--init", "--recursive"]
        if pbar:
            pbar.update(1)
        return 1, cmd
    return 0, []

def stashcommand(
        args: Namespace, 
        pbar: Optional[tqdm]
        ) -> Tuple[int, List[str]]:
    '''gets command for git stash'''
    if args.stash:
        info("\nstashing changes", pbar)
        cmd: List[str] = ["git", "stash"]
        if pbar:
            pbar.update(1)
        return 1, cmd
    return 0, []

def pullcommand(
        args: Namespace, 
        pbar: Optional[tqdm]
        ) -> Tuple[int, List[str]]:
    '''gets command for git pull'''
    if args.pull or args.norebase:
        info("\npulling from remote", pbar)
        args.mainpbar = pbar  # attach progress bar to args (if needed)
        if pbar:
            pbar.update(1)
        return 1, _getpullcommand(args)
    return 0, []

def stagecommand(
        args: Namespace, 
        pbar: Optional[tqdm]
        ) -> Tuple[int, List[str]]:
    '''gets command for git add'''
    info("\nstaging changes", pbar)
    cmd: List[str] = ["git", "add", *args.add] if args.add else ["git", "add", "."]
    if args.verbose and not args.quiet:
        cmd.append("--verbose")
    if pbar:
        pbar.update(1)
    return 1, cmd

def diffcommand(
        args: Namespace, 
        pbar: Optional[tqdm]
        ) -> Tuple[int, List[str]]:
    '''gets command for git diff'''
    if args.diff:
        info("\nshowing diff", pbar)
        cmd: List[str] = ["git", "diff", "--staged"]
        return 1, cmd
    return 0, []

def commitcommand(
        args: Namespace, 
        pbar: Optional[tqdm]
        ) -> Tuple[int, List[str]]:
    '''gets command for git commit'''
    info("\ncommitting", pbar)
    cmd: List[str] = _getcommitcommand(args)
    if pbar:
        pbar.update(1)
    return 1, cmd

def pulldiffcommand(
        args: Namespace,
        pbar: Optional[tqdm]
        ) -> Tuple[int, List[str]]:
    '''Get command to show diff after pull'''
    info("changes: ", pbar)
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
    elif gitcommand == "pull":
        precmd = []
        cmd = ["git", "pull"] + commandarguments + ["--autostash"]
    elif gitcommand == "clone":
        precmd = []
        cmd = ["git", "clone"] + commandarguments + ["--verbose", "--recursive", "--remote-submodules"]
    else:
        precmd = []
        cmd = ["git", gitcommand] + commandarguments
    
    return precmd, cmd

def suggestfix(errormsg: str) -> str:
    msg = errormsg.lower()
    feedback: List[str] = []
    if "non-fast-forward" in msg or "rejected" in msg:
        feedback.append("try running `git pull` before pushing, or use --force-with-lease")
    if "permission denied" in msg:
        feedback.append("check your ssh keys or credentials")
    if "Already up to date." in msg:
        feedback.append(f"    i {Fore.CYAN}everything up to date")
    if "nothing to commit" in msg:
        feedback.append(f"    i {Fore.CYAN}nothing to commit")
    if "Changes not staged for commit:":
        feedback.append(f"    i {Fore.CYAN}there are unstaged changes") # TODO: find out how to print unstaged files
    
    return "\n".join(feedback)

def runcmd(
    cmd: List[str],
    flags: Namespace = MinimalNamespace,
    pbar: Optional[tqdm] = None,
    withprogress: bool = True,
    captureoutput: bool = True,
    printsuccess: bool = True,
    isinteractive: Optional[bool] = None
) -> Optional[CompletedProcess[bytes]]:
    """
    Executes a command with error handling. When with_progress is True, it uses a progress bar and a loading animation.
    Otherwise, it runs the command directly without additional UI.
    """
    if not cmd:
        return None

    # check if this is an interactive command
    interactive = (cmd[0] == "git" and cmd[1] == "commit" and len(cmd) == 2)
    if isinteractive is not None:
        interactive = isinteractive
        if (cmd[0] == "git" and cmd[1] == "commit" and len(cmd) == 2):
            interactive = True

    if interactive:
        captureoutput = False
        if pbar:
            pbar.clear()

    currentdirectory: str = getcwd()
    cmdstr: str = list2cmdline(cmd)
    if flags.dry:
        printcmd(cmdstr, pbar)
        return None

    try:
        info("    running command:", pbar)
        printcmd(f"      $ {cmdstr}", pbar)
        cmdargs: List[str] = cmd.copy()
        result: Optional[CompletedProcess[bytes]] = None

        if len(cmd) > 1 and cmd[1] == "log":
            result = runsubprocess(cmd, check=False)
            return result

        if interactive:
            result = runsubprocess(cmdargs, check=True, cwd=currentdirectory, capture_output=captureoutput)
            if result and pbar:
                printoutput(result, flags, pbar, pbar)
            return result

        if not withprogress:
            result = runsubprocess(cmdargs, check=True, cwd=currentdirectory, capture_output=captureoutput)
            if result:
                printoutput(result, flags, pbar, pbar)
            if printsuccess:
                success("    ✓ completed successfully", pbar)
            return result

        basecmd: str = cmd[1] if len(cmd) > 1 else ''
        defaultmsg: str = f"executing {cmdstr}..."
        loadingmsg: str = GITCOMMANDMESSAGES.get(basecmd, defaultmsg)

        with tqdm(
            total=100,
            desc=f"{Fore.CYAN}mrrping...{Style.RESET_ALL}",
            bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt}',
            position=1,
            leave=False
        ) as inner_pbar:
            inner_pbar.update(10)
            animation = startloadinganimation(loadingmsg)
            result = runsubprocess(cmdargs, check=True, cwd=currentdirectory, capture_output=captureoutput)
            inner_pbar.n = 50
            inner_pbar.refresh()

            stoploadinganimation(animation)
            if result:
                printoutput(result, flags, inner_pbar, pbar)
            inner_pbar.n = 100
            inner_pbar.colour = 'green'
            inner_pbar.refresh()
            if printsuccess:
                success("    ✓ completed successfully", pbar)
            return result
    except CalledProcessError as e:
        if pbar is not None:
            pbar.colour = 'magenta'
            pbar.refresh()
        error(f"\n❌ command failed with exit code {e.returncode}:", pbar)
        printcmd(f"  $ {cmdstr}", pbar)
        outstr: str = e.stdout.decode('utf-8', errors='replace') if e.stdout else ""
        errstr: str = e.stderr.decode('utf-8', errors='replace') if e.stderr else ""
        if outstr:
            info(f"{Fore.BLACK}{outstr}", pbar)
        if errstr:
            error(f"{Fore.RED}{errstr}", pbar)
            suggestion = suggestfix(errstr)
            if suggestion:
                error(suggestion, pbar)
        if not flags.cont:
            exit(e.returncode)
        else:
            info(f"{Fore.CYAN}continuing...", pbar)
        return None
    except KeyboardInterrupt:
        error(f"{Fore.CYAN}user interrupted", pbar)
        return None

@contextmanager
def incrementprogress(pbar: tqdm, by: int = 1):
    start = time()
    try:
        yield lambda: time() - start
    finally:
        pbar.update(by)
        pbar.refresh()