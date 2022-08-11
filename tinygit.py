# imports
from gitobject import *

from repo import *

from ref import *

import sys

import os

import argparse

import configparser

import shutil

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
sp.add_argument("workdir", metavar="directory", nargs="?", default=".", help="Where to create the repository.")

sp = subs.add_parser("status", help="Display status")

sp = subs.add_parser("commit", help="Commit the working tree.")
sp.add_argument("message", help="Commit message.")

sp = subs.add_parser("checkout", help="Checkout a commit using the working dir.")
sp.add_argument("commitish", help="The commit to checkout.")

sp = subs.add_parser("log", help="Display history of a given commit.")
sp.add_argument("commitish", nargs="?", default="HEAD", help="Commit to start at, defaults to HEAD.")

sp = subs.add_parser("tag", help="List and create tags")
sp.add_argument("name", help="The new tag's name")
sp.add_argument("objectish", nargs="?", help="The object the new tag will point to")

# plumbing commands
sp = subs.add_parser("hash-object", help="Compute object ID and optionally creates a blob from a file")
sp.add_argument("-t", metavar="type", dest="type", choices=["blob", "commit", "tag", "tree"], default="blob", help="Specify the type")
sp.add_argument("-w", dest="write", action="store_true", help="Actually write the object into the database")
sp.add_argument("file", help="Read object from <file>")

sp = subs.add_parser("cat-file", help="Provide content of repository objects")
sp.add_argument("type", metavar="type", choices=["blob", "commit", "tag", "tree"], help="Specify the type")
sp.add_argument("object", metavar="object", help="The object to display")

sp = subs.add_parser("show-ref", help="List references.")

sp = subs.add_parser("rev-parse", help="Parse revision (or other objects )identifiers")
sp.add_argument("--wyag-type", metavar="type", dest="type", choices=["blob", "commit", "tag", "tree"], default=None, help="Specify the expected type")
sp.add_argument("name", help="The name to parse")

sp = subs.add_parser("ls-tree", help="Pretty-print a tree object.")
sp.add_argument("object", help="The object to show.")



# commands
# init empty git repo at some directory
# the dir must not exist or be empty
def cmd_init(args):
  # make workdir
  workdir = os.path.abspath(args.workdir)
  if not os.path.exists(workdir): os.makedirs(workdir)
  if not os.path.isdir(workdir): raise Exception("workdir is not a directory")
  if os.listdir(workdir): raise Exception("workdir is not empty")
      
  # make gitdir
  os.makedirs(os.path.join(workdir, ".git", "branches"))
  os.makedirs(os.path.join(workdir, ".git", "objects"))
  os.makedirs(os.path.join(workdir, ".git", "refs", "tags"))
  os.makedirs(os.path.join(workdir, ".git", "refs", "heads"))
  with open(os.path.join(workdir, ".git", "description"), "w") as f:
    f.write("Unnamed repository; edit this file 'description' to name the repository.\n")
  with open(os.path.join(workdir, ".git", "HEAD"), "w") as f:
    f.write("refs/heads/master")
  with open(os.path.join(workdir, ".git", "config"), "w") as f:
    dconfig = configparser.ConfigParser()
    dconfig['core'] = {"repositoryformatversion": "0", "filemode": "false", "bare": "false"}
    dconfig.write(f)

  print(bcolors.WARNING + "hint: Using 'master' as the name for the initial branch." + bcolors.ENDC)
  print("Initialized empty TinyGit repository in " + os.path.join(workdir, ".git"))



# print status, based on HEAD
# 1. which branch HEAD is pointing to
# 2. or if detached, which commit HEAD is pointing to
def cmd_status(args):
  repo = repo_find()
  head = git_r(repo, "HEAD")
  if head.startswith("refs/heads"): 
    print("On branch " + head)
  else: 
    print("HEAD detached at " + head)



