import hashlib
import zlib
from repo import *
import collections
from ref import * 

# types of objects: blob, tree, commit, tag
class GitObject:

  def __init__(self, data=None):
    if data != None:
      self.deserialize(data)

  def serialize(self):
    raise Exception("Unimplemented")

  def deserialize(self, data):
    raise Exception("Unimplemented")

class GitBlob(GitObject):
  # bytes representing the raw content of the blob (non dir file)
  kind = "blob"
  # get stored "data" bytes from class fields
  def serialize(self):
    return self.blobbytes
  # get class fields from stored "data" bytes
  def deserialize(self, data):
    self.blobbytes = data

class GitTree(GitObject):
  # list of (mode, path, sha) strings representing the contents of the directory
  kind = "tree"    
  # get stored "data" bytes from class fields
  def serialize(self):
    ret = b''
    for item in self.items:
      ret += (item[0] + " " + item[1] + "\r\n").encode()
    return ret
  # get class fields from stored "data" bytes
  def deserialize(self, data):
    self.items = []
    pos = 0
    max = len(data)
    while pos < max:
      # get path
      ispace = data.find(b' ', pos) 
      path = data[pos:ispace].decode("ascii")
      # get sha (git stores in binary, we store in hex becuase we value our sanity)
      sha = data[ispace + 1:ispace + 41].decode("ascii")
      self.items.append((path, sha)) 
      pos = ispace + 43 # each line ended by \r\n

class GitCommit(GitObject):
  # dict representing (tree, parent, author, authortime, committer, commit time)
  kind = "commit"
  def serialize(self):
    ret = b''
    for k in self.headers.keys():
      ret += (k + ' ' + self.headers[k] + '\n').encode()
    ret += ('\n' + self.body).encode()
    return ret
  def deserialize(self, data):
    self.headers = {}
    pos = 0
    max = len(data)
    while pos < max:
      # get fieldname
      ispace = data.find(b' ', pos)
      inl = data.find(b'\n', pos)
      if (ispace < 0 or inl < ispace):
        self.body = data[inl + 1:].decode()
        break
      else:
        self.headers[data[pos:ispace].decode()] = data[ispace + 1:inl].decode()
      pos = inl + 1



# commitish is either 
# 1. commit sha (e.g. 280beb21fad764ad44e7158e0003eff4459a68f7)
# 2. abbr commit sha (e.g. 280beb2)
# 3. relpath of non-HEAD ref (e.g. HEAD, refs/heads/somebranch, refs/tags/sometag)
# 4. name of non-HEAD ref (e.g. somebranch, sometag)
def commit_resolve(repo, commitish):
  shas = set()
  
  # add object hashes if the objects exist
  # sha case
  if object_exists(repo, commitish):
    shas.add(commitish)
  # abbr sha case
  if os.path.isdir(git_path(repo, "objects", commitish[0:2])):
    for file in os.scandir(git_path(repo, "objects", commitish[0:2])):
      if file.name.startswith(commitish[2:]):
        shas.add(commitish[0:2] + file.name)
  if commitish == "HEAD":
    shas.add(ref_resolve(repo, commitish))
  if git_exists(repo, commitish) and commitish.startswith("refs/heads/"):
    shas.add(ref_resolve(repo, commitish))
  if git_exists(repo, commitish) and commitish.startswith("refs/tags/"):
    shas.add(ref_resolve(repo, commitish))
  if git_exists(repo, "refs", "heads", commitish):
    shas.add(ref_resolve(repo, os.path.join("refs", "heads", commitish)))
  if git_exists(repo, "refs", "tags", commitish):
    shas.add(ref_resolve(repo, os.path.join("refs", "tags", commitish)))

  # keep object hashes if they refer to a commit
  matches = list(shas)
  for sha in shas:
    if not sha: # special case were HEAD points to refs/heads/master, but no commits yet
      continue
    elif object_read(repo, sha).kind != "commit":
      matches.remove(sha)

  return matches



# objectish is either
# 1. object sha (e.g. 280beb21fad764ad44e7158e0003eff4459a68f7)
# 2. obr object sha (e.g. 280beb2)
# 3. name of ref (e.g. HEAD, sometag, somebranch)
# 4. path of a ref (e.g. HEAD, refs/tags/sometag, refs/heads/somebranch)
def object_resolve(repo, objectish):
  return



# return true if object exists in store
def object_exists(repo, sha):
  return os.path.isfile(git_path(repo, "objects", sha[0:2], sha[2:]))



# read an object of any kind from the db
def object_read(repo, sha):
  # read binary
  b =  git_read(repo, "objects", sha[0:2], sha[2:], mode="rb")
  raw = zlib.decompress(b)
  # read type
  ispace = raw.find(b' ')
  kind = raw[0:ispace].decode("ascii")
  # read size
  inull = raw.find(b'\x00', ispace)
  size = int(raw[ispace:inull].decode("ascii"))
  if size != len(raw) - inull - 1: raise Exception("Object corrupted")
  # pick constructor
  if   kind=='blob'   : c=GitBlob
  elif kind=='commit' : c=GitCommit
  elif kind=='tree'   : c=GitTree
  elif kind=='tag'    : c=GitTag
  else: raise Exception("Object corrupted")
  return c(raw[inull + 1:])



# write an object of any kind to the db
def object_write(repo, obj):
  data = obj.serialize()
  raw = obj.kind.encode() + b' ' + str(len(data)).encode() + b'\x00' + data
  sha = hashlib.sha1(raw).hexdigest()
  objpath = git_path(repo, "objects", sha[0:2], sha[2:])
  git_write(repo, "objects", sha[0:2], sha[2:], data=zlib.compress(raw), mkdir=True, mode="wb")  
  return sha



# just return hash, don't write to db
def object_hash(obj):
  data = obj.serialize()
  raw = obj.kind.encode() + b' ' + str(len(data)).encode() + b'\x00' + data
  return hashlib.sha1(raw).hexdigest()
  
  




