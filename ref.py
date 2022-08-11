import os

from repo import *

# get final sha from ref relpath e.g. (HEAD, refs/tags/sometag)
def ref_resolve(repo, relpath):
  if relpath and (relpath == "HEAD" or relpath.startswith("refs/")):
    newpath = git_read(repo, relpath)
    return ref_resolve(repo, newpath)
  else:
    return relpath

# get dictionary for rel path -> hash for all refs
def ref_list():
  repo = repo_find()
  ret = {}
  for fname in os.listdir(repo_file(repo, "refs", "heads")):
    ret["refs/heads/" + fname] = ref_resolve("refs/heads/" + fname)
  for fname in os.listdir(repo_file(repo, "refs", "tags")):
    ret["refs/tags/" + fname] = ref_resolve("refs/tags/" + fname)
  ret["HEAD"] = ref_resolve("HEAD")
  return reta