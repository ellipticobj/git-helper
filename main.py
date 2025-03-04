from os import getcwd
from time import time
from tqdm import tqdm
from sys import exit, argv
from collections.abc import Callable
from colorama import init, Fore, Style
from subprocess import CompletedProcess
from argparse import ArgumentParser, Namespace
from typing import List, Optional, Final, Dict, Union, Tuple
from loaders import startloadinganimation, stoploadinganimation, ThreadEventTuple
from loggers import success, info, printinfo, showcommitresult, printsteps, printdiff, spacer
from helpers import completebar, initcommands, validateargs, pushcommand, statuscommand, submodulesupdatecommand, \
    stashcommand, pullcommand, stagecommand, diffcommand, commitcommand, pulldiffcommand, runcmd, GITCOMMANDMESSAGES

'''
main entry point
'''

# initialize colorama
init(autoreset=True)

VERSION: Final[str] = "0.2.5-preview4"

KNOWNCMDS: List[str] = list(GITCOMMANDMESSAGES.keys())

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
            handlegitcommands(args, GITCOMMANDMESSAGES)
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

def generatereport(report: List[dict], totaltime: float, pbar: Optional[tqdm] = None, savetofile: Optional[str] = None) -> None:
    '''generates a report of the pipeline'''
    output: List[str] = []
    output.append("\n")
    output.append("report:\n")
    for i, step in enumerate(report, start=1):
        output.append(f"step: {step['step']}\n")
        output.append(f"  command: {step.get('command', 'N/A')}\n")
        output.append(f"  duration: {step['duration']:.8f} seconds\n")
        if step.get("output"):
            output.append(f"  output: {step['output']}\n")
        if step.get("returncode"):
            output.append(f"  return code: {step['returncode']}\n")
        output.append("\n")
    output.append(f"total duration: {totaltime:.8f} seconds\n")

    if savetofile:
        with open(savetofile, 'w') as f:
            for line in output:
                f.write(line)
    else:
        for line in output:
            info(message=line, pbar=pbar)

def displayheader() -> None:
    '''displays header'''
    print(f"{Fore.MAGENTA}{Style.BRIGHT}meow {Style.RESET_ALL}{Fore.CYAN}v{VERSION}{Style.RESET_ALL}")
    print(f"\ncurrent directory: {Style.BRIGHT}{getcwd()}\n")

def displaysteps(steps: List[str]) -> None:
    '''displays the steps'''
    print(f"\n{Fore.CYAN}{Style.BRIGHT}meows to meow:{Style.RESET_ALL}")
    printsteps(steps)

def runandreporton(
        func: Callable, 
        flags: Namespace, 
        pbar: Optional[tqdm], 
        noprogressbar: bool = False, 
        printsuccess: bool = True, 
        customsuccess: str = "", 
        printcmd: Optional[Callable] = None
        ) -> Tuple[ Dict[str, Union[str, float, List[str]]], int]:
    '''
    runs a command returned by func, 
    and returns a tuple with the report generated, and the number of steps completed
    '''
    toadd: int
    cmd: List[str]
    stepstart: float = time()
    output: Optional[CompletedProcess[bytes]]
    toadd, cmd = func(flags, progressbar=pbar)
    if noprogressbar:
        output = runcmd(cmd=cmd, flags=flags, pbar=pbar, printsuccess=printsuccess)
    else:
        output = runcmd(cmd=cmd, pbar=pbar, printsuccess=printsuccess, withprogress=False)
    if output and printcmd:
        outputstr: str = output.stdout.decode('utf-8', errors='replace').strip()
        printcmd(outputstr, pbar)
        success(customsuccess, pbar)
            
    duration = time() - stepstart
    return {
        "step": "update submodules",
        "command": " ".join(cmd) if cmd else "",
        "duration": duration,
        "output": output.stdout.decode('utf-8', errors='replace') if output else "",
        "returncode": output.returncode if output else ""
    }, toadd

