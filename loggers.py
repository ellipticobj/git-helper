from sys import exit
from tqdm import tqdm
from argparse import Namespace
from colorama import Fore, Style
from typing import Optional, List, NoReturn
from subprocess import list2cmdline, CompletedProcess

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
        pbar.write(f"{Fore.MAGENTA}{Style.BRIGHT}{message}")
    else:
        print(f"{Fore.MAGENTA}{Style.BRIGHT}{message}")

def info(message: str, pbar: Optional[tqdm] = None) -> None:
    '''print info message'''
    if pbar:
        pbar.write(f"{Fore.BLUE}{message}")
    else:
        print(f"{Fore.BLUE}{message}")

def warning(message: str, pbar: Optional[tqdm] = None) -> None:
    '''print warning message'''
    if pbar:
        pbar.write(f"{Fore.YELLOW}{Style.DIM}{message}")
    else:
        print(f"{Fore.YELLOW}{Style.DIM}{message}")

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

def printdiff(outputstr: str, pbar: Optional[tqdm]) -> None:
    additions = 0
    deletions = 0
    files = []
    
    # process git output
    for line in outputstr.split('\n'):
        if not line:
            continue
        parts = line.split('\t')
        if len(parts) >= 3:
            add = int(parts[0]) if parts[0].isdigit() else 0
            rem = int(parts[1]) if parts[1].isdigit() else 0
            fname = parts[2]
            files.append((fname, add, rem))
            additions += add
            deletions += rem
    
    # print formatted text
    for fname, add, rem in files:
        info(f"    {Style.BRIGHT}{fname}{Style.RESET_ALL}", pbar=pbar)
        if add > 0:
            info(f"      {Fore.GREEN}+++ {add} additions{Style.RESET_ALL}", pbar=pbar)
        if rem > 0:
            info(f"      {Fore.RED}--- {rem} deletions{Style.RESET_ALL}", pbar=pbar)

    # print summary
    info(f"\n    {Fore.CYAN}total: {len(files)} files changed", pbar=pbar)
    info(f"    {Fore.GREEN}{additions} insertions(+){Style.RESET_ALL}", pbar=pbar)
    info(f"    {Fore.RED}{deletions} deletions(-){Style.RESET_ALL}", pbar=pbar)

def printoutput(
        result: CompletedProcess[bytes], 
        flags: Namespace, 
        pbar: Optional[tqdm], 
        mainpbar: Optional[tqdm]
        ) -> None:
    '''prints commands output'''
    outputstr: str = result.stdout.decode('utf-8', errors='replace').strip()

    if 'diff' in list2cmdline(result.args):
        printdiff(outputstr=outputstr, pbar=pbar)
        return
    
    if pbar:
        pbar.n = 80
        pbar.refresh()

    if outputstr:
        if flags.verbose:
            # output everything
            info(f"    i {Fore.CYAN}{outputstr}", mainpbar)
        else:
            messagestr = " ".join(flags.message) if isinstance(flags.message, list) else flags.message
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
                if messagestr in outputstr: # dont duplicate commit message
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
    return (
        f"\n      {Fore.YELLOW}commit {commit_hash}{Style.RESET_ALL}\n"
        f"      author: {Fore.CYAN}{author}{Style.RESET_ALL}\n"
        f"      date:   {date}\n"
        f"      message:\n        {Fore.GREEN}{message}{Style.RESET_ALL}"
    )

def showcommitresult(
        result: CompletedProcess[bytes], 
        mainpbar: Optional[tqdm] = None
        ) -> None:
    '''displays formatted commit'''
    if result.returncode != 0:
        return

    try:
        output = result.stdout.decode()
        if '|' in output:
            parts = output.split('|')
            if len(parts) == 4:
                info(formatcommit(
                    commit_hash=parts[0][:7],
                    author=parts[1],
                    date=parts[2],
                    message=parts[3]
                ), mainpbar)
        else:
            info(f"      i {Fore.CYAN}{output}", mainpbar)
    except Exception as e:
        error(f"error showing commit: {str(e)}", mainpbar)

def showresult(
        result: CompletedProcess[bytes],
        mainpbar: Optional[tqdm] = None
        ) -> None:
    '''displays normal results'''
    if result.returncode == 0:
        for line in result.stdout.decode().split("\n"):
            info(f"    i {Fore.CYAN}{line}", mainpbar)

def spacer(pbar: Optional[tqdm] = None, height: int = 1) -> str:
    for i in range(height):
        info(message="", pbar=pbar)

    return "\n" * height