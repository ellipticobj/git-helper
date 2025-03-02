from os import getcwd
from tqdm import tqdm
from sys import exit, argv
from colorama import init, Fore, Style
from argparse import ArgumentParser, Namespace
from typing import List, Optional, Final
from loaders import startloadinganimation, stoploadinganimation, ThreadEventTuple
from subprocess import list2cmdline, run as runsubprocess, CompletedProcess, CalledProcessError
from loggers import success, error, info, printcmd, printinfo, printsteps, printoutput, showcommitresult
from helpers import completebar, initcommands, validateargs, getpushcommand, getstatuscommand, getsubmoduleupdatecommand, getstashcommand, getpullcommand, getstagecommand, getdiffcommand, getcommitcommand

# initialize colorama
init(autoreset=True)

GITCOMMANDMESSAGES = {
    'log': 'q to exit: ',
    'commit': 'committing...',
    'add': 'staging...',
    'push': 'pushing...',
    'pull': 'pulling...',
    'clone': 'cloning...',
    'status': 'checking repo status...'
}
KNOWNCMDS: List[str] = ['push', 'pull', 'commit', 'add', 'log', 'clone']
VERSION: Final[str] = "0.2.5-preview1"
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
        captureoutput: bool = True
        ) -> CompletedProcess[bytes]:
    '''runs command without progressbar'''
    result: CompletedProcess[bytes] = runsubprocess(cmd, check=True, cwd=getcwd(), capture_output=captureoutput)
    # parse output
    outputstr: str = result.stdout.decode('utf-8', errors='replace').strip()
    if outputstr:
        if 'Everything up-to-date' in outputstr:
            info(f"    i {Fore.CYAN}everything up to date", mainpbar)
        elif 'nothing to commit' in outputstr:
            info(f"    i {Fore.CYAN}nothing to commit", mainpbar)
        elif len(outputstr) < 200:  # short messages
            info(f"    i {Fore.BLACK}{outputstr}", mainpbar)

    success("  ✓ completed successfully", mainpbar)
    return result

def runcmd(
        cmd: List[str], 
        flags: Namespace = MinimalNamespace, 
        mainpbar: Optional[tqdm] = None, 
        keepbar: bool = False, 
        captureoutput: bool = True
        ) -> Optional[CompletedProcess[bytes]]:
    '''executes a command with error handling'''
    if len(cmd) < 1: # if command is [], exit immediately
        return None

    cwd: str = getcwd()
    cmdstr: str = list2cmdline(cmd)

    if flags.dry:
        printcmd(cmdstr, mainpbar)
        return None

    try:
        info("  running command:", mainpbar)
        printcmd(f"    $ {cmdstr}", mainpbar)

        # capture output to parse relevant messages
        cmdargs: List[str] = cmd.copy()
        result: Optional[CompletedProcess[bytes]]

        basecmd = cmd[1] if len(cmd) > 1 else ''
        defaultcmd = f"executing {cmdstr}..."
        animationmessage: str = GITCOMMANDMESSAGES.get(basecmd, defaultcmd)

        with tqdm(total=100, desc=f"{Fore.CYAN}mrrping...{Style.RESET_ALL}", bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt}', position=1, leave=keepbar) as pbar:
            pbar.update(10)
            animation: ThreadEventTuple = startloadinganimation(animationmessage)
            result = runsubprocess(cmdargs, check=True, cwd=cwd, capture_output=captureoutput)
            pbar.n = 50
            pbar.refresh()

            stoploadinganimation(animation)
            del animation

            if result:
                printoutput(result, flags, pbar, mainpbar)

            pbar.n = 100
            pbar.colour = 'green'
            pbar.refresh()
            success("  ✓ completed successfully", mainpbar)

            return result
    except CalledProcessError as e:
        error(f"\n❌ command failed with exit code {e.returncode}:", mainpbar)
        printcmd(f"  $ {cmdstr}", mainpbar)

        if e.stdout:
            info(f"{Fore.BLACK}{e.stdout.decode('utf-8', errors='replace')}", mainpbar)

        if e.stderr:
            error(f"{Fore.RED}{e.stderr.decode('utf-8', errors='replace')}", mainpbar)

        if not flags.cont:
            exit(e.returncode)
        else:
            info(f"{Fore.CYAN}continuing...")
        return None
    except KeyboardInterrupt:
        error(f"{Fore.CYAN}user interrupted", mainpbar)
        return None

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
            handlegitcommands(args)
    return None

