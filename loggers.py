from sys import exit
from tqdm import tqdm
from argparse import Namespace
from colorama import Fore, Style
from subprocess import CompletedProcess
from typing import Optional, List, NoReturn

'''
things that log
'''

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

def printinfo(version: str) -> NoReturn:
    '''print program info'''
    print(f"{Fore.MAGENTA}{Style.BRIGHT}meow{Style.RESET_ALL} version {Fore.CYAN}{version}{Style.RESET_ALL}")
    print(f"{Fore.BLUE}https://github.com/ellipticobj/meower{Style.RESET_ALL}")
    exit(1)

def printsteps(steps: List[str]) -> None:
    '''prints pipeline steps'''
    for i, step in enumerate(steps, 1): 
        print(f"  {Fore.BLUE}{i}.{Style.RESET_ALL} {Fore.BLACK}{step}{Style.RESET_ALL}")
    print()

def printoutput(
        result: CompletedProcess[bytes], 
        flags: Namespace, 
        pbar: tqdm, 
        mainpbar: Optional[tqdm]
        ) -> None:
    '''prints commands output'''
    outputstr: str = result.stdout.decode('utf-8', errors='replace').strip()
    pbar.n = 80
    pbar.refresh()
    if outputstr:
        if flags.verbose:
            # output everything
            info(f"    i {Fore.CYAN}{outputstr}", mainpbar)
        else:
            # check for specific outputs
            if 'Everything up-to-date' in outputstr:
                info(f"    i {Fore.CYAN}everything up-to-date", mainpbar)
            elif 'nothing to commit' in outputstr:
                info(f"    i {Fore.CYAN}nothing to commit", mainpbar)
            elif 'create mode' in outputstr or 'delete mode' in outputstr:
                # show additions/deletions
                outputl: List[str] = outputstr.split('\n')
                for line in outputl: # make sure everything is indented properly
                    info(f"    i {Fore.BLACK}{line}", mainpbar)
            elif len(outputstr) < 200:  # show short messages
                if flags.message in outputstr: # dont duplicate commit message
                    pass
                else:
                    info(f"    i {Fore.BLACK}{outputstr}", mainpbar)

def formatcommit(
        commit_hash: str, 
        author: str, 
        date: str, 
        message: str
        ) -> str:
    '''formats commit for output'''
    return f"""
    {Fore.YELLOW}commit {commit_hash}{Style.RESET_ALL}
    author: {Fore.CYAN}{author}{Style.RESET_ALL}
    date:   {date}

        {Fore.GREEN}{message}{Style.RESET_ALL}
    """

def showcommitresult(
        result: CompletedProcess[bytes], 
        mainpbar: Optional[tqdm]
        ) -> None:
    '''displays formatted commit'''
    if result.returncode == 0:
        parts = result.stdout.decode().split('|')
        if len(parts) == 4:
            info(formatcommit(
                commit_hash=parts[0][:7],
                author=parts[1],
                date=parts[2],
                message=parts[3]
            ), mainpbar)