def runpipeline(args: Namespace) -> None:
    # show pipeline overview
    toadd: int
    steps = getsteps(args)
    starttime: float = time()
    totalsteps: int = len(steps)
    reportitem: Dict[str, Union[str, float, List[str]]]
    report: List[Dict[str, Union[str, float, List[str]]]] = []

    displaysteps(steps)

    # execute pipeline
    with tqdm(total=len(steps), desc=f"{Fore.RED}meowing...{Style.RESET_ALL}", bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt}', position=0, leave=True) as progressbar:
        # status
        reportitem, toadd = runandreporton(func=statuscommand, noprogressbar=True, flags=args, pbar=progressbar)
        report.append(reportitem)
        progressbar.update(toadd)
        
        # update submodules
        reportitem, toadd = runandreporton(func=submodulesupdatecommand, flags=args, pbar=progressbar)
        report.append(reportitem)
        progressbar.update(toadd)

        # stash
        reportitem, toadd = runandreporton(func=stashcommand, flags=args, pbar=progressbar)
        report.append(reportitem)
        progressbar.update(toadd)

        # pull
        reportitem, toadd = runandreporton(func=pullcommand, flags=args, pbar=progressbar)
        report.append(reportitem)
        progressbar.update(toadd)

        if args.pull or args.norebase:
            reportitem, toadd = runandreporton(func=pulldiffcommand, noprogressbar=True, flags=args, pbar=progressbar, printsuccess=False, customsuccess="  ✓ changes shown", printcmd=printdiff)
            progressbar.update(toadd)
            report.append(reportitem)
            
        # add
        reportitem, toadd = runandreporton(func=stagecommand, flags=args, pbar=progressbar)
        report.append(reportitem)
        progressbar.update(toadd)

        # diff
        reportitem, toadd = runandreporton(func=diffcommand, noprogressbar=True, flags=args, pbar=progressbar)
        report.append(reportitem)
        progressbar.update(toadd)

        # commit
        reportitem, toadd = runandreporton(func=commitcommand, flags=args, pbar=progressbar)
        progressbar.update(toadd)
        report.append(reportitem)

        spacer(pbar=progressbar)

        if reportitem["output"] and reportitem["returncode"] == 0:
            showcmd: List[str] = ["git", "show", "-s", "--pretty=format:%H|%an|%ad|%s"]
            output = runcmd(showcmd, args, pbar=progressbar, printsuccess=False)
            if output and output.returncode == 0:
                showcommitresult(output, progressbar)
            success("    ✓ comleted succesfully", progressbar)

        spacer(pbar=progressbar)

        # push
        reportitem, toadd = runandreporton(func=pushcommand, flags=args, pbar=progressbar)
        report.append(reportitem)
        progressbar.update(toadd)

        totaltime = time() - starttime
        
        if args.report:
            generatereport(report=report, totaltime=totaltime)
        else:
            generatereport(report=report, totaltime=totaltime, savetofile="report.txt")
            spacer(pbar=progressbar)
            info(message="report generated in report.txt", pbar=progressbar)
            spacer(pbar=progressbar)

        completebar(progressbar, totalsteps)
        
def main() -> None:
    '''entry point'''
    # init
    parser: ArgumentParser = ArgumentParser(
        prog="meow",
        epilog=f"{Fore.MAGENTA}{Style.BRIGHT}meow {Style.RESET_ALL}{Fore.CYAN}v{VERSION}{Style.RESET_ALL}"
    )
    initcommands(parser)
    checkargv(argv, parser)
    args: Namespace = parser.parse_args()
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

    print("\n😺")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}{Style.BRIGHT}operation cancelled by user{Style.RESET_ALL}")
        exit(1)
    except Exception as e:
        print(f"\n\n{Fore.MAGENTA}{Style.BRIGHT}error: {Style.RESET_ALL}{Fore.RED}{e}{Style.RESET_ALL}")
