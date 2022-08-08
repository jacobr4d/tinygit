# imports
from gitobject import *

from repo import *

from ref import *

import sys

import os

import argparse

import configparser

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# parser to parse command line arguments 

parser = argparse.ArgumentParser()
subs = parser.add_subparsers(title="commands", dest="command", required=True)

sp = subs.add_parser("init", help="Initialize a new, empty repository.")
sp.add_argument("path", metavar="directory", nargs="?", default=".", help="Where to create the repository.")

sp = subs.add_parser("commit", help="Commit the working tree.")
sp.add_argument("message", help="Commit message.")

sp = subs.add_parser("cat-file", help="Provide content of repository objects")
sp.add_argument("type", metavar="type", choices=["blob", "commit", "tag", "tree"], help="Specify the type")
sp.add_argument("object", metavar="object", help="The object to display")

sp = subs.add_parser("log", help="Display history of a given commit.")
sp.add_argument("commit", help="Commit to start at.")

sp = subs.add_parser("ls-tree", help="Pretty-print a tree object.")
sp.add_argument("object", help="The object to show.")

sp = subs.add_parser("checkout", help="Checkout a commit inside of a directory.")
sp.add_argument("commit", help="The commit or tree to checkout.")
sp.add_argument("path", help="The EMPTY directory to checkout on.")

sp = subs.add_parser("show-ref", help="List references.")

sp = subs.add_parser("tag", help="List and create tags")
# sp.add_argument("-a", action="store_true", dest="create_tag_object", help="Whether to create a tag object")
sp.add_argument("name", help="The new tag's name")
sp.add_argument("object", nargs="?", help="The object the new tag will point to")

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

# init empty git repo at some directory
def cmd_init(args):
  """args.path must either not exist or be empty"""
  workdir = args.path

  if not os.path.exists(workdir): os.makedirs(workdir)
  else:
    if not os.path.isdir(workdir): raise Exception("workdir is not a directory")
    elif os.listdir(workdir): raise Exception("workdir is not empty")
      
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


# print contents of file to stdout
def cmd_cat_file(args):
  obj = object_read(args.object)
  sys.stdout.buffer.write(obj.serialize())


# hash object and optionally write to db
def cmd_hash_object(args):
  with open(args.file, "rb") as f:
    data = f.read()
    if   args.type == 'blob'   : c = GitBlob
    elif args.type == 'commit' : c = GitCommit
    elif args.type == 'tag'    : c = GitTag
    elif args.type == 'tree'   : c = GitTree
    else: raise Exception("Unknown type")
    obj = c(data)

  if args.write:
    object_write(obj)

  print(object_hash(obj))

def cmd_commit(args):
  print("commiting")
  # make a list of all dirs in BFS order
  dirs = [repo_find().workdir]
  frontier = [repo_find().workdir]
  while frontier:
    cur = frontier.pop(0)    
    for child in os.scandir(cur):
      if child.is_dir() and child.name != ".git" :
        frontier.append(child.path)
        dirs.append(child.path)

  # add blob and tree objects
  dirs.reverse()
  treehashes = {}
  tree = None
  for cur in dirs:
    tree = GitTree()
    tree.items = []
    for child in os.scandir(cur):
      if child.is_dir() and child.name != ".git":
        tree.items.append((child.name, treehashes[child.path]))
      elif not child.is_dir():
        with open(child.path, "rb") as f:
          sha = object_write(GitBlob(f.read()))
          tree.items.append((child.name, sha))
    treehashes[cur] = object_write(tree)

  # create and store commit object
  commit = GitCommit()
  commit.headers = {}
  commit.headers["tree"] = object_hash(tree)
  commit.headers["author"] = "Jake Glenn <jbradleyglenn@gmail.com> 1659942309 -0400"
  commit.body = args.message + "\n"

  # update branch we are on
  with open (repo_file("HEAD"), "r") as f:
    data = f.read()[:-1] # drop newline
    if data.startswith("ref: "): # we are on some branch
      # if there is a parent, put it in commit
      if ref_resolve(data[5:]):
          commit.headers["parent"] = ref_resolve(data[5:])
      # update head ref to this new commit
      with open (repo_file(data[5:]), "w") as f1:
        newhash = object_write(commit)
        f1.write(newhash + "\n")
        print(newhash)

def cmd_show_ref(args):
  for k, v in ref_list().items():
    if v: print("{} {}".format(v, k))

def cmd_tag(args):
  if os.path.exists(repo_file("refs/tags/" + args.name)):
    print("tag %s already exists" % args.name)
  else: 
    with open(repo_file("refs/tags/" + args.name), "w") as f:
      if args.object: f.write(args.object + "\n")
      else: f.write(ref_resolve("HEAD") + "\n")

def cmd_log(args):
  commit = object_read(args.commit)
  while commit:
    print(bcolors.HEADER + "commit " + object_hash(commit) + bcolors.ENDC)
    sys.stdout.buffer.write(commit.serialize())
    print()
    if "parent" in commit.headers:
      commit = object_read(commit.headers["parent"])
    else:
      commit = None











