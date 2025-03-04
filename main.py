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
from loggers import success, info, printinfo, spacer
from helpers import completebar, initcommands, validateargs, pushcommand, statuscommand, submodulesupdatecommand, \
    stashcommand, pullcommand, stagecommand, diffcommand, commitcommand, pulldiffcommand, runcmd, GITCOMMANDMESSAGES, \
    incrementprogress

'''
main entry point

file pipeline:
loaders -> loggers -> helpers -> githandler -> main
'''

# initialize colorama
init(autoreset=True)

VERSION: Final[str] = "0.2.5-preview5"

KNOWNCMDS: List[str] = list(GITCOMMANDMESSAGES.keys())

class PipelineStep:
    '''step in the pipeline'''
    def __init__(self, name: str, func: Callable[[Namespace, Optional[tqdm]], Tuple[int, List[str]]], nopbar: bool = False):
        self.name = name
        self.func = func
        self.nopbar = nopbar

    def execute(self, args: Namespace, pbar: Optional[tqdm]) -> Tuple[Dict[str, Union[str, float, int]], int]:
        '''execute the step'''
        start = time()
        toadd, cmd = self.func(args, pbar=pbar) # type: ignore

        result: Optional[CompletedProcess[bytes]] = runcmd(
            cmd=cmd,
            flags=args,
            pbar=pbar,
            withprogress=not self.nopbar
        )
        duration = time() - start
        report = {
            "step": self.name,
            "command": " ".join(cmd) if cmd else "",
            "duration": duration,
            "output": result.stdout.decode("utf-8", errors="replace") if result else "",
            "returncode": result.returncode if result else ""
        }
        return report, toadd # type: ignore
    
class Pipeline:
    '''pipeline'''
    def __init__(self, args: Namespace, steps: List[PipelineStep], pbar: tqdm):
        self.args = args
        self.steps = steps
        self.pbar = pbar
        self.report: List[Dict[str, Union[str, float]]] = []

    def run(self) -> None:
        '''loops through items in self.steps and runs them'''
        starttime = time()
        for step in self.steps:
            reportitem, toadd = step.execute(self.args, self.pbar)
            with incrementprogress(self.pbar, by=toadd):
                self.report.append(reportitem)
        totaltime = time() - starttime
        self.report.append({"step": "TOTAL", "duration": totaltime})
        completebar(self.pbar, self.pbar.total)

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

def getsteps(args: Namespace) -> List[PipelineStep]:
    '''gets the commands the program has to complete'''
    steps: List[PipelineStep] = []

    # get status
    if args.status:
        steps.append(PipelineStep("get status", statuscommand, nopbar=True))

    # update submodules
    if args.updatesubmodules:
        steps.append(PipelineStep("update submodules", submodulesupdatecommand))

    # stash
    if args.stash:
        steps.append(PipelineStep("stash changes", stashcommand))
    
    # pull
    if args.pull or args.norebase:
        steps.append(PipelineStep("pull from remote", pullcommand))
        steps.append(PipelineStep("get pull diff", pulldiffcommand, nopbar=True))
    
    # stage changes
    steps.append(PipelineStep("stage changes", stagecommand))
    if args.diff:
        steps.append(PipelineStep("get diff", diffcommand, nopbar=True))
    
    # commit changes
    steps.append(PipelineStep("commit changes", commitcommand))

    # push
    if not args.nopush:
        steps.append(PipelineStep("push changes", pushcommand))
    
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

def displaysteps(steps: List[PipelineStep]) -> None:
    '''displays the steps'''
    print(f"\n{Fore.CYAN}{Style.BRIGHT}meows to meow:{Style.RESET_ALL}")

    i: int
    step: PipelineStep
    for i, step in enumerate(steps, 1): 
        print(f"  {Fore.BLUE}{i}.{Style.RESET_ALL} {Fore.BLACK}{step.name}{Style.RESET_ALL}")
    print()

def runandreporton(
        func: Callable, 
        stepname: str,
        flags: Namespace, 
        pbar: Optional[tqdm], 
        nopbar: bool = False, 
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
    toadd, cmd = func(flags, pbar=pbar)
    if nopbar:
        output = runcmd(cmd=cmd, flags=flags, pbar=pbar, printsuccess=printsuccess)
    else:
        output = runcmd(cmd=cmd, pbar=pbar, printsuccess=printsuccess, withprogress=False)
    if output and printcmd:
        outputstr: str = output.stdout.decode('utf-8', errors='replace').strip()
        printcmd(outputstr, pbar)
        success(customsuccess, pbar)
            
    duration = time() - stepstart
    return {
        "step": stepname,
        "command": " ".join(cmd) if cmd else "",
        "duration": duration,
        "output": output.stdout.decode('utf-8', errors='replace') if output else "",
        "returncode": output.returncode if output else ""
    }, toadd

def runpipeline(args: Namespace) -> None:
    # show pipeline overview
    steps = getsteps(args)
    totalsteps: int = len(steps)

    displaysteps(steps)

    # execute pipeline
    with tqdm(total=len(steps), desc=f"{Fore.RED}meowing...{Style.RESET_ALL}", bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt}', position=0, leave=True) as pbar:
        pipeline = Pipeline(args, steps, pbar)
        pipeline.run()

        totaltime: int = int(pipeline.report[-1].get("duration", 0))

        if args.report:
            generatereport(report=pipeline.report, totaltime=totaltime)
        else:
            generatereport(report=pipeline.report, totaltime=totaltime, savetofile="report.txt")
            spacer(pbar=pbar)
            info(message="report generated in report.txt", pbar=pbar)
            spacer(pbar=pbar)

        completebar(pbar, totalsteps)
        
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
