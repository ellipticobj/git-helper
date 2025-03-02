from sys import exit
from tqdm import tqdm
from colorama import Fore, Style
from typing import Optional, List, TypeAlias, NoReturn

'''
things that log
'''

ProgressBar: TypeAlias = tqdm
FormatString: TypeAlias = str

def success(message: str, pbar: Optional[ProgressBar] = None) -> None:
    '''print success message'''
    if pbar:
        pbar.write(f"{Fore.GREEN}{Style.BRIGHT}{message}")
    else:
        print(f"{Fore.GREEN}{Style.BRIGHT}{message}")

def error(message: str, pbar: Optional[ProgressBar] = None) -> None:
    '''print error message'''
    if pbar:
        pbar.write(f"{Fore.RED}{Style.BRIGHT}{message}")
    else:
        print(f"{Fore.RED}{Style.BRIGHT}{message}")

def info(message: str, pbar: Optional[ProgressBar] = None) -> None:
    '''print info message'''
    if pbar:
        pbar.write(f"{Fore.BLUE}{message}")
    else:
        print(f"{Fore.BLUE}{message}")

def warning(message: str, pbar: Optional[ProgressBar] = None) -> None:
    '''print warning message'''
    if pbar:
        pbar.write(f"{Fore.YELLOW}{Style.BRIGHT}{message}")
    else:
        print(f"{Fore.YELLOW}{Style.BRIGHT}{message}")

def printcmd(cmd: str, pbar: Optional[ProgressBar] = None) -> None:
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