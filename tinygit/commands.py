import sys
import os
import configparser
import shutil
from collections import defaultdict
from collections import Counter

from tinygit.utils import *
from tinygit.state import *


def cmd_init(args):
  """tinygit init [<location>]         
  
  Create a tinygit repository.

  Default location is pwd. 
  Fails if location exists and is not a directory or exists and already 
  contains a tinygit repository. 
  Makes location if it doesn't exist.
  """
  location = os.path.abspath(args.location)

  if os.path.exists(location) and not os.path.isdir(location):
    raise Exception(f"Location '{location}' exists and is not a directory")

  if os.path.exists(location) and ".tinygit" in os.listdir(location):
    raise Exception(f"Location '{location}' exists and already contains a tinygit repository")
  
  if not os.path.exists(location):
    os.makedirs(location)
      
  make_dir(location, ".tinygit", "branches")
  make_dir(location, ".tinygit", "objects")
  make_dir(location, ".tinygit", "refs", "tags")
  make_dir(location, ".tinygit", "refs", "heads")
  write_file(location, ".tinygit", "description", data="Unnamed repository; edit this file 'description' to name the repository.\n")
  write_file(location, ".tinygit", "HEAD", data=json.dumps({"type":"branch", "id":"master"}, indent=2))

  print(f"{bcolors.WARNING}hint: Using 'master' as the name for the initial branch.{bcolors.ENDC}")
  print(f"Initialized empty TinyGit repository in {(os.path.join(location, '.tinygit'))}")


def cmd_commit(args):
  """tinygit commit <message>         
  
  Add a snapshot of work to the repository.

  Fails if not called currently in a tinygit repository. 
  Compresses workdir into commit and store it.
  If on branch, advances branch head.
  If not on branch, detaches HEAD.
  """
  repo = repo_find()

  # list dirs in BFS discovery order, avoiding .tinygit etc.
  dirs = []
  for dirpath, dirnames, filenames in os.walk(repo.workdir):
    dirs.append(dirpath)
    if ".tinygit" in dirnames: 
      dirnames.remove(".tinygit")

  # store blob and tree objects
  dirs.reverse()
  treehashes = {}
  tree = None
  for dirpath in dirs:
    tree = GitTree()
    for child in os.scandir(dirpath):
      if child.is_dir() and child.name != ".tinygit":
        tree.items.append((child.name, treehashes[child.path]))
      elif child.is_file():
        with open(child.path, "rb") as f:
          sha = repo.object_write(GitBlob(f.read()))
          tree.items.append((child.name, sha))
    treehashes[dirpath] = repo.object_write(tree)

  # Build and write commit object
  commit = GitCommit()
  commit.state["headers"]["tree"] = object_hash(tree)
  commit.state["body"] = args.message
  head = repo.get_head()
  if head["type"] == "branch":
    if file_exists(repo.tinygitdir, "refs", "heads", head["id"]):
      commit.state["headers"]["parent"] = read_file(repo.tinygitdir, "refs", "heads", head["id"])
  else:
    commit.state["headers"]["parent"] = head["id"]
  commitsha = repo.object_write(commit)

  # Update Head and or Branch
  if head["type"] == "branch":
    write_file(repo.tinygitdir, "refs", "heads", head["id"], data=commitsha)
  else:
    repo.set_head(type="commit", id=commitsha)

  print(f"commit {commitsha} saved")


def cmd_log(args):
  """tinygit log [<commit-alias>]    
  
  Show commit history.

  Starts from commit-alias and works backwards.
  If no commit-alias provided, logs from HEAD backwards.
  Fails if not called currently in a tinygit repository.
  Fails if commit-alias doesn't refer to a commit.
  Fails if commit-alias is ambiguous.
  Fails if the chosen branch has no commit history.
  For each commit prints
    1. sha hash
    2. contents
  """
  repo = repo_find()
  commit_shas = repo.resolve_commit_alias(args.commit)

  if not commit_shas:
    raise Exception(f"'{args.commit}' did not match any commits known to tinygit")

  if len(commit_shas) > 1:
    raise Exception(f"'{args.commit}' is an ambigious alias")

  commit = repo.object_read(commit_shas[0])
  while commit:
    print(f"{bcolors.HEADER}commit {object_hash(commit)}{bcolors.ENDC}")
    print(commit.serialize().decode())
    print()
    commit = repo.object_read(commit.state["headers"]["parent"]) if "parent" in commit.state["headers"] else None


