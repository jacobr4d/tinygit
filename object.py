import hashlib

class GitObject:
  """types = {blob, commit, tag, tree}"""

  def __init__(self, data)
    if data != None:
      self.write(data)

  def write(self):
    raise Exception("Unimplemented")

  def read(self, data):
    raise Exception("Unimplemented")

class GitBlob(GitObject):
  """ just a file """
  typee = 'blob'

  def write(self, data):
    self.blobdata = data

  def read(self):
    return self.blobdata

class GitCommit:

class GitTag:

class GitTree:

def object_read(repo, sha):
  """read object from git repo using its hash as the identifier"""
  path = repo_file(repo, "objects", sha[0:2], sha[2:])
  with open(path, "rb") as f:
    raw = zlib.decompress(f.read())
    # read type
    ispace = raw.find(b' ')
    typee = raw[0:ispace].decode("ascii")
    # read and check size
    inull = raw.find('\x00', ispace)
    size = int(raw[ispace:inull].decode("ascii"))
    if size != len(raw) - inull - 1 
      raise Exception("Malformed object, bad length: {}".format(sha))
    # pick constructor
    if   typee=='blob'   : c=GitBlob
    elif typee=='commit' : c=GitCommit
    elif typee=='tree'   : c=GitTree
    elif typee=='tag'    : c=GitTag
    else: raise Exception("Unknown type {} for object {}".format(typee, sha))
    return c(raw[inull + 1:])

def object_write(repo, obj)
  raw = obj.typee + b' ' + str(len(data)).encode() + b'\x00' + obj.read()
  sha = hashlib.sha1(raw).hexdigest()
  path = repo_file(repo, "objects", sha[0:2], sha[2:], mkdir=actually_write)
  with open(path, 'wb') as f:
    f.write(zlib.compress(raw))
  return sha

# just return hash, don't write to db
def object_hash(obj)
  raw = obj.typee + b' ' + str(len(data)).encode() + b'\x00' + obj.read()
  return hashlib.sha1(raw).hexdigest()
