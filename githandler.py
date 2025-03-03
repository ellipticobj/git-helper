from sys import exit
from os import getcwd
from tqdm import tqdm
from colorama import Fore, Style
from helpers import getgitcommands
from typing import List, Optional, Dict
from loggers import success, error, info, printcmd, showcommitresult
from loaders import startloadinganimation, stoploadinganimation, ThreadEventTuple
from subprocess import list2cmdline, run as runsubprocess, CalledProcessError, CompletedProcess

'''
handles meow <cmd>
'''

def handlegitcommands(args: List[str], messages: Dict[str, str]) -> None:
    '''handles meow <cmd> commands'''
    
    gitcommand = args[1]
    commandarguments: List[str] = args[2:]
    
    if gitcommand == "log":
        cmd = ["git", "log"] + commandarguments
        result: CompletedProcess = runsubprocess(cmd, check=False)
        exit(result.returncode)
    
    lastcmdstr = ""
    try:
        with tqdm(
            total=100,
            desc=f"{Fore.CYAN}mrrping...{Style.RESET_ALL}",
            bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt}',
            position=0,
            leave=True
        ) as mainpbar:
            mainpbar.update(10)
            animation: Optional[ThreadEventTuple] = None

            if not (gitcommand == "commit" and not commandarguments):
                animation = startloadinganimation(getloadingmessage(gitcommand, messages))
            
            precmd, cmd = getgitcommands(gitcommand, commandarguments)
            lastcmdstr = list2cmdline(cmd)
            
            # (optional) pre-command
            runcmd(precmd, mainpbar)
            info(message="", pbar=mainpbar)
            
            # maincommand
            result = runcmd(cmd, mainpbar)
            
            if animation:
                stoploadinganimation(animation)
            mainpbar.update(100)
            
            if gitcommand == "commit" and result:
                showcommitresult(result=result, mainpbar=mainpbar)
            
            mainpbar.n = 100
            mainpbar.refresh()
            
            exitcode = 0 if result and result.returncode == 0 else 1
            exit(exitcode)
    except CalledProcessError as e:
        handleerror(e, lastcmdstr)
    except KeyboardInterrupt:
        error(f"{Fore.CYAN}user interrupted")
        exit(1)

def getloadingmessage(gitcommand: str, messages: Dict[str, str]) -> str:
    return messages.get(gitcommand, "processing...")

def runcmd(cmd: List[str], pbar) -> CompletedProcess:
    '''runs cmd'''
    cmdstr = list2cmdline(cmd)
    info("    running command:", pbar)
    printcmd(f"      $ {cmdstr}", pbar)
    cwd = getcwd()
    try:
        result: CompletedProcess = runsubprocess(cmd, check=True, cwd=cwd, capture_output=True)
        if result.stdout:
            outputstr: str = result.stdout.decode('utf-8', errors='replace').strip()
            if outputstr:
                info(f"    i {outputstr}", pbar)
        success("    ✓ completed successfully", pbar)
        return result
    except CalledProcessError as e:
        raise e

def handleerror(e: CalledProcessError, cmdstr: str) -> None:
    error(f"\n❌ command failed with exit code {e.returncode}:")
    printcmd(f"  $ {cmdstr}")
    if e.stdout:
        info(f"{e.stdout.decode('utf-8', errors='replace')}")
    if e.stderr:
        error(f"{e.stderr.decode('utf-8', errors='replace')}")
    exit(e.returncode)