# print status, based on HEAD
def cmd_status(args):
  """tinygit status
  
  Print HEAD. Compares working tree to last commit if there was one.

  Fails if not called currently in a tinygit repository.
  Print new files, deleted files, modified files compared to last commit.
  """
  repo = repo_find()
  print("HEAD")
  print(read_file(repo.tinygitdir, "HEAD"))
  print()
  commit_shas = repo.resolve_commit_alias("HEAD")
  if not commit_shas:
    print("No commits yet")
  else:
    work_entry_map = workdir_entries()
    tree_sha = repo.object_read(commit_shas[0]).state["headers"]["tree"]
    commit_entry_map = tree_entries(tree_sha)
    commit_entry_keys, work_entry_keys = set(commit_entry_map.keys()), set(work_entry_map.keys())

    if commit_entry_map == work_entry_map:
      print("Nothing to commit, working tree clean")
    else:
      for e in work_entry_keys.intersection(commit_entry_keys):
        if work_entry_map[e] != commit_entry_map[e]:
          print(f"Modified {e}")
      for e in work_entry_keys - commit_entry_keys:
        print(f"Added {e}")
      for e in commit_entry_keys - work_entry_keys:
        print(f"Deleted {e}")


def workdir_entries():
  # return map (type, path) -> sha
  # needs to be map to generate created, deleted, modified information
  repo = repo_find()
  # list dir paths in reversed BFS discovery order, avoiding .tinygit etc.
  dir_paths = []
  for dir_path, dir_names, _ in os.walk(repo.workdir):
    dir_paths.append(dir_path)
    if ".tinygit" in dir_names: 
      dir_names.remove(".tinygit")
  dir_paths.reverse()
  # calculate blob and trees
  entry_map = {}
  tree, tree_shas = None, {}
  for dir_path in dir_paths:
    tree = GitTree()
    for entry in os.scandir(dir_path):
      if entry.is_dir() and entry.name != ".tinygit":
        tree.items.append((entry.name, tree_shas[entry.path]))
        entry_map[("dir", os.path.relpath(entry.path, repo.workdir))] = tree_shas[entry.path]
      elif entry.is_file():
        with open(entry.path, "rb") as f:
          file_sha = object_hash(GitBlob(f.read()))
        tree.items.append((entry.name, file_sha))
        entry_map[("file", os.path.relpath(entry.path, repo.workdir))] = file_sha
    tree_shas[dir_path] = object_hash(tree)
  return entry_map


def tree_entries(tree_sha):
  # return map (type, path) -> sha
  # needs to be map to generate created, deleted, modified information
  repo = repo_find()
  entry_map = {}
  tree = repo.object_read(tree_sha)
  S = [(repo.workdir, tree_sha)]
  while S:
    tree_path, tree_sha = S.pop()
    tree = repo.object_read(tree_sha)
    for name, obj_sha in tree.items:
      obj = repo.object_read(obj_sha)
      if obj.kind == "tree":
        entry_map[("dir", os.path.relpath(os.path.join(tree_path, name), repo.workdir))] = obj_sha
        S.append((os.path.join(tree_path, name), obj_sha))
      elif obj.kind == "blob":
        entry_map[("file", os.path.relpath(os.path.join(tree_path, name), repo.workdir))] = obj_sha
  return entry_map


def cmd_checkout_commit(args):
  """tinygit checkout-commit <commitalias>
  
  Checkout a commit.

  Overwrites the the workdir completely, replacing with the contents of the snapshot.
  Fails if not called currently in a tinygit repository.
  Fails if commitalias doesn't resolve to a commit.
  Updates HEAD to commitalias.
  """
  repo = repo_find()
  commit_shas = repo.resolve_commit_alias(args.commit)
  if not commit_shas:
    raise Exception(f"'{args.commit}' did not match any commits known to tinygit")
  if len(commit_shas) > 1:
    raise Exception(f"'{args.commit}' is ambiguous")

  # Update HEAD
  repo.set_head(type="commit", id=commit_shas[0])
  print(f"Entering 'detached HEAD' state at {commit_shas[0]}")

  # Update Working Directory
  commit = repo.object_read(commit_shas[0])
  for entry in scan_dir(repo.workdir):
    if entry.name == ".tinygit":
      pass
    elif entry.is_dir():
      shutil.rmtree(entry.path)
    elif entry.is_file():
      os.remove(entry.path)
  unpack_tree(repo.object_read(commit.state["headers"]["tree"]), repo.workdir, repo)