# pack workdir into commit object and store it
# advance HEAD
# 1. and branch ref if HEAD on a branch
# 2. solely if HEAD detached (not on a branch)
def cmd_commit(args):
  repo = repo_find()

  # make a list of all dirs in BFS order
  dirs = [repo.workdir]
  frontier = [repo.workdir]
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
          sha = object_write(repo, GitBlob(f.read()))
          tree.items.append((child.name, sha))
    treehashes[cur] = object_write(repo, tree)

  # create and store commit object
  commit = GitCommit()
  commit.headers = {}
  commit.headers["tree"] = object_hash(tree)
  commit.headers["author"] = "Jake Glenn <jbradleyglenn@gmail.com> 1659942309 -0400"
  commit.body = args.message + "\n"

  # update HEAD
  head = ref_read(repo, "HEAD")
  if head.startswith("refs/heads"):
    branch = head
    # if branch has commits, set parent
    if ref_read(repo, branch):
      commit.headers["parent"] = ref_read(repo, branch)
    ref_write(repo, branch, object_write(repo, commit))
  else:
    # detached HEAD state
    sha = head
    commit.headers["parent"] = sha
    ref_write(repo, "HEAD", object_write(repo, commit))



# unpack a commit in the workdir
# commitish resolves to one commit, or else ambiguity error
def cmd_checkout(args):
  repo = repo_find()

  # determine commit
  commitshas = commit_resolve(repo, args.commitish)
  if len(commitshas) > 1: raise Exception("commitish ambiguous")
  commit = object_read(repo, commitshas[1])

  # remove everything except .git folder
  pathworkdir = repo.workdir
  for entry in os.scandir(pathworkdir):
    if entry.name == ".git":
      pass
    elif entry.is_dir():
      shutil.rmtree(entry.path)
    elif entry.is_file():
      os.remove(entry.path)
  
  # unpack commit in workdir
  unpack_tree(repo, repo.workdir, object_read(repo, commit.headers["tree"]))

  # set HEAD to this commit, detached
  ref_write(repo, "HEAD", args.commit)
  print("You are in 'detached HEAD' state.")


# helper function for checkout
# unpack direct children of tree, in path path
def unpack_tree(repo, path, tree):
  for name, sha in tree.items:
    obj = object_read(repo, sha)
    if obj.kind == "blob":
      with open(os.path.join(path, name), "wb") as f:
        f.write(obj.blobbytes)
    elif obj.kind == "tree":
      os.mkdir(os.path.join(path, name))
      unpack_tree(repo, os.path.join(path, name), obj)


# log history of commitish
# or if none provided, of HEAD
def cmd_log(args):
  repo = repo_find()

  # determine commit
  commitshas = commit_resolve(repo, args.commitish)
  if len(commitshas) > 1: raise Exception("commitish ambiguous")

  if not commitsha[1]: #special case where HEAD -> refs/heads/master but no commits
    print("Your current branch does not have any commits yet")
  else:
    commit = object_read(repo, commitshas[1]) 
    while commit:
      print(bcolors.HEADER + "commit " + object_hash(commit) + bcolors.ENDC)
      sys.stdout.buffer.write(commit.serialize() + '\n'.encode())
      commit = object_read(repo, commit.headers["parent"]) if "parent" in commit.headers else None


def cmd_tag(args):
  repo = repo_find()
  if os.path.exists(repo_file(repo, "refs/tags/" + args.name)):
    print("tag %s already exists" % args.name)
  else: 
    with open(repo_file(repo, "refs/tags/" + args.name), "w") as f:
      if args.object: f.write(args.object + "\n")
      else: f.write(ref_resolve("HEAD") + "\n")


# plumbing commands
# print contents of file to stdout
def cmd_cat_file(args):
  repo = repo_find()
  obj = object_read(repo, args.object)
  sys.stdout.buffer.write(obj.serialize())


# hash object and optionally write to db
def cmd_hash_object(args): 
  repo = repo_find()
  with open(args.file, "rb") as f:
    data = f.read()
    if   args.type == 'blob'   : c = GitBlob
    elif args.type == 'commit' : c = GitCommit
    elif args.type == 'tag'    : c = GitTag
    elif args.type == 'tree'   : c = GitTree
    else: raise Exception("Unknown type")
    obj = c(data)

  if args.write:
    object_write(repo, obj)

  print(object_hash(obj))


def cmd_show_ref(args):
  repo = repo_find()
  for k, v in ref_list().items():
    if v: print("{} {}".format(v, k))


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
  elif args.command == "status"      : cmd_status(args)
  elif args.command == "tag"         : cmd_tag(args)










