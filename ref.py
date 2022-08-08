import os

from repo import *

# given a path for a ref, e.g. HEAD or refs/heads/master
#, get the hash for the object it is referring to
def ref_resolve(path):
  fullpath = repo_file(path)
  if not os.path.exists(fullpath): #probably head
    return None
  with open(fullpath, "r") as f:
    data = f.read()[:-1] # drop newline
    if data.startswith("ref: "):
      return ref_resolve(data[5:])
    else: return data

# get dictionary for rel path -> hash for all refs
def ref_list():
  ret = {}
  for fname in os.listdir(repo_file("refs", "heads")):
    ret["refs/heads/" + fname] = ref_resolve("refs/heads/" + fname)
  for fname in os.listdir(repo_file("refs", "tags")):
    ret["refs/tags/" + fname] = ref_resolve("refs/tags/" + fname)
  ret["HEAD"] = ref_resolve("HEAD")
  return ret