from sys import stdout
from time import sleep, time
from colorama import Fore, Style
from threading import Event, Thread

'''
loading animations
'''

def loadingthread(message: str, stopevent: Event) -> None:
    '''animated loading icon function to run in a thread'''
    frames = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
    i = 0
    message = f"{Fore.CYAN}{message}{Style.RESET_ALL}"
    
    while not stopevent.is_set():
        stdout.write(f'\r{frames[i]} {message}')
        stdout.flush()
        sleep(0.1)
        i = (i + 1) % len(frames)
    
    # clear the line
    stdout.write(f'\r {len(message)*2}\r')
    stdout.flush()

def startloading(message: str) -> tuple[Thread, Event]:
    '''start loading animation in a thread'''
    stop = Event()
    anithread = Thread(
        target=loadingthread,
        args=(message, stop),
        daemon=True
    )
    anithread.start()
    return anithread, stop

def stoploading(threadinfo: tuple[Thread, Event]) -> None:
    '''stop threaded loading animation'''
    thread, event = threadinfo
    event.set()
    thread.join(timeout=0.2)  # wait for the thread to finish!!!!

def unthreadedloading(message: str, duration: float = 2.0) -> None:
    '''unthreaded loading animation'''
    frames = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
    i = 0
    message = f"{Fore.CYAN}{message}{Style.RESET_ALL}"
    endtime = time() + duration
    
    while time() < endtime:
        stdout.write(f'\r{frames[i]} {message}')
        stdout.flush()
        sleep(0.1)
        i = (i + 1) % len(frames)
    
    # clear the line
    stdout.write(f'\r {len(message)*2}\r')
    stdout.flush()