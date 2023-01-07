import sys
import argparse

from tinygit.commands import *


parser = argparse.ArgumentParser()
subs = parser.add_subparsers(title="commands", dest="command", required=True)

sp = subs.add_parser("init", help="Initialize a new, empty repository.")
sp.add_argument("location", metavar="location", nargs="?", default=".", help="Where to create the tinygit repository.")

sp = subs.add_parser("status", help="Display status")

sp = subs.add_parser("commit", help="Commit the working tree.")
sp.add_argument("message", help="Commit message.")

sp = subs.add_parser("checkout-commit", help="Checkout a commit using the working dir.")
sp.add_argument("commit", help="The commit to checkout.")

sp = subs.add_parser("checkout-branch", help="Checkout a branch using the working dir.")
sp.add_argument("branch", help="The branch to checkout.")

sp = subs.add_parser("branch", help="Make or list branches.")
sp.add_argument("branchname", nargs="?", default="", help="The new branch's name.")
sp.add_argument("-d", dest="branchtodelete")

sp = subs.add_parser("merge", help="Merge branches")
sp.add_argument("branchname", help="name of the branch to merge into this one.")

sp = subs.add_parser("log", help="Display history of a given commit.")
sp.add_argument("commit", nargs="?", default="HEAD", help="Commit to start at, defaults to HEAD.")

sp = subs.add_parser("tag", help="List and create tags")
sp.add_argument("name", help="The new tag's name.")
sp.add_argument("object", nargs="?", default="HEAD", help="The object the new tag will point to.")

sp = subs.add_parser("hash-object", help="Compute object ID and optionally creates a blob from a file")
sp.add_argument("-t", metavar="type", dest="type", choices=["blob", "commit", "tag", "tree"], default="blob", help="Specify the type")
sp.add_argument("-w", dest="write", action="store_true", help="Actually write the object into the database")
sp.add_argument("file", help="Read object from <file>")

sp = subs.add_parser("cat-file", help="Provide content of repository objects")
sp.add_argument("object", metavar="object", help="The object to display")

sp = subs.add_parser("show-ref", help="List references.")

sp = subs.add_parser("rev-parse", help="Parse revision (or other objects )identifiers")
sp.add_argument("--wyag-type", metavar="type", dest="type", choices=["blob", "commit", "tag", "tree"], default=None, help="Specify the expected type")
sp.add_argument("name", help="The name to parse")

sp = subs.add_parser("ls-tree", help="Pretty-print a tree object.")
sp.add_argument("object", help="The object to show.")

# main entry point for CLI application
def main():
  args = parser.parse_args(sys.argv[1:])  
  if   args.command == "add"              : cmd_add(args)
  elif args.command == "branch"           : cmd_branch(args)
  elif args.command == "cat-file"         : cmd_cat_file(args)
  elif args.command == "checkout-commit"  : cmd_checkout_commit(args)
  elif args.command == "checkout-branch"  : cmd_checkout_branch(args)
  elif args.command == "commit"           : cmd_commit(args)
  elif args.command == "hash-object"      : cmd_hash_object(args)
  elif args.command == "init"             : cmd_init(args)
  elif args.command == "log"              : cmd_log(args)
  elif args.command == "ls-tree"          : cmd_ls_tree(args)
  elif args.command == "merge"            : cmd_merge(args)
  elif args.command == "rev-parse"        : cmd_rev_parse(args)
  elif args.command == "rm"               : cmd_rm(args)
  elif args.command == "show-ref"         : cmd_show_ref(args)
  elif args.command == "status"           : cmd_status(args)
  elif args.command == "tag"              : cmd_tag(args)

if __name__ == '__main__':
  sys.exit(main())
