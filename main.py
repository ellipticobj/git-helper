import os
import sys
import subprocess
from argparse import ArgumentParser
from typing import List

VERSION = "0.1.3"


def run(args: List[str], dry: bool = False) -> None:
    cwd = os.getcwd()
    if dry:
        print(subprocess.list2cmdline(args))
        return None

    try:
        print(f"running command: {subprocess.list2cmdline(args)} from {cwd} ...")
        subprocess.run(args, check=True, cwd=cwd)
        print(" done")
    except subprocess.CalledProcessError as e:
        print(
            f"error: command '{subprocess.list2cmdline(args)}' failed with exit code {e.returncode}."
        )
        sys.exit(e.returncode)


def main() -> None:
    parser = ArgumentParser(
        prog="meow",
        description="automatically stages, commits and pushes, with options",
    )

    parser.add_argument("message", nargs='?', help="commit message, overrides --no-message")
    parser.add_argument("-v", "--version", required=False, dest="ver", action='store_true', help="displays version number")
    parser.add_argument("-n", "--allow-empty-message", "--no-message", dest="nomsg", required=False, action='store_true', help="allows empty commit message, has to be provided if no message is given")
    parser.add_argument("-u", "--set-upstream", "--upstream", dest="upstream", required=False, help="upstream branch to push to")
    parser.add_argument("-d", "--dry-run", "--dry", dest="dry", required=False, action="store_true", help="prints out the commands that will be run without actually running them")
    parser.add_argument("-f", "--force", required=False, action='store_true', help="force push")
    parser.add_argument("-q", "--quiet", required=False, action='store_true', help="quiet")
    parser.add_argument("-ve", "--verbose", required=False, action='store_true', help="verbose")
    parser.add_argument("--allow-empty", dest="empty", required=False, action='store_true', help="allows empty commit")
    parser.add_argument("-np", "--no-push", action='store_true', required=False, dest="nopush", help="does not push")
    parser.add_argument("--pull", action="store_true", help="runs git pull before pushing before pushing")
    parser.add_argument("--pull-no-rebase", dest="norebase", action="store_true", help="runs git pull --no-rebase before pushing, overrides --pull")
    parser.add_argument("--update-submodules", action="store_true", help="update submodules recursively")

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()

    if args.ver:
        print(f"meow version {VERSION}\nhttps://github.com/ellipticobj/meower")
        sys.exit(1)

    if not args.nomsg and not args.message:
        parser.error("provide a commit message or use --no-message")
        sys.exit(0)

    if not args.message:
        parser.error("no commit message provided. use -h for detailed help")
        sys.exit(0)

    verbose = args.verbose and not args.quiet

    if args.update_submodules:
        run(["git", "submodule", "update", "--init", "--recursive"], args.dry)

    gpullc: List[str] = ["git", "pull"]
    gac: List[str] = ["git", "add", "."]
    gcc: List[str] = ["git", "commit"]
    gpc: List[str] = ["git", "push"]

    if args.message:
        msg = args.message
        gcc += ["-m", msg]

    if args.upstream:
        try:
            remote, branch = args.upstream.split("/", 1)
        except ValueError:
            parser.error("upstream must be in the format remote/branch")
        gpc += ["--set-upstream", remote, branch]

    if args.force:
        gpc.append("--force")

    if args.quiet:
        for i in [gpullc, gpc, gcc]:
            i.append("--quiet")
    elif verbose:
        for i in [gpullc, gpc, gcc, gac]:
            i.append("--verbose")

    if args.nomsg:
        gcc.append("--allow-empty-message")

    if args.empty:
        gcc.append("--allow-empty")

    if args.norebase:
        gpullc.append("--no-rebase")
        run(gpullc, args.dry)
    elif args.pull:
        run(gpullc, args.dry)

    for i in [gac, gcc]:
        run(i, args.dry)

    if not args.nopush:
        run(gpc, args.dry)
    else:
        print("not pushing...")

    if not args.dry:
        print("done")


if __name__ == "__main__":
    main()
