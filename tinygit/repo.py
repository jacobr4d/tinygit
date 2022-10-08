import os 
import configparser
import hashlib
import zlib
import collections

from tinygit.fsutils import *
import tinygit.gitobjects
from tinygit.gitobjects import *

# internal representation of a repo 
class GitRepo:

  def __init__(self, workdir):
    self.workdir = workdir
    self.gitdir = os.path.join(workdir, ".git")
    
    if not os.path.isdir(self.gitdir):
      raise Exception("Not a git repository %s" % workdir)


# read a repo from where we are running this command
def repo_find(path="."):
  path = os.path.realpath(path)
  if os.path.isdir(os.path.join(path, ".git")): 
    return GitRepo(path)
  else:
    parentpath = os.path.realpath(os.path.join(path, ".."))
    if parentpath == path: raise Exception("No repository")
    return repo_find(path=parentpath)

# return true if object exists in store
def object_exists(sha, repo=None):
  if not repo:
    repo = repo_find()
  return file_exists(repo.gitdir, "objects", sha[0:2], sha[2:])


# read an object of any kind from the db
def object_read(sha, repo=None):
  if not repo:
    repo = repo_find()
  # read binary
  b =  file_read(repo.gitdir, "objects", sha[0:2], sha[2:], mode="rb")
  raw = zlib.decompress(b)
  # read type
  ispace = raw.find(b' ')
  kind = raw[0:ispace].decode("ascii")
  # read size
  inull = raw.find(b'\x00', ispace)
  size = int(raw[ispace:inull].decode("ascii"))
  if size != len(raw) - inull - 1: raise Exception("Object corrupted")
  # pick constructor
  if   kind=='blob'   : c=tinygit.gitobjects.GitBlob
  elif kind=='commit' : c=tinygit.gitobjects.GitCommit
  elif kind=='tree'   : c=tinygit.gitobjects.GitTree
  elif kind=='tag'    : c=tinygit.gitobjects.GitTag
  else: raise Exception("Object corrupted")
  return c(raw[inull + 1:])


# write an object of any kind to the db
def object_write(obj, repo=None):
  if not repo:
    repo = repo_find()
  data = obj.serialize()
  raw = obj.kind.encode() + b' ' + str(len(data)).encode() + b'\x00' + data
  sha = hashlib.sha1(raw).hexdigest()
  objpath = os.path.join(repo.gitdir, "objects", sha[0:2], sha[2:])
  file_write(repo.gitdir, "objects", sha[0:2], sha[2:], data=zlib.compress(raw), mkdir=True, mode="wb")  
  return sha

