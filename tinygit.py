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
  dir_make(workdir, ".git", "branches")
  dir_make(workdir, ".git", "objects")
  dir_make(workdir, ".git", "refs", "tags")
  dir_make(workdir, ".git", "refs", "heads")
  file_write(workdir, ".git", "description", data="Unnamed repository; edit this file 'description' to name the repository.\n")
  file_write(workdir, ".git", "HEAD", data="refs/heads/master")
  with open(os.path.join(workdir, ".git", "config"), "w") as f:
    dconfig = configparser.ConfigParser()
    dconfig['core'] = {"repositoryformatversion": "0", "filemode": "false", "bare": "false"}
    dconfig.write(f)

  # print message
  print(bcolors.WARNING + "hint: Using 'master' as the name for the initial branch." + bcolors.ENDC)
  print("Initialized empty TinyGit repository in " + os.path.join(workdir, ".git"))



# print status, based on HEAD
# 1. which branch HEAD is pointing to
# 2. or if detached, which commit HEAD is pointing to
def cmd_status(args):
  repo = repo_find()
  head = file_read(repo.gitdir, "HEAD")
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

  # make a list of all dir paths in BFS discovery order
  # not exploring the git directory
  dirpaths = []
  for dirpath, dirnames, filenames in os.walk(repo.workdir):
    dirpaths.append(dirpath)
    if ".git" in dirnames: dirnames.remove(".git")

  # pack blob and tree objects bottom up
  dirpaths.reverse()
  treehashes = {}
  tree = None
  for dirpath in dirpaths:
    tree = GitTree()
    tree.items = []
    for child in os.scandir(dirpath):
      if child.is_dir() and child.name != ".git":
        tree.items.append((child.name, treehashes[child.path]))
      elif child.is_file():
        with open(child.path, "rb") as f:
          sha = object_write(GitBlob(f.read()), repo=repo)
          tree.items.append((child.name, sha))
    treehashes[dirpath] = object_write(tree, repo=repo)

  # pack commit object
  commit = GitCommit()
  commit.headers = {}
  commit.headers["tree"] = object_hash(tree)
  commit.headers["author"] = "Jake Glenn <jbradleyglenn@gmail.com> 1659942309 -0400"
  commit.body = args.message + "\n"

  # who is the parent commit?
  headcontents = file_read(repo.gitdir, "HEAD")
  reftoupdate = None
  if headcontents.startswith("refs/heads/"): # branch state
    if file_exists(repo.gitdir, headcontents): 
      commit.headers["parent"] = file_read(repo.gitdir, headcontents)
    reftoupdate = headcontents
  else: # detached HEAD state
    commit.headers["parent"] = headcontents
    reftoupdate = "HEAD"
  file_write(repo.gitdir, reftoupdate, data=object_write(commit, repo=repo))



# unpack a commit in the workdir
# commitish resolves to one commit, or else ambiguity error
def cmd_checkout(args):
  repo = repo_find()

  # determine commit
  commitshas = commit_resolve(args.commitish, repo=repo)
  if not commitshas:
    print("error: commitish '" + commitish + "' did not match any commit(s) known to tinygit")
    return
  if len(commitshas) > 1:
    print("error: commitish '" + commitish + "' is ambiguous:")
    print(commitshas)
    return
  commitsha = commitshas[0]
  commit = object_read(commitsha, repo=repo)

  # remove everything except .git folder
  for entry in dir_scan(repo.workdir):
    if entry.name == ".git":
      pass
    elif entry.is_dir():
      shutil.rmtree(entry.path)
    elif entry.is_file():
      os.remove(entry.path)
  
  # unpack commit in workdir
  unpack_tree(object_read(commit.headers["tree"], repo=repo), repo.workdir, repo=repo)

  # set HEAD to this commit, detached
  file_write(repo.gitdir, "HEAD", data=commitsha)
  print("You are in 'detached HEAD' state at " + commitsha)


# helper function for checkout
# unpack direct children of tree, in path path
def unpack_tree(tree, path, repo):
  for name, sha in tree.items:
    obj = object_read(sha, repo=repo)
    if obj.kind == "blob":
      with open(os.path.join(path, name), "wb") as f:
        f.write(obj.blobbytes)
    elif obj.kind == "tree":
      os.mkdir(os.path.join(path, name))
      unpack_tree(obj, os.path.join(path, name), repo)


# log history of commitish
# or if none provided, of HEAD
def cmd_log(args):
  repo = repo_find()

  # determine commit
  commitshas = commit_resolve(args.commitish, repo=repo)
  if not commitshas:
    print("error: commitish '" + args.commitish + "' did not match any commit(s) known to tinygit")
    return
  if len(commitshas) > 1:
    print("error: commitish '" + args.commitish + "' is ambiguous")
    print(commitshas)
    return
  commitsha = commitshas[0]

  if not commitsha: 
    print("Your current branch does not have any commits yet")
  else:
    commit = object_read(commitsha, repo=repo) 
    while commit:
      print(bcolors.HEADER + "commit " + object_hash(commit) + bcolors.ENDC)
      sys.stdout.buffer.write(commit.serialize() + '\n'.encode())
      commit = object_read(commit.headers["parent"], repo=repo) if "parent" in commit.headers else None


def cmd_tag(args):
  repo = repo_find()
  name = args.name
  objectish = args.objectish

  objectsha = object_resolve(args.objectish, repo=repo)

  if not ref_is_name(name):
    print("invalid tag name")
  elif file_exists(repo.gitdir, "refs", "tags", name):
    print("tag %s already exists" % name) 
  elif not objectsha:
    print("error: objectish '" + objectish + "' did not match any object(s) known to tinygit")
  elif len(objectsha) > 1:
    print("error: objectish '" + objectish + "' is ambiguous")
  else:
    objectsha = objectsha[0]
    file_write(repo.gitdir, "refs", "tags", name, data=objectsha)


# plumbing commands
# print contents of file to stdout
def cmd_cat_file(args):
  repo = repo_find()
  obj = object_read(args.object, repo=repo)
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
    object_write(obj, repo=repo)

  print(object_hash(obj))


def cmd_show_ref(args):
  repo = repo_find()
  for k, v in ref_list(repo=repo).items():
    print("{} {}".format(v, k))


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










