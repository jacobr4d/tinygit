import sys
import os
import configparser
import shutil
from collections import defaultdict
from collections import Counter

from tinygit.fsutils import *
from tinygit.state import *

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


def cmd_branch(args):
  """tinygit branch command
  
  Used for listing branches, creating a branch, and deleting a branch
  """
  repo = repo_find()
  if args.branchtodelete != None:       # delete branch
    if args.branchtodelete not in {entry.name for entry in dir_scan(os.path.join(repo.gitdir, "refs", "heads"))}:
      print(f"branch '{args.branchtodelete}' not found")
      return
    os.remove(os.path.join(repo.gitdir, "refs", "heads", args.branchtodelete))
  elif args.branchname != "":           # create branch
    if args.branchname in {entry.name for entry in dir_scan(os.path.join(repo.gitdir, "refs", "heads"))}:
      print(f"a branch named '{args.branchname}' already exists")
      return
    file_write(repo.gitdir, "refs", "heads", args.branchname, data=repo.ref_resolve("HEAD"), mkdir=False, mode="w")
  else:                                 # list branches 
    for entry in dir_scan(os.path.join(repo.gitdir, "refs", "heads")):
      print(entry.name)


def files_dirs_to_create(commit, repo):
  # files to create (path, filesha, fileobj, commitsha)
  # dirs to create (path)
  files_to_create = []
  dirs_to_create = []
  commitsha = object_hash(commit)[:6]
  trees = [(repo.workdir, commit.state["headers"]["tree"])]
  while trees:
    path, treesha = trees.pop()
    tree = repo.object_read(treesha)
    for name, objsha in tree.items:
      obj = repo.object_read(objsha)
      if obj.kind == "blob":
        files_to_create.append((os.path.join(path, name), objsha, obj, commitsha))
      if obj.kind == "tree":
        dirs_to_create.append(os.path.join(path, name))
        trees.append((os.path.join(path, name), objsha))
  return files_to_create, dirs_to_create

def cmd_merge(args):
  """tinygit merge command
  
  Used for merging branches

  Merge isn't fancy like git. It is a UNION of files and directories where conflicts are BOTH present.
  First, directories in branch a or b or both will be created
  Next, files in branch a and b or be or both be created if there is only one version
  If files in branch a and b have the same name foo and different contents ie they CONFLICT, then foo.a and foo.b will be created
  """
  repo = repo_find()
  commit_a = repo.object_read(repo.commit_resolve("HEAD")[0])
  commit_b = repo.object_read(repo.commit_resolve(args.branchname)[0])
  files_a, dirs_a = files_dirs_to_create(commit_a, repo)
  files_b, dirs_b = files_dirs_to_create(commit_b, repo)

  dirs = set(dirs_a + dirs_b)

  pathsandshas = defaultdict(set)
  for path, sha, _, _ in files_a + files_b:
    pathsandshas[path].add(sha)
  conflicts = set(path for path, sha, _, _ in files_a if len(pathsandshas[path]) == 2)

  # empty workdir
  for entry in dir_scan(repo.workdir):
    if entry.name == ".git":
      pass
    elif entry.is_dir():
      shutil.rmtree(entry.path)
    elif entry.is_file():
      os.remove(entry.path)

  # build dirs
  for path in dirs:
    os.mkdir(path)

  # build files
  for path, objsha, obj, commitsha in files_a + files_b:
    file_write(path + "." + commitsha if path in conflicts else path, data=obj.blobbytes, mode="wb")


# init empty git repo at some directory
# the dir must not exist or be empty
def cmd_init(args):
  # make workdir
  workdir = os.path.abspath(args.workdir)
  if not os.path.exists(workdir): 
    os.makedirs(workdir)
  if not os.path.isdir(workdir): 
    print(f"Workdir '{workdir}' is not a directory")
    sys.exit(1)
  if ".git" in os.listdir(workdir):
    print(f"Workdir '{workdir}' already contains a tinygit repository")
    sys.exit(1)
      
  # make gitdir
  dir_make(workdir, ".git", "branches")
  dir_make(workdir, ".git", "objects")
  dir_make(workdir, ".git", "refs", "tags")
  dir_make(workdir, ".git", "refs", "heads")
  file_write(workdir, ".git", "description", data="Unnamed repository; edit this file 'description' to name the repository.\n")
  file_write(workdir, ".git", "HEAD", data="refs/heads/master")

  # print message
  print(f"{bcolors.WARNING}hint: Using 'master' as the name for the initial branch.{bcolors.ENDC}")
  print(f"Initialized empty TinyGit repository in {(os.path.join(workdir, '.git'))}")


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
          sha = repo.object_write(GitBlob(f.read()))
          tree.items.append((child.name, sha))
    treehashes[dirpath] = repo.object_write(tree)

  # pack commit object
  commit = GitCommit()
  commit.state = {"headers": {}, "body": ""}
  commit.state["headers"]["tree"] = object_hash(tree)
  commit.state["body"] = args.message

  # who is the parent commit?
  headcontents = file_read(repo.gitdir, "HEAD")
  reftoupdate = None
  if headcontents.startswith("refs/heads/"): # branch state
    if file_exists(repo.gitdir, headcontents): 
      commit.state["headers"]["parent"] = file_read(repo.gitdir, headcontents)
    reftoupdate = headcontents
  else: # detached HEAD state
    commit.state["headers"]["parent"] = headcontents
    reftoupdate = "HEAD"
  file_write(repo.gitdir, reftoupdate, data=repo.object_write(commit))


