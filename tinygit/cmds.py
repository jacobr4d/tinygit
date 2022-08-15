import sys
import os
import configparser
import shutil

from tinygit.fsutils import *
from tinygit.gitobjects import *
from tinygit.ref import *
from tinygit.repo import *

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
  commit.headers["tree"] = tree.object_hash()
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
      print(bcolors.HEADER + "commit " + commit.object_hash() + bcolors.ENDC)
      sys.stdout.buffer.write(commit.serialize() + '\n'.encode())
      commit = object_read(commit.headers["parent"], repo=repo) if "parent" in commit.headers else None


def cmd_tag(args):
  name = args.name
  objectish = args.objectish

  repo = repo_find()

  objectsha = object_resolve(objectish, repo=repo)

  if not ref_is_name(name):
    print("error: tag name {name} is invalid")
    return
  if file_exists(repo.gitdir, "refs", "tags", name):
    print("error: tag {name} already exists") 
    return
  if not objectsha:
    print("error: objectish '{objectish}' did not match any object(s) known to tinygit")
    return
  if len(objectsha) > 1:
    print("objectish '{objectish}}' is ambiguous")
    return
  
  file_write(repo.gitdir, "refs", "tags", name, data=objectsha[0])


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









