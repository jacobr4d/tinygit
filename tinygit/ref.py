import os

from tinygit.ref import *
from tinygit.repo import *

# *path is sha or relpath of EXISTING ref
def ref_resolve(*relpath, repo=None):
  if not repo:
    repo = repo_find()
  
  if file_exists(repo.gitdir, *relpath):
    ref = file_read(repo.gitdir, *relpath)
    if not ref_is_relpath(ref):
      return ref
    else:
      return ref_resolve(ref, repo=repo)

# valid ref relpath
def ref_is_relpath(relpath):
  return os.path.normpath(relpath) == relpath and (
      relpath == "HEAD" or
      relpath.startswith("refs/heads/") or 
      relpath.startswith("refs/tags/")
    )

# valid ref name
def ref_is_name(name):
  #  todo: insert regex match
  return os.path.normpath(name) == name

# get dictionary for rel path -> hash for all refs
def ref_list(repo=None):
  if not repo:
    repo = repo_find()

  ret = dict()
  # if ref_resolve("HEAD", repo=repo):
  ret["HEAD"] = ref_resolve("HEAD", repo=repo)
  for entry in dir_scan(repo.gitdir, "refs", "heads"):
    ret["refs/heads/" + entry.name] = ref_resolve("refs/heads/" + entry.name, repo=repo)
  for entry in dir_scan(repo.gitdir, "refs", "tags"):
    ret["refs/tags/" + entry.name] = ref_resolve("refs/tags/" + entry.name, repo=repo)
  return ret