def cmd_checkout(args):
  """tinygit checkout command
  
  Used for checking out branches and commits

  HEAD changed and workdir updated
  """
  repo = repo_find()

  branchsha = repo.branch_resolve(args.commitish)
  if branchsha:         
    # move HEAD
    file_write(repo.gitdir, "HEAD", data="refs/heads/" + args.commitish)
    # update workdir
    commit = repo.object_read(branchsha)

    for entry in dir_scan(repo.workdir):
      if entry.name == ".git":
        pass
      elif entry.is_dir():
        shutil.rmtree(entry.path)
      elif entry.is_file():
        os.remove(entry.path)

    unpack_tree(repo.object_read(commit.state["headers"]["tree"]), repo.workdir, repo)
  else:
    # resolve commit
    commitshas = repo.commit_resolve(args.commitish)
    if not commitshas:
      print(f"error: commitish '{args.commitish}' did not match any commit(s) known to tinygit")
      return
    if len(commitshas) > 1:
      print(f"error: commitish '{args.commitish}' is ambiguous:")
      print(commitshas)
      return
    commitsha = commitshas[0]
    commit = repo.object_read(commitsha)

    # set HEAD to this commit, detached
    file_write(repo.gitdir, "HEAD", data=commitsha)
    print("You are in 'detached HEAD' state at " + commitsha)

    # update workdir
    for entry in dir_scan(repo.workdir):
      if entry.name == ".git":
        pass
      elif entry.is_dir():
        shutil.rmtree(entry.path)
      elif entry.is_file():
        os.remove(entry.path)
  
    unpack_tree(repo.object_read(commit.state["headers"]["tree"]), repo.workdir, repo)


# helper function for checkout
# unpack direct children of tree, in path path
def unpack_tree(tree, path, repo):
  for name, sha in tree.items:
    obj = repo.object_read(sha)
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
  commitish = args.commitish

  commitshas = repo.commit_resolve(commitish)
  if not commitshas:
    print(f"Commitish '{commitish}' did not match any commits known to tinygit")
    sys.exit(1)
  if len(commitshas) > 1:
    print(f"Commitish '{commitish}' is ambiguous")
    print(commitshas)
    sys.exit(1)

  commitsha = commitshas[0]
  if not commitsha: 
    print("Your current branch does not have any commits yet")
    sys.exit(1)
  
  commit = repo.object_read(commitsha) 
  while commit:
    print(f"{bcolors.HEADER}commit {object_hash(commit)}{bcolors.ENDC}")
    print(commit.serialize().decode("ascii"))
    commit = repo.object_read(commit.state["headers"]["parent"]) if "parent" in commit.state["headers"] else None


def cmd_tag(args):
  repo = repo_find()
  name = args.name
  objectish = args.objectish

  if not ref_is_name(name):
    print("error: tag name {name} is invalid")
    return
  if file_exists(repo.gitdir, "refs", "tags", name):
    print("error: tag {name} already exists") 
    return
  
  objectsha = repo.object_resolve(objectish)
  if not objectsha:
    print("error: objectish '{objectish}' did not match any object(s) known to tinygit")
    return
  if len(objectsha) > 1:
    print("objectish '{objectish}' is ambiguous")
    return
  
  objectsha = objectsha[0]
  if not objectsha:
    print("error: '{objectish}' is an invalid ref at this point")
  else:
    file_write(repo.gitdir, "refs", "tags", name, data=objectsha[0])


# plumbing commands
# print contents of file to stdout
def cmd_cat_file(args):
  repo = repo_find()
  obj = repo.object_read(args.object)
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
    else:
      raise Exception("Unknown type")
    obj = c(data)

  if args.write:
    repo.object_write(obj)

  print(object_hash(obj))


def cmd_show_ref(args):
  repo = repo_find()
  for k, v in repo.ref_list().items():
    print(f"{v} {k}")



