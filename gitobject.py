import hashlib
import zlib
from repo import *
import collections

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

# read an object of any kind from the db
def object_read(sha):
  """read object from git repo using its hash as the identifier"""
  path = repo_file("objects", sha[0:2], sha[2:])
  with open(path, "rb") as f:
    raw = zlib.decompress(f.read())
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
def object_write(obj):
  data = obj.serialize()
  raw = obj.kind.encode() + b' ' + str(len(data)).encode() + b'\x00' + data
  sha = hashlib.sha1(raw).hexdigest()
  path = repo_file("objects", sha[0:2], sha[2:], mkdir=True)
  with open(path, 'wb') as f: 
    f.write(zlib.compress(raw))
  return sha

# just return hash, don't write to db
def object_hash(obj):
  data = obj.serialize()
  raw = obj.kind.encode() + b' ' + str(len(data)).encode() + b'\x00' + data
  return hashlib.sha1(raw).hexdigest()
  
  




