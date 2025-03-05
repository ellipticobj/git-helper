from sys import exit
from os import getcwd
from tqdm import tqdm # type: ignore
from argparse import Namespace
from colorama import Fore, Style # type: ignore
from typing import List, Optional
from subprocess import run as runsubprocess, CompletedProcess, CalledProcessError

from utils.helpers import suggestfix, list2cmdline
from utils.loggers import error, info, printcmd, printoutput, success
from utils.loaders import startloadinganimation, stoploadinganimation

def runcmd(
    cmd: List[str],
    flags: Optional[Namespace] = None,
    pbar: Optional[tqdm] = None,
    withprogress: bool = True,
    captureoutput: bool = True,
    printsuccess: bool = True,
    isinteractive: Optional[bool] = None
) -> Optional[CompletedProcess]:
    '''
    executes a command
    
    cmd: command to execute
    flags: optional flags controlling execution
    pbar: optional progress bar
    withprogress: show progress animation
    captureoutput: capture command output
    printsuccess: print success message
    isinteractive: interactive mode
    '''
    # default flags
    flags = flags or Namespace(dry= False, cont = False, verbose = False)

    if not cmd:
        return None

    # print command for dry run
    if flags.dry:
        printcmd(list2cmdline(cmd), pbar)
        return None

    try:
        info("    running command:", pbar)
        printcmd(f"      $ {list2cmdline(cmd)}", pbar)

        interactive = isinteractive or (
            len(cmd) >= 2 and cmd[0] == "git" and cmd[1] == "commit" and len(cmd) == 2
        )

        if interactive:
            result = runsubprocess(
                cmd, 
                check=True, 
                cwd=getcwd(), 
                capture_output=False
            )
            return result

        # progressbar and loading animation
        if withprogress:
            with tqdm(
                total=100,
                desc=f"{Fore.CYAN}mrrping...{Style.RESET_ALL}",
                bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt}',
                position=1,
                leave=False
            ) as innerpbar:
                innerpbar.update(10)
                animation = startloadinganimation("running...")
                
                result = runsubprocess(
                    cmd, 
                    check=True, 
                    cwd=getcwd(), 
                    capture_output=captureoutput
                )
                
                innerpbar.n = 50
                innerpbar.refresh()
                stoploadinganimation(animation)
                
                if result:
                    printoutput(result, flags, innerpbar, pbar)
                
                innerpbar.n = 100
                innerpbar.colour = 'green'
                innerpbar.refresh()
                
                if printsuccess:
                    success("    ✓ completed successfully", pbar=innerpbar)
                
                return result
        
        # standard execution
        result = runsubprocess(
            cmd, 
            check=True, 
            cwd=getcwd(), 
            capture_output=captureoutput
        )
        
        if result:
            printoutput(result, flags, pbar, pbar)
        
        if printsuccess:
            success("    ✓ completed successfully", pbar=pbar)
        
        return result

    except CalledProcessError as e:
        # error handling
        error(f"\n❌ command failed with exit code {e.returncode}:", pbar)
        printcmd(f"  $ {list2cmdline(cmd)}", pbar)
        
        outstr = e.stdout.decode('utf-8', errors='replace') if e.stdout else ""
        errstr = e.stderr.decode('utf-8', errors='replace') if e.stderr else ""
        
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