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
# 3. relpath of ref (e.g. HEAD, refs/heads/somebranch, refs/tags/sometag)
# 4. name of ref (e.g. HEAD, somebranch, sometag)
def commit_resolve(commitish, repo=None):
  if not repo:
    repo = repo_find()

  # resolve object
  shas = object_resolve(commitish, repo=repo)

  # filter candidate object hashes by whethet they point to a COMMIT
  # don't remove None, becuase that is special case where no commits on master yet
  matches = shas[:]
  for sha in shas:
    if sha and object_read(sha, repo=repo).kind != "commit":
      matches.remove(sha)

  return matches


# objectish is either
# 1. object sha (e.g. 280beb21fad764ad44e7158e0003eff4459a68f7)
# 2. obr object sha (e.g. 280beb2)
# 3. name of ref (e.g. HEAD, sometag, somebranch)
# 4. path of a ref (e.g. HEAD, refs/tags/sometag, refs/heads/somebranch)
def object_resolve(objectish, repo=None):
  if not repo:
    repo = repo_find()
  
  shas = set()
  
  # collect candidate object hashes
  # sha case
  if file_exists(repo.gitdir, "objects", objectish[0:2], objectish[2:]):
    shas.add(objectish)
  # abbr sha case
  if len(objectish) == 7:
    if dir_exists(repo.gitdir, "objects", objectish[0:2]):
      for entry in dir_scan(repo.gitdir, "objects", objectish[0:2]):
        if entry.name.startswith(objectish[2:]):
          shas.add(objectish[0:2] + entry.name)
  # relpath of ref case
  if ref_is_relpath(objectish) and file_exists(repo.gitdir, objectish):
    shas.add(ref_resolve(objectish, repo=repo))
  # name of ref case
  if ref_is_name(objectish) and file_exists(repo.gitdir, "refs", "heads", objectish):
    shas.add(ref_resolve("refs", "heads", objectish, repo=repo))
  if ref_is_name(objectish) and file_exists(repo.gitdir, "refs", "tags", objectish):
    shas.add(ref_resolve("refs", "tags", objectish, repo=repo))

  return list(shas)



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
  if   kind=='blob'   : c=GitBlob
  elif kind=='commit' : c=GitCommit
  elif kind=='tree'   : c=GitTree
  elif kind=='tag'    : c=GitTag
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



# just return hash, don't write to db
def object_hash(obj):
  data = obj.serialize()
  raw = obj.kind.encode() + b' ' + str(len(data)).encode() + b'\x00' + data
  return hashlib.sha1(raw).hexdigest()
  
  




