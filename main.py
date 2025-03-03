from os import getcwd
from tqdm import tqdm
from sys import exit, argv
from colorama import init, Fore, Style
from argparse import ArgumentParser, Namespace
from typing import List, Optional, Final, Dict
from loaders import startloadinganimation, stoploadinganimation, ThreadEventTuple
from subprocess import list2cmdline, run as runsubprocess, CompletedProcess, CalledProcessError
from loggers import success, error, info, printcmd, printinfo, printsteps, printoutput, showcommitresult
from helpers import completebar, initcommands, validateargs, getpushcommand, getstatuscommand, getsubmoduleupdatecommand, \
    getstashcommand, getpullcommand, getstagecommand, getdiffcommand, getcommitcommand, getpulldiffcommand

# initialize colorama
init(autoreset=True)

VERSION: Final[str] = "0.2.5-preview3"
GITCOMMANDMESSAGES: Dict[str, str] = {
    'log': 'q to exit: ',
    'add': 'staging...',
    'push': 'pushing...',
    'pull': 'pulling...',
    'clone': 'cloning...',
    'fetch': 'fetching...',
    'commit': 'committing...',
    'status': 'checking repo status...'
}
KNOWNCMDS: List[str] = list(GITCOMMANDMESSAGES.keys())

MinimalNamespace = Namespace(
    cont=False, 
    dry=False, 
    verbose=True, 
    quiet=False, 
    mainpbar=None
)

def runcmdwithoutprogress(
        cmd: List[str], 
        mainpbar: Optional[tqdm], 
        captureoutput: bool = True,
        printoutput: bool = True,
        printsuccess: bool = True
        ) -> Optional[CompletedProcess[bytes]]:
    '''runs command without progressbar'''
    if not cmd:
        return None
    
    result: CompletedProcess[bytes] = runsubprocess(cmd, check=True, cwd=getcwd(), capture_output=captureoutput)
    outputstr: str = result.stdout.decode('utf-8', errors='replace').strip()
    if outputstr and printoutput:
        if 'Everything up-to-date' in outputstr:
            info(f"    i {Fore.CYAN}everything up to date", mainpbar)
        elif 'nothing to commit' in outputstr:
            info(f"    i {Fore.CYAN}nothing to commit", mainpbar)
        elif len(outputstr) < 200:  # short messages
            info(f"    i {Fore.BLACK}{outputstr}", mainpbar)
    if printsuccess:
        success("  ✓ completed successfully", mainpbar)
    return result

