# imports
import sys

import os

import argparse

import configparser

# parser to parse command line arguments 

parser = argparse.ArgumentParser()
subs = parser.add_subparsers(title="commands", dest="command", required=True)

sp = subs.add_parser("init", help="Initialize a new, empty repository.")
sp.add_argument("path", metavar="directory", nargs="?", default=".", help="Where to create the repository.")

sp = subs.add_parser("cat-file", help="Provide content of repository objects")
sp.add_argument("type", metavar="type", choices=["blob", "commit", "tag", "tree"], help="Specify the type")
sp.add_argument("object", metavar="object", help="The object to display")

sp = subs.add_parser("log", help="Display history of a given commit.")
sp.add_argument("commit", default="HEAD", nargs="?", help="Commit to start at.")

sp = subs.add_parser("ls-tree", help="Pretty-print a tree object.")
sp.add_argument("object", help="The object to show.")

sp = subs.add_parser("checkout", help="Checkout a commit inside of a directory.")
sp.add_argument("commit", help="The commit or tree to checkout.")
sp.add_argument("path", help="The EMPTY directory to checkout on.")

sp = subs.add_parser("show-ref", help="List references.")

sp = subs.add_parser("tag", help="List and create tags")
sp.add_argument("-a", action="store_true", dest="create_tag_object", help="Whether to create a tag object")
sp.add_argument("name", nargs="?", help="The new tag's name")
sp.add_argument("object", default="HEAD", nargs="?", help="The object the new tag will point to")

sp = subs.add_parser("rev-parse", help="Parse revision (or other objects )identifiers")
sp.add_argument("--wyag-type", metavar="type", dest="type", choices=["blob", "commit", "tag", "tree"], default=None, help="Specify the expected type")
sp.add_argument("name", help="The name to parse")

sp = subs.add_parser("hash-object", help="Compute object ID and optionally creates a blob from a file")
sp.add_argument("-t", metavar="type", dest="type", choices=["blob", "commit", "tag", "tree"], default="blob", help="Specify the type")
sp.add_argument("-w", dest="write", action="store_true", help="Actually write the object into the database")
sp.add_argument("file", help="Read object from <file>")

# main entry point

def main():
  args = parser.parse_args(sys.argv[1:])  
  if   args.command == "add"         : cmd_add(args)
  elif args.command == "cat-file"    : cmd_cat_file(args)
  elif args.command == "checkout"    : cmd_checkout(args)
  elif args.command == "commit"      : cmd_commit(args)
  elif args.command == "hash-object" : cmd_hash_object(args)
  elif args.command == "init"        : cmd_init(args)
  elif args.command == "log"         : cmd_log(args)
  elif args.command == "ls-tree"     : cmd_ls_tree(args)
  elif args.command == "merge"       : cmd_merge(args)
  elif args.command == "rebase"      : cmd_rebase(args)
  elif args.command == "rev-parse"   : cmd_rev_parse(args)
  elif args.command == "rm"          : cmd_rm(args)
  elif args.command == "show-ref"    : cmd_show_ref(args)
  elif args.command == "tag"         : cmd_tag(args)

# commands

def cmd_init(args):
  """args.path must either not exist or be empty"""
  workdir = args.path

  if not os.path.exists(workdir):
    os.makedirs(workdir)
  else:
    if not os.path.isdir(workdir):
      raise Exception("workdir is not a directory")
    elif os.listdir(workdir):
      raise Exception("workdir is not empty")
      
  os.makedirs(os.path.join(workdir, ".git", "branches"))
  os.makedirs(os.path.join(workdir, ".git", "objects"))
  os.makedirs(os.path.join(workdir, ".git", "refs", "tags"))
  os.makedirs(os.path.join(workdir, ".git", "refs", "heads"))

  with open(os.path.join(workdir, ".git", "description"), "w") as f:
    f.write("Unnamed repository; edit this file 'description' to name the repository.\n")

  with open(os.path.join(workdir, ".git", "HEAD"), "w") as f:
    f.write("ref: refs/heads/master\n")

  with open(os.path.join(workdir, ".git", "config"), "w") as f:
    dconfig = configparser.ConfigParser()
    dconfig['core'] = {"repositoryformatversion": "0", "filemode": "false", "bare": "false"}
    dconfig.write(f)


def cmd_cat_file(args):
  repo = repo_find()  
  obj = object_read(repo, args.object)
  sys.stdout.buffer.write(obj.serialize())

def cmd_hash_object(args):
  repo = find_repo()
  with open(args.path, "rb") as f:
    data = f.read()
    if   args.type == 'blob'   : c = GitBlob
    elif args.type == 'commit' : c = GitCommit
    elif args.type == 'tag'    : c = GitTag
    elif args.type == 'tree'   : c = GitTree
    else: raise Exception("Unknown type")
    obj = c(repo, data)

  if args.write:
    object_write(repo, obj)

  print(hash_object(obj))
