def cmd_checkout_branch(args):
  """tinygit checkout-branch <branchname>
  
  Checkout a branch.

  Overwrites the the workdir completely, replacing with the contents of the snapshot.
  Fails if not called currently in a tinygit repository.
  Fails if branchname doesn't refer to a branch.
  Updates HEAD to branch.
  """
  repo = repo_find()
  branch_sha = repo.resolve_branch(args.branch)
  if not branch_sha:
    raise Error(f"'{args.branch}' did not match any branches known to tinygit")
  commit = repo.object_read(branch_sha)

  # Update HEAD        
  repo.set_head(type="branch", id=args.branch)
  
  # Update Working Directory
  for entry in scan_dir(repo.workdir):
    if entry.name == ".tinygit":
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


def cmd_branch(args):
  """tinygit branch command
  
  Used for listing branches, creating a branch, and deleting a branch
  """
  repo = repo_find()
  if args.branchtodelete != None:       # delete branch
    if args.branchtodelete not in {entry.name for entry in scan_dir(repo.tinygitdir, "refs", "heads")}:
      print(f"Branch '{args.branchtodelete}' not found")
      return
    os.remove(os.path.join(repo.tinygitdir, "refs", "heads", args.branchtodelete))

  elif args.branchname != "":           # create branch

    if args.branchname in {entry.name for entry in scan_dir(repo.tinygitdir, "refs", "heads")}:
      print(f"A branch named '{args.branchname}' already exists")
      return

    curcommit = repo.resolve_head()
    if curcommit == None:
      print("Cannot make new branch pointing to no commit")
    else:
      write_file(repo.tinygitdir, "refs", "heads", args.branchname, data=curcommit)

  else:                                 # list branches 
    for entry in scan_dir(repo.tinygitdir, "refs", "heads"):
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
  for entry in scan_dir(repo.workdir):
    if entry.name == ".tinygit":
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
    write_file(path + "." + commitsha if path in conflicts else path, data=obj.blobbytes, mode="wb")


def cmd_tag(args):
  repo = repo_find()
  name = args.name
  objectish = args.objectish

  if not ref_is_name(name):
    print("error: tag name {name} is invalid")
    return

  if file_exists(repo.tinygitdir, "refs", "tags", name):
    print("error: tag {name} already exists") 
    return
  
  objectsha = repo.object_resolve(objectish)
  if not objectsha:
    print(f"error: objectish '{objectish}' did not match any object(s) known to tinygit")
    return

  if len(objectsha) > 1:
    print(f"objectish '{objectish}' is ambiguous")
    return
  
  objectsha = objectsha[0]
  if not objectsha:
    print(f"error: '{objectish}' is an invalid ref at this point")
  else:
    write_file(repo.tinygitdir, "refs", "tags", name, data=objectsha)


# plumbing commands
# print contents of file to stdout
def cmd_cat_file(args):
  repo = repo_find()
  obj = repo.object_read(args.object)
  print(f"Requested object is a {obj.kind}")
  if obj.kind == "blob":
    print("blobs are bytes and cannot be printed using this command")
  else:
    print(obj.serialize().decode())


# hash object and optionally write to db
def cmd_hash_object(args): 
  repo = repo_find()
  with open(args.file, "rb") as f:
    data = f.read()
    if   args.type == 'blob': 
      c = GitBlob
    elif args.type == 'commit': 
      c = GitCommit
    elif args.type == 'tag': 
      c = GitTag
    elif args.type == 'tree': 
      c = GitTree
    else:
      raise Exception("Unknown type")
    obj = c(data)

  if args.write:
    repo.object_write(obj)

  print(object_hash(obj))


def cmd_show_ref(args):
  """tinygit show-ref command
  
  Used for diplaying all refs ie branches and tags
  """
  repo = repo_find()
  for k, v in repo.ref_list().items():
    print(f"{v} {k}")



