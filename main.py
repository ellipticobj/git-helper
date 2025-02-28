import os
import sys
import subprocess
import time
from argparse import ArgumentParser, Namespace, _ArgumentGroup
from typing import List, Union, Optional
from colorama import Fore, Style, init # type: ignore
from tqdm import tqdm # type: ignore

# initialize colorama
init(autoreset=True)

VERSION = "0.2.3-preview2"

def success(message: str, pbar: Optional[tqdm] = None) -> None:
    '''print success message'''
    if pbar:
        pbar.write(f"{Fore.GREEN}{Style.BRIGHT}{message}")
    else:
        print(f"{Fore.GREEN}{Style.BRIGHT}{message}")

def error(message: str, pbar: Optional[tqdm] = None) -> None:
    '''print error message'''
    if pbar:
        pbar.write(f"{Fore.RED}{Style.BRIGHT}{message}")
    else:
        print(f"{Fore.RED}{Style.BRIGHT}{message}")

def info(message: str, pbar: Optional[tqdm] = None) -> None:
    '''print info message'''
    if pbar:
        pbar.write(f"{Fore.BLUE}{message}")
    else:
        print(f"{Fore.BLUE}{message}")

def warning(message: str, pbar: Optional[tqdm] = None) -> None:
    '''print warning message'''
    if pbar:
        pbar.write(f"{Fore.YELLOW}{Style.BRIGHT}{message}")
    else:
        print(f"{Fore.YELLOW}{Style.BRIGHT}{message}")

def printcmd(cmd: str, pbar: Optional[tqdm] = None) -> None:
    '''prints a command'''
    if pbar:
        pbar.write(f"{Fore.CYAN}{cmd}")
    else:
        print(f"{Fore.CYAN}{cmd}")

def progressbar(description: str, duration: float = 0.5) -> None:
    '''progress bar'''
    with tqdm(total=100, desc=f"{Fore.CYAN}{description}{Style.RESET_ALL}", bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt}') as pbar:
        for _ in range(100):
            time.sleep(duration / 100)
            pbar.update(1)

def initcommands(parser: ArgumentParser) -> None:
    '''initialize commands with commands.'''
    # core functionality
    parser.add_argument("message", nargs='?', help="commit message (overrides --no-message)")
    parser.add_argument("-a", "--add", dest="add", nargs="+", help="select specific files to stage")

    # general options
    general_group: _ArgumentGroup = parser.add_argument_group("general options")
    general_group.add_argument("-v", "--version", action='store_true', help="show version")
    general_group.add_argument("-c", "--continue", dest="cont", action='store_true', help="continue after errors")
    general_group.add_argument("-q", "--quiet", action='store_true', help="suppress output")
    general_group.add_argument("-ve", "--verbose", action='store_true', help="verbose output")
    general_group.add_argument("--dry", dest = "dry", action='store_true', help="preview commands without execution")
    general_group.add_argument("--status", action='store_true', help="show git status before executing commands")

    # commit options
    commit_group: _ArgumentGroup = parser.add_argument_group("commit options")
    commit_group.add_argument("-n", "--no-message", dest="nomsg", action='store_true', help="allow empty commit message")
    commit_group.add_argument("--allow-empty", dest="allowempty", action='store_true', help="allow empty commit")
    commit_group.add_argument("--diff", action='store_true', help="show diff before committing")
    commit_group.add_argument("--amend", action='store_true', help="amend previous commit")

    # push options
    push_group: _ArgumentGroup = parser.add_argument_group("push options")
    push_group.add_argument("-u", "--upstream", "--set-upstream", nargs='+', metavar="REMOTE/BRANCH", help="set upstream branch to push to (formats: REMOTE BRANCH or REMOTE/BRANCH)")
    push_group.add_argument("-f", "--force", action='store_true', help="force push")
    push_group.add_argument("-np", "--no-push", action='store_true', help="skip pushing")
    push_group.add_argument("--tags", action='store_true', help="push tags with commits")

    # pull options
    pull_group: _ArgumentGroup = parser.add_argument_group("pull options")
    pull_group.add_argument("--pull", action='store_true', help="run git pull before pushing")
    pull_group.add_argument("--pull-no-rebase", dest="norebase", action='store_true', help="run git pull --no-rebase (overrides --pull)")

    # advanced options
    advanced_group: _ArgumentGroup = parser.add_argument_group("advanced options")
    advanced_group.add_argument("--update-submodules", dest="updatesubmodules", action='store_true', help="update submodules recursively")
    advanced_group.add_argument("--stash", action='store_true', help="stash changes before pull")

