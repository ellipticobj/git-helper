from time import time
from tqdm import tqdm # type: ignore
from argparse import Namespace
from collections.abc import Callable
from typing import List, Optional, Dict, Union, Any

from core.executor import runcmd # type: ignore

from utils.loggers import info, success # type: ignore

'''pipeline related functions'''

class PipelineStep:
    '''one step in the pipeline'''
    def __init__(
        self, 
        name: str, 
        func: Callable[[Namespace], Any], 
        noprogressbar: bool = False
    ):
        self.name = name
        self.func = func
        self.noprogressbar = noprogressbar

    def execute(
        self, 
        args: Namespace, 
        pbar: Optional[tqdm]
    ) -> tuple[dict[str, Union[object,Any]], Any]:
        '''executes thes tep'''
        start = time()
        toadd, cmd = self.func(args)

        result = runcmd(
            cmd=cmd,
            flags=args,
            pbar=pbar,
            withprogress=not self.noprogressbar
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
    def __init__(self, args: Namespace, steps: List[PipelineStep], pbar: tqdm):
        self.args = args
        self.steps = steps
        self.pbar = pbar
        self.report: List[Dict[str, Union[str, float]]] = []

    def run(self) -> None:
        '''runs all steps in the pipeline'''
        starttime = time()
        for step in self.steps:
            reportitem: Dict
            toadd: int
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

    def generatereport(self, saveto: Optional[str] = None, pbar: Optional[tqdm] = None) -> None:
        '''generates report and saves to saveto if saveto is provided'''
        output: List[str] = ["\report:\n"]
        for step in self.report:
            output.append(f"step: {step['step']}\n")
            output.append(f"  command: {step.get('command', 'N/A')}\n")
            output.append(f"  duration: {step['duration']:.8f} seconds\n")
            
            if step.get("output"):
                output.append(f"  output: {step['output']}\n")
            if step.get("returncode"):
                output.append(f"  return code: {step['returncode']}\n")
            output.append("\n")
        
        output.append(f"total duration: {self.report[-1]['duration']:.8f} seconds\n")

        if saveto:
            with open(saveto, 'w') as f:
                f.writelines(output)
            success(message=f"report saved to {saveto}", pbar=pbar)
        else:
            for line in output:
                info(line, pbar = pbar)