def runcmd(
        cmd: List[str], 
        flags: Namespace = MinimalNamespace, 
        progressbar: Optional[tqdm] = None, 
        keepbar: bool = False, 
        captureoutput: bool = True
        ) -> Optional[CompletedProcess[bytes]]:
    '''executes a command with error handling'''
    if not cmd:  # if command is empty, exit immediately
        return None

    interactive = (cmd[0] == "git" and cmd[1] == "commit" and len(cmd) == 2)
    if interactive:
        # dont capture output for interactive commands so that git can use the terminal properly.
        captureoutput = False
        if progressbar:
            progressbar.clear()  # clear the main progress bar output

    currentdirectory: str = getcwd()
    cmdstr: str = list2cmdline(cmd)
    if flags.dry:
        printcmd(cmdstr, progressbar)
        return None

    try:
        info("    running command:", progressbar)
        printcmd(f"      $ {cmdstr}", progressbar)
        cmdargs: List[str] = cmd.copy()
        result: Optional[CompletedProcess[bytes]] = None

        # run git log without the extras
        if len(cmd) > 1 and cmd[1] == "log":
            result = runsubprocess(cmd, check=False)
            return result

        if interactive: # run the interactive command without mrrping progress bar
            result = runsubprocess(cmdargs, check=True, cwd=currentdirectory, capture_output=captureoutput)
            if result and progressbar: # use the passed mainpbar for any output display
                printoutput(result, flags, progressbar, progressbar)
            return result
        
        # show a per command progress bar and loader
        basecmd: str = cmd[1] if len(cmd) > 1 else ''
        defaultmsg: str = f"executing {cmdstr}..."
        loadingmsg: str = GITCOMMANDMESSAGES.get(basecmd, defaultmsg)

        with tqdm(
            total=100, 
            desc=f"{Fore.CYAN}mrrping...{Style.RESET_ALL}", 
            bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt}', 
            position=1, 
            leave=keepbar
        ) as pbar:
            pbar.update(10)
            animation = startloadinganimation(loadingmsg)
            result = runsubprocess(cmdargs, check=True, cwd=currentdirectory, capture_output=captureoutput)
            pbar.n = 50
            pbar.refresh()

            stoploadinganimation(animation)
            if result:
                printoutput(result, flags, pbar, progressbar)

            pbar.n = 100
            pbar.colour = 'green'
            pbar.refresh()
            success("    ✓ completed successfully", progressbar)
            return result
    except CalledProcessError as e:
        # update the main progress bar to red before exiting.
        if progressbar is not None:
            progressbar.colour = 'magenta'
            progressbar.refresh()
        
        error(f"\n❌ command failed with exit code {e.returncode}:", progressbar)
        printcmd(f"  $ {cmdstr}", progressbar)
        if e.stdout:
            info(f"{Fore.BLACK}{e.stdout.decode('utf-8', errors='replace')}", progressbar)
        if e.stderr:
            error(f"{Fore.RED}{e.stderr.decode('utf-8', errors='replace')}", progressbar)

        if not flags.cont:
            exit(e.returncode)
        else:
            info(f"{Fore.CYAN}continuing...", progressbar)
        return None
    except KeyboardInterrupt:
        error(f"{Fore.CYAN}user interrupted", progressbar)
        return None

def getsteps(args: Namespace) -> List[str]:
    '''gets the commands the program has to complete'''
    steps: List[str] = []
    if args.status:
        steps.append("status check")
    if args.updatesubmodules:
        steps.append("update submodules")
    if args.stash:
        steps.append("stash changes")
    if args.pull or args.norebase:
        steps.append("pull from remote")
        steps.append("show changes")
    steps.append("stage changes")
    if args.diff:
        steps.append("show diff")
    steps.append("commit changes")
    if not args.nopush:
        steps.append("push to remote")
    return steps

def displayheader() -> None:
    '''displays header'''
    print(f"{Fore.MAGENTA}{Style.BRIGHT}meow {Style.RESET_ALL}{Fore.CYAN}v{VERSION}{Style.RESET_ALL}")
    print(f"\ncurrent directory: {Style.BRIGHT}{getcwd()}\n")

def displaysteps(steps: List[str]) -> None:
    '''displays the steps'''
    print(f"\n{Fore.CYAN}{Style.BRIGHT}meows to meow:{Style.RESET_ALL}")
    printsteps(steps)

