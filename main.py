import sys

args = sys.argv

'''
usage;
gpm
gpm "commit message"
gpm [-u | --upstream] [remote] [branch]
gpm "commit message" [remote] [branch]
'''

if args:
    commitmsg = args[0]
    args.pop(0)