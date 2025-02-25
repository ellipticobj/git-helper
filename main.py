import sys
import subprocess
from argparse import ArgumentParser
from typing import List

def run(args: List[str], verbose: bool, dry: bool=False) -> None:
    if dry:
        print(subprocess.list2cmdline(args))
        return None
    
    if verbose:
        print(f"running command: {subprocess.list2cmdline(args)}")
    try:
        subprocess.run(args, check=True)
    except subprocess.CalledProcessError as e:
        print(f"error: command '{subprocess.list2cmdline(args)}' failed with exit code {e.returncode}.")
        sys.exit(e.returncode)

def main() -> None:
    parser = ArgumentParser(
        prog="meower",
        description="helps to stages all changes, commits, and pushes, with args",
        epilog="made by luna :3"
    )

    parser.add_argument("message", nargs='?', help="commit message")
    parser.add_argument("-u", "--upstream", required=False, help="upstream branch to push to")
    parser.add_argument("-d", "--dry-run", "--dry", dest="dry", required=False, action="store_true", help="prints out the commands that will be run without actually running them")
    parser.add_argument("-f", "--force", required=False, action='store_true', help="force push")
    parser.add_argument("-q", "--quiet", required=False, action='store_true', help="quiet")
    parser.add_argument("-v", "--verbose", required=False, action='store_true', help="verbose")
    parser.add_argument("-n", "--allow-empty-message", "--no-message", dest="nomsg", required=False, action='store_true', help="allows empty commit message")
    parser.add_argument("--allow-empty", dest="empty", required=False, action='store_true', help="allows empty commit")
    parser.add_argument("--pull", action="store_true", help="runs git pull before pushing before pushing")
    parser.add_argument("--pull-no-rebase", dest="norebase", action="store_true", help="runs git pull --no-rebase before pushing")
    parser.add_argument("--update-submodules", action="store_true", help="update submodules recursively")

    args = parser.parse_args()

    if not args.nomsg and not args.message:
        parser.error("provide a commit message or use --no-message")
        sys.exit(0)

    if not args.message:
        parser.error("no commit message provided. use -h for detailed help")
        sys.exit(0)
    
    verbose = args.verbose and not args.quiet


    if args.update_submodules:
        run(['git', 'submodule', 'update', '--init', '--recursive'], verbose, args.dry)

    gpullc: List[str] = ['git', 'pull']
    gac: List[str] = ['git', 'add', '.']
    gcc: List[str] = ['git', 'commit']
    gpc: List[str] = ['git', 'push']

    if args.message:
        msg = args.message
        # msg = msg.replace('"', '\"')
        # msg = msg.replace('!', '\!')
        gcc += ['-m', msg]

    if args.upstream:
        try:
            remote, branch = args.upstream.split('/', 1)
        except ValueError:
            parser.error("upstream must be in the format remote/branch")
        gpc += ['--set-upstream', remote, branch]

    if args.force:
        gpc.append('--force')

    if args.quiet:
        for i in [gpullc, gpc, gcc]:
            i.append('--quiet')
    elif verbose:
        for i in [gpullc, gpc, gcc, gac]:
            i.append('--verbose')

    if args.nomsg:
        gcc.append('--allow-empty-message')

    if args.empty:
        gcc.append('--allow-empty')

    if args.norebase:
        gpullc.append('--no-rebase')
        run(gpullc, verbose, args.dry)
    elif args.pull:
        run(gpullc, verbose, args.dry)

    for i in [gac, gcc, gpc]:
        run(i, verbose, args.dry)

    if not args.dry:
        print("done")

if __name__ == "__main__":
    main()