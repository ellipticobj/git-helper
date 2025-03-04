from typing import List, Optional, Tuple, Dict, Union
from time import time
from tqdm import tqdm # type: ignore
from collections.abc import Callable
from core.executor import runcmd
from utils.loggers import info, success

'''pipeline related functions'''

class PipelineStep:
    '''one step in the pipeline'''
    def __init__(
        self, 
        name: str, 
        func: Callable[[Dict, Optional[tqdm]], Tuple[int, List[str]]], 
        noprogressbar: bool = False
    ):
        self.name = name
        self.func = func
        self.noprogressbar = noprogressbar

    def execute(
        self, 
        args: Dict, 
        pbar: Optional[tqdm]
    ) -> Tuple[Dict[str, Union[str, float, int]], int]:
        '''executes thes tep'''
        start = time()
        toadd, cmd = self.func(args, pbar=pbar)

        result = runcmd(
            cmd=cmd,
            flags=args,
            pbar=pbar,
            with_progress=not self.noprogressbar
        )

        duration = time() - start
        report = {
            "step": self.name,
            "command": " ".join(cmd) if cmd else "",
            "duration": duration,
            "output": result.stdout.decode("utf-8", errors="replace") if result else "",
            "returncode": result.returncode if result else ""
        }
        return report, toadd


class Pipeline:
    def __init__(self, args: Dict, steps: List[PipelineStep], pbar: tqdm):
        self.args = args
        self.steps = steps
        self.pbar = pbar
        self.report: List[Dict[str, Union[str, float]]] = []

    def run(self) -> None:
        '''runs all steps in the pipeline'''
        starttime = time()
        for step in self.steps:
            reportitem, toadd = step.execute(self.args, self.pbar)
            
            # update bar
            self.pbar.update(toadd)
            self.report.append(reportitem)

        totaltime = time() - starttime
        self.report.append({"step": "TOTAL", "duration": totaltime})
        
        # complete bar
        self.pbar.n = self.pbar.total
        self.pbar.colour = 'green'
        self.pbar.refresh()

    def generatereport(self, saveto: Optional[str] = None) -> None:
        '''generates report and saves to saveto if saveto is provided'''
        output: List[str] = ["\nReport:\n"]
        for step in self.report:
            output.append(f"Step: {step['step']}\n")
            output.append(f"  Command: {step.get('command', 'N/A')}\n")
            output.append(f"  Duration: {step['duration']:.8f} seconds\n")
            
            if step.get("output"):
                output.append(f"  Output: {step['output']}\n")
            if step.get("returncode"):
                output.append(f"  Return Code: {step['returncode']}\n")
            output.append("\n")
        
        output.append(f"Total Duration: {self.report[-1]['duration']:.8f} seconds\n")

        if saveto:
            with open(saveto, 'w') as f:
                f.writelines(output)
            success(f"Report saved to {saveto}")
        else:
            for line in output:
                info(line)