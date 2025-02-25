import subprocess
from argparse import ArgumentParser
from typing import List

'''
usage;
gpm
gpm "commit message"
gpm [-u | --upstream] [remote] [branch]
gpm "commit message" [remote] [branch]
'''

parser = ArgumentParser(
    prog="automatic git comitter",
    description="helps to stages all changes, commits, and pushes, with args",
    epilog="made by luna :3"
)

parser.add_argument("message")
parser.add_argument("-u", "--upstream", required=False, default="origin/main")
parser.add_argument("-f", "--force", required=False, action='store_true')
parser.add_argument("-q", "--quiet", required=False, action='store_true')
parser.add_argument("-v", "--verbose", required=False, action='store_true')
parser.add_argument("-nomsg", "-n", "--allow-empty", "--no-message", required=False, action='store_true')

args = parser.parse_args()

gac: List[str] = ['git', 'add']
gcc: List[str] = ['git', 'commit']
gpc: List[str] = ['git', 'push']