def validateargs(args: Namespace) -> None:
    '''validate argument combinations'''
    if not args.amend and not args.nomsg and not args.message:
        raise ValueError("commit message required (use --amend, --no-message, or provide message)")

def printinfo() -> None:
    print(f"{Fore.MAGENTA}{Style.BRIGHT}meow{Style.RESET_ALL} version {Fore.CYAN}{VERSION}{Style.RESET_ALL}")
    print(f"{Fore.BLUE}https://github.com/ellipticobj/meower{Style.RESET_ALL}")
    sys.exit(1)

def pullhandler(args: Namespace) -> None:
    '''handles git pull operations'''
    pull: List[str] = ["git", "pull"]
    if args.norebase:
        pull.append("--no-rebase")
    if args.pull or args.norebase:
        if hasattr(args, 'mainpbar'): # checks of the main bar exists
            runcmd(pull, args, mainpbar=args.mainpbar)
        else:
            runcmd(pull, args, args.cont, args.dry)

def commithelper(args: Namespace) -> List[str]:
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

def pushhelper(args: Namespace) -> Union[None, List[str]]:
    if not args.no_push:
        push: List[str] = ["git", "push"]
        if args.tags:
            push.append("--tags")

        if args.upstream:
            if len(args.upstream) == 1 and '/' in args.upstream[0]:
                # use REMOTE/BRANCH format
                remote, branch = args.upstream[0].split('/')
                push.extend(["--set-upstream", remote, branch])
            elif len(args.upstream) == 2:
                # use REMOTE BRANCH format
                push.extend(["--set-upstream", args.upstream[0], args.upstream[1]])
            else:
                error("invalid upstream format. Use 'REMOTE BRANCH' or 'REMOTE/BRANCH'")
                sys.exit(1)

        if args.force:
            push.append("--force")

        if args.quiet:
            push.append("--quiet")
        elif args.verbose:
            push.append("--verbose")
        
        return push
    return None