def handlegitcommands(args: List[str]) -> None:
    '''parses meow <cmd> commands'''
    gitcommand = args[1]
    commandarguments: List[str] = args[2:]
    cmd: List[str]

    # minimal progress bar for git commands
    with tqdm(total=100, desc=f"{Fore.CYAN}mrrping...{Style.RESET_ALL}", bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt}', position=0, leave=True) as mainpbar:
        mainpbar.update(10)
        animation = startloadinganimation(GITCOMMANDMESSAGES.get(gitcommand, "processing..."))
        
        if gitcommand == "add":
            cmd = ["git", "add"] + (commandarguments or ["."])
        elif gitcommand == "commit":
            cmd = ["git", "commit"] + (["-m"] + commandarguments if commandarguments else [])
        # elif gitcommand == "push": # TODO: finish this
        #     pass
        # elif gitcommand == "pull":
        #     pass
        # elif gitcommand == "clone":
        #     pass
        # elif gitcommand == "log":
        #     pass
        else:
            cmd = ["git", gitcommand] + commandarguments

        result = runcmd(cmd=cmd, captureoutput=False, mainpbar=mainpbar)
        
        stoploadinganimation(animation)
        mainpbar.update(100)
        
        if gitcommand == "commit" and result:
            showcommitresult(result=result, mainpbar=mainpbar)
    
    # exit after handling command
    exit(0 if result and result.returncode == 0 else 1)

def getsteps(args: Namespace) -> List[str]:
    steps: List[str] = []

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

    if not args.nopush:
        steps.append("push to remote")

    return steps

def main() -> None:
    # start animatior before initialization
    initializinganimation: ThreadEventTuple = startloadinganimation("initializing...")

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

    # stop the animation after initialization
    stoploadinganimation(initializinganimation)
    del initializinganimation

    # fancy header
    print(f"{Fore.MAGENTA}{Style.BRIGHT}meow {Style.RESET_ALL}{Fore.CYAN}v{VERSION}{Style.RESET_ALL}")

    print(f"\ncurrent directory: {Style.BRIGHT}{getcwd()}")

    if args.dry:
        print(f"\n{Fore.MAGENTA}{Style.BRIGHT}dry run{Style.RESET_ALL}")

    if args.version:
        printinfo(VERSION)

    validateargs(args)

    preparinganimation: ThreadEventTuple = startloadinganimation("preparing...")

    # display pipeline steps
    steps: List[str] = getsteps(args)

    stoploadinganimation(preparinganimation)
    del preparinganimation

    # show pipeline overview
    print(f"\n{Fore.CYAN}{Style.BRIGHT}meows to meow:{Style.RESET_ALL}")

    printsteps(steps)

    # execute pipeline
    with tqdm(total=len(steps), desc=f"{Fore.MAGENTA}meowing...{Style.RESET_ALL}", bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt}', position=0, leave=True) as progressbar:
        completedsteps: int = 0
        totalsteps: int = len(steps)
        toadd: int
        cmd: List[str]

        toadd, cmd = getstatuscommand(args, progressbar)
        runcmdwithoutprogress(cmd=cmd, mainpbar=progressbar)
        completedsteps += toadd

        toadd, cmd = getsubmoduleupdatecommand(args, progressbar)
        runcmd(cmd=cmd, flags=args, mainpbar=progressbar)
        completedsteps += toadd

        toadd, cmd = getstashcommand(args, progressbar)
        runcmd(cmd=cmd, flags=args, mainpbar=progressbar)
        completedsteps += toadd

        toadd, cmd = getpullcommand(args, progressbar)
        runcmd(cmd=cmd, flags=args, mainpbar=args.mainpbar)
        completedsteps += 1

        cmd = getstagecommand(args, progressbar)
        runcmd(cmd=cmd, flags=args, mainpbar=progressbar)
        completedsteps += 1

        toadd, cmd = getdiffcommand(args, progressbar)
        runcmdwithoutprogress(cmd=cmd, mainpbar=progressbar)
        completedsteps += toadd

        cmd = getcommitcommand(args, progressbar)
        runcmd(cmd, args, mainpbar=progressbar)
        completedsteps += 1

        cmd = getpushcommand(args)
        info(f"\n{Style.BRIGHT}pushing to remote{Style.RESET_ALL}", progressbar)
        runcmd(cmd, args, mainpbar=progressbar)
        progressbar.update(1)
        completedsteps += 1

        completebar(progressbar, totalsteps)

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