def runpipeline(args: Namespace) -> None:
    # show pipeline overview
    steps = getsteps(args)
    displaysteps(steps)

    # execute pipeline
    with tqdm(total=len(steps), desc=f"{Fore.RED}meowing...{Style.RESET_ALL}", bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt}', position=0, leave=True) as progressbar:
        completedsteps: int = 0
        totalsteps: int = len(steps)
        toadd: int
        cmd: List[str]

        # status
        toadd, cmd = getstatuscommand(args, progressbar)
        runcmdwithoutprogress(cmd=cmd, mainpbar=progressbar)
        completedsteps += toadd
        
        # update submodules
        toadd, cmd = getsubmoduleupdatecommand(args, progressbar)
        runcmd(cmd=cmd, flags=args, progressbar=progressbar)
        completedsteps += toadd

        # stash
        toadd, cmd = getstashcommand(args, progressbar)
        runcmd(cmd=cmd, flags=args, progressbar=progressbar)
        completedsteps += toadd

        # pull
        toadd, cmd = getpullcommand(args, progressbar)
        # pullresult: Optional[CompletedProcess[bytes]] = 
        runcmd(cmd=cmd, flags=args, progressbar=progressbar)
        completedsteps += 1
        info(message="", pbar=progressbar)

        if args.pull or args.norebase:
            info(f"\n{Style.BRIGHT}showing pull changes{Style.RESET_ALL}", progressbar)
            diffcmd: List[str] = getpulldiffcommand()
            diffresult = runcmdwithoutprogress(diffcmd, progressbar, captureoutput=True, printoutput=False, printsuccess=False)
            if diffresult:
                printoutput(result=diffresult, flags=args, pbar=progressbar, mainpbar=None)
                success("  ✓ changes shown", progressbar)

            progressbar.update(1)
            completedsteps += 1

        # add
        cmd = getstagecommand(args, progressbar)
        runcmd(cmd=cmd, flags=args, progressbar=progressbar)
        completedsteps += 1

        # diff
        toadd, cmd = getdiffcommand(args, progressbar)
        runcmdwithoutprogress(cmd=cmd, mainpbar=progressbar)
        completedsteps += toadd

        # commit
        cmd = getcommitcommand(args, progressbar)
        commitresult: Optional[CompletedProcess[bytes]] = runcmd(cmd, args, progressbar=progressbar)
        completedsteps += 1
        info(message="", pbar=progressbar)

        if commitresult and commitresult.returncode == 0:
            showcmd: List[str] = ["git", "show", "-s", "--pretty=format:%H|%an|%ad|%s"]
            showresult = runcmd(showcmd, args, progressbar=progressbar)
            if showresult and showresult.returncode == 0:
                showcommitresult(showresult, progressbar)

        cmd = getpushcommand(args)
        info(f"\n{Style.BRIGHT}pushing to remote{Style.RESET_ALL}", progressbar)
        runcmd(cmd, args, progressbar=progressbar)
        progressbar.update(1)
        completedsteps += 1

        completebar(progressbar, totalsteps)

def checkargv(
        args: List[str], 
        parser: ArgumentParser
        ) -> None:
    '''checks sys.argv before flags are parsed'''
    if len(args) == 1: # prints help if user runs `meow`
        parser.print_help()
        print(f"\ncurrent directory: {Style.BRIGHT}{getcwd()}")
        exit(1)
    elif len(args) > 1:
        if len(args) == 2 and args[1] == "meow":
            print(f"{Fore.MAGENTA}{Style.BRIGHT}meow meow :3{Style.RESET_ALL}")
            exit(0)
        elif args[1] in KNOWNCMDS:
            from githandler import handlegitcommands
            handlegitcommands(args)
    return None
def main() -> None:
    '''entry point'''
    # init
    parser: ArgumentParser = ArgumentParser(
        prog="meow",
        epilog=f"{Fore.MAGENTA}{Style.BRIGHT}meow {Style.RESET_ALL}{Fore.CYAN}v{VERSION}{Style.RESET_ALL}"
    )
    initcommands(parser)

    # check argv before parsing args
    checkargv(argv, parser)

    # get args
    args: Namespace = parser.parse_args()

    # fancy header
    displayheader()

    if args.dry:
        print(f"\n{Fore.MAGENTA}{Style.BRIGHT}dry run{Style.RESET_ALL}")

    if args.version:
        printinfo(VERSION)

    validateargs(args)

    preparinganimation: ThreadEventTuple = startloadinganimation("preparing...")

    stoploadinganimation(preparinganimation)
    del preparinganimation

    runpipeline(args=args)

    # success message
    print("\n😺")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}{Style.BRIGHT}operation cancelled by user{Style.RESET_ALL}")
        exit(1)
    except Exception as e:
        print(f"\n\n{Fore.MAGENTA}{Style.BRIGHT}error: {Style.RESET_ALL}{Fore.RED}{e}{Style.RESET_ALL}")