def runcmd(args: List[str], flags: Namespace, mainpbar: Optional[tqdm] = None, showprogress: bool = True,) -> Optional[subprocess.CompletedProcess]:
    '''executes a command with error handling'''
    cwd = os.getcwd()
    cmdstr = subprocess.list2cmdline(args)
    
    if flags.dry:
        printcmd(cmdstr, mainpbar)
        return None

    try:
        info(f"\n  running command from directory: {Style.BRIGHT}{cwd}:", mainpbar)
        printcmd(f"    $ {cmdstr}", mainpbar)
        
        # capture output to parse relevant messages
        cmdargs = args.copy()
        result = None
        
        if showprogress:
            with tqdm(total=100, desc=f"{Fore.CYAN}mrrping...{Style.RESET_ALL}", bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt}', position=1, leave=True) as pbar:
                # start progress bar
                pbar.update(10)
                
                try:
                    result = subprocess.run(cmdargs, check=True, cwd=cwd, capture_output=True)
                    # complete bar immediately
                    pbar.n = 100
                    pbar.refresh()
                    
                    # parse output
                    outputstr = result.stdout.decode('utf-8', errors='replace').strip()
                    if outputstr:
                        # check for specific outputs
                        if 'Everything up-to-date' in outputstr:
                            info(f"    ℹ️ {Fore.CYAN}Everything already up-to-date", mainpbar)
                        elif 'nothing to commit' in outputstr:
                            info(f"    ℹ️ {Fore.CYAN}Nothing to commit, working tree clean", mainpbar)
                        elif 'create mode' in outputstr or 'delete mode' in outputstr:
                            # show additions/deletions
                            info(f"    ℹ️ {Fore.BLACK}{outputstr}", mainpbar)
                        elif len(outputstr) < 200:  # show short messages
                            if flags.message in outputstr: # dont duplicate commit message
                                pass
                            else:
                                info(f"    ℹ️ {Fore.BLACK}{outputstr}", mainpbar)
                    
                    success("  ✓ completed successfully", mainpbar)
                    return result
                except subprocess.CalledProcessError as e:
                    # change bar to red if command fails
                    pbar.desc = f"{Fore.RED}  command failed{Style.RESET_ALL}"
                    pbar.n = 100  # still complete the bar
                    pbar.refresh()
                    raise e  # raise exception
        else:
            result = subprocess.run(cmdargs, check=True, cwd=cwd, capture_output=True)
            # parse output
            outputstr = result.stdout.decode('utf-8', errors='replace').strip()
            if outputstr:
                # check for specific outputs
                if 'Everything up-to-date' in outputstr:
                    info(f"    ℹ️ {Fore.CYAN}everything up to date!", mainpbar)
                elif 'nothing to commit' in outputstr:
                    info(f"    ℹ️ {Fore.CYAN}nothing to commit!", mainpbar)
                elif len(outputstr) < 200:  # short messages
                    info(f"    ℹ️ {Fore.BLACK}{outputstr}", mainpbar)
            
            success("  ✓ completed successfully", mainpbar)
            return result
            
    except subprocess.CalledProcessError as e:
        error(f"\n❌ command failed with exit code {e.returncode}:", mainpbar)
        printcmd(f"  $ {cmdstr}", mainpbar)
        if e.stdout:
            info(f"{Fore.BLACK}{e.stdout.decode('utf-8', errors='replace')}", mainpbar)
        if e.stderr:
            error(f"{Fore.RED}{e.stderr.decode('utf-8', errors='replace')}", mainpbar)
        
        if not flags.cont:
            sys.exit(e.returncode)
    return None

