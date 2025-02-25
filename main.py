import sys
import subprocess
from argparse import ArgumentParser
from typing import List

def run(args: List[str], verbose: bool) -> None:
    if verbose:
        print("running command:", " ".join(args))
    try:
        subprocess.run(args, check=True)
    except subprocess.CalledProcessError as e:
        print(f"error: command '{' '.join(args)}' failed with exit code {e.returncode}.")
        sys.exit(e.returncode)

def main() -> None:
    parser = ArgumentParser(
        prog="automatic git comitter",
        description="helps to stages all changes, commits, and pushes, with args",
        epilog="made by luna :3"
    )

    parser.add_argument("message", required=False, help="commit message")
    parser.add_argument("-u", "--upstream", required=False, help="upstream branch to push to")
    parser.add_argument("-f", "--force", required=False, action='store_true', help="force push")
    parser.add_argument("-q", "--quiet", required=False, action='store_true', help="quiet")
    parser.add_argument("-v", "--verbose", required=False, action='store_true', help="verbose")
    parser.add_argument("-n", "--allow-empty-message", "--no-message", dest="nomsg", required=False, action='store_true', help="allows empty commit message")
    parser.add_argument("--allow-empty", dest="empty", required=False, action='store_true', help="allows empty commit")

    args = parser.parse_args()

    if not args.message and not args.nomsg:
        parser.error("provide a commit message or use --allow-empty-message/-n")
        sys.exit(0)

    verbose = args.verbose and not args.quiet

    gac: List[str] = ['git', 'add']
    gcc: List[str] = ['git', 'commit']
    gpc: List[str] = ['git', 'push']

    if args.message:
        gcc += ['-m', args.message]

    if args.upstream:
        try:
            remote, branch = args.upstream.split('/', 1)
        except ValueError:
            parser.error("upstream must be in the format remote/branch")
        gpc += ['--set-upstream', remote, branch]

    if args.force:
        gpc.append('--force')

    if args.quiet:
        gpc.append('--quiet')
        gcc.append('--quiet')
    elif verbose:
        gpc.append('--verbose')
        gcc.append('--verbose')
        gac.append('--verbose')

    if args.nomsg:
        gcc.append('--allow-empty-message')

    if args.empty:
        gcc.append('--allow-empty')

    run(gac, verbose)
    run(gcc, verbose)
    run(gpc, verbose)

    print("done")

if __name__ == "__main__":
    main()