def main() -> None:
    # fancy header 
    print(f"{Fore.MAGENTA}{Style.BRIGHT} meow {Style.RESET_ALL}{Fore.CYAN}v{VERSION}{Style.RESET_ALL}")

    # init 
    parser: ArgumentParser = ArgumentParser(
        prog=f"{Fore.MAGENTA}{Style.BRIGHT}meow{Style.RESET_ALL}",
        description=f"{Fore.CYAN}git wrapper{Style.RESET_ALL}"
    )
    initcommands(parser)

    # get args
    args: Namespace = parser.parse_args()

    # check args
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
    elif len(sys.argv) == 2:
        if sys.argv[1] == "meow":
            print(f"{Fore.MAGENTA}{Style.BRIGHT}meow meow :3{Style.RESET_ALL}")
            sys.exit(0)
        elif sys.argv[1] == "--version" or sys.argv[1] == "-v":
            printinfo()

    if args.dry:
        print(f"{Fore.MAGENTA}{Style.BRIGHT}dry run{Style.RESET_ALL}")

    if len(sys.argv) == 2:
        if sys.argv[1] == "meow":
            print(f"{Fore.MAGENTA}{Style.BRIGHT}meow meow :3{Style.RESET_ALL}")
            sys.exit(1)

    if args.version:
        print(f"{Fore.MAGENTA}{Style.BRIGHT}meow{Style.RESET_ALL} version {Fore.CYAN}{VERSION}{Style.RESET_ALL}")
        print(f"{Fore.BLUE}https://github.com/ellipticobj/meower{Style.RESET_ALL}")
        sys.exit()

    try:
        validateargs(args)
    except ValueError as e:
        error(f"error: {str(e)}")
        sys.exit(1)

    # display pipeline steps
    steps = []
    if args.status:
        steps.append("status check")
    if args.updatesubmodules:
        steps.append("update submodules")
    if args.stash:
        steps.append("stash changes")
    if args.pull or args.norebase:
        steps.append("pull from remote")
    steps.append("stage changes")
    if args.diff:
        steps.append("show diff")
    steps.append("commit changes")
    if not args.no_push:
        steps.append("push to remote")
    
    # show pipeline overview
    print(f"\n{Fore.CYAN}{Style.BRIGHT}meows to meow:{Style.RESET_ALL}")
    for i, step in enumerate(steps, 1):
        print(f"  {Fore.BLUE}{i}.{Style.RESET_ALL} {Fore.BLACK}{step}{Style.RESET_ALL}")
    print()

    # execute pipeline
    with tqdm(total=len(steps), desc=f"{Fore.MAGENTA}meowing...{Style.RESET_ALL}", bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt}', position=0, leave=True) as progressbar:
        completedsteps = 0
        totalsteps = len(steps)
        
        # status check
        if args.status:
            info(f"{Style.BRIGHT}status check{Style.RESET_ALL}", progressbar)
            runcmd(["git", "status"], args, mainpbar=progressbar, showprogress=False)
            completedsteps += 1
            progressbar.update(1)

        # update submodules
        if args.updatesubmodules:
            info(f"\n{Style.BRIGHT}updating submodules{Style.RESET_ALL}", progressbar)
            runcmd(["git", "submodule", "update", "--init", "--recursive"], args, mainpbar=progressbar)
            completedsteps += 1
            progressbar.update(1)

        # stash changes
        if args.stash:
            info(f"\n{Style.BRIGHT}stashing changes{Style.RESET_ALL}", progressbar)
            runcmd(["git", "stash"], args, mainpbar=progressbar)
            completedsteps += 1
            progressbar.update(1)

        # pull
        if args.pull or args.norebase:
            info(f"\n{Style.BRIGHT}pulling from remote{Style.RESET_ALL}",progressbar)
            # Create a copy of args with the progress bar added
            args.mainpbar = progressbar
            pullhandler(args)
            completedsteps += 1
            progressbar.update(1)

        # stage changes
        info(f"\n{Style.BRIGHT}staging changes{Style.RESET_ALL}", progressbar)
        addcmd: List[str] = ["git", "add", *args.add] if args.add else ["git", "add", "."]
        if args.verbose and not args.quiet:
            addcmd.append("--verbose")
        runcmd(addcmd, args, mainpbar=progressbar)
        completedsteps += 1
        progressbar.update(1)

        # diff
        if args.diff:
            info(f"\n{Style.BRIGHT}showing diff{Style.RESET_ALL}", progressbar)
            runcmd(["git", "diff", "--staged"], args, showprogress=False, mainpbar=progressbar)
            completedsteps += 1
            progressbar.update(1)

        # commit
        info(f"\n{Style.BRIGHT}committing{Style.RESET_ALL}", progressbar)
        commit = commithelper(args)
        runcmd(commit, args, mainpbar=progressbar)
        completedsteps += 1
        progressbar.update(1)

        # push
        push: Optional[List[str]] = pushhelper(args)
        if push:
            info(f"\n{Style.BRIGHT}pushing to remote{Style.RESET_ALL}", progressbar)
            runcmd(push, args, mainpbar=progressbar)
            completedsteps += 1
            progressbar.update(1)
        
        # ensure progress bar is 100%
        if completedsteps < totalsteps:
            progressbar.n = totalsteps
            progressbar.refresh()
    
    # success message
    print("\n😺")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}{Style.BRIGHT}operation cancelled by user{Style.RESET_ALL}")
        sys.exit(1)