import os 
import sys
import configparser
import hashlib
import zlib
import collections
import json

from tinygit.utils import *

# Repo state fetched upon invocatio of all commands
class GitRepo:
  """The state for the repo obtained at the beginning every command.

  The state simply consists of the work directory path and the 
  tinygit directory path. The work directory is where the users work
  is. The tinygit directory is where the history of the project is
  stored.

  Attributes:
      workdir (str): Path of the work directory.
      gitdir (str): Path of the tinygit directory.

  """

  def __init__(self, workdir):
    self.workdir = workdir
    self.tinygitdir = os.path.join(workdir, ".tinygit")
    
    if not os.path.isdir(self.tinygitdir):
      raise Exception("Not a git repository %s" % workdir)

  def get_head(self):
    return json.loads(read_file(self.tinygitdir, "HEAD"))

  def set_head(self, type, id):
    write_file(self.tinygitdir, "HEAD", data=json.dumps({"type": type, "id": id}, indent=2))

  # obtain sha of commit head points to or None if no commits yet
  def resolve_head(self):
    head = self.get_head()
    if head["type"] == "branch":
      if file_exists(self.tinygitdir, "refs", "heads", head["id"]):
        return read_file(self.tinygitdir, "refs", "heads", head["id"])
      else:
        return None   # no commits yet
    elif head["type"] == "commit":
      return head["id"]

  # sha from branch name
  def resolve_branch(self, name):
    if file_exists(self.tinygitdir, "refs", "heads", name):
      return read_file(self.tinygitdir, "refs", "heads", name)
    else:
      return None

  # sha from tag name
  def resolve_tag(self, name):
    if file_exists(self.tinygitdir, "refs", "tags", name):
      return read_file(self.tinygitdir, "refs", "tags", name)
    else:
      return None

  # MIGHT BE A BUG HERE
  def resolve_obj(self, name):
    if file_exists(self.tinygitdir, "objects", name[0:2], name[2:]):
      return read_file(self.tinygitdir, "objects", name[0:2], name[2:])
    return None

  # sha from abbr sha
  def resolve_obj_abbr(self, name):
    ret = []
    if dir_exists(self.tinygitdir, "objects", name[0:2]):
      for entry in scan_dir(self.tinygitdir, "objects", name[0:2]):
        if entry.name.startswith(objectish[2:]):
          ret.add(objectish[0:2] + entry.name)
    return ret

  def object_exists(self, sha):
    return file_exists(self.tinygitdir, "objects", sha[0:2], sha[2:])

  # read an object of any kind from the db
  def object_read(self, sha):
    # read binary
    b =  read_file(self.tinygitdir, "objects", sha[0:2], sha[2:], mode="rb")
    raw = zlib.decompress(b)
    # read type
    ispace = raw.find(b' ')
    kind = raw[0:ispace].decode("ascii")
    # read size
    inull = raw.find(b'\x00', ispace)
    size = int(raw[ispace:inull].decode("ascii"))
    if size != len(raw) - inull - 1: 
      raise Exception("Object corrupted")
    # pick constructor
    if   kind=='blob'   : c=GitBlob
    elif kind=='commit' : c=GitCommit
    elif kind=='tree'   : c=GitTree
    elif kind=='tag'    : c=GitTag
    else: raise Exception("Object corrupted")
    return c(raw[inull + 1:])

  # write an object of any kind to the db
  def object_write(self, obj):
    data = obj.serialize()
    raw = obj.kind.encode() + b' ' + str(len(data)).encode() + b'\x00' + data
    sha = hashlib.sha1(raw).hexdigest()
    write_file(self.tinygitdir, "objects", sha[0:2], sha[2:], data=zlib.compress(raw), mode="wb")  
    return sha

  # objectish is either
  # 1. HEAD
  # 2. object sha (e.g. 280beb21fad764ad44e7158e0003eff4459a68f7)
  # 3. obr object sha (e.g. 280beb2)
  # 4. name of branch or tag (e.g. sometag, somebranch)
  def object_resolve(self, objectish):
    shas = set()
    if objectish == "HEAD":
      shas.add(self.resolve_head())
    if resolve_branch(objectish):
      shas.add(resolve_branch(objectish))
    if resolve_tag(objectish):
      shas.add(resolve_branch(objectish))
    if resolve_obj(objectish):
      shas.add(resolve_obj(objectish))
    if resolve_obj_abbr(objectish):
      shas.add(resolve_obj_abbr(objectish))
    return list(shas)

  # commitish is objtect resolving to a commit
  def commit_resolve(self, commitish):
    shas = self.object_resolve(commitish)
    return [sha for sha in shas if not sha or self.object_read(sha).kind == "commit"]

  # get dictionary for rel path -> hash for all refs
  def ref_list():
    ret = {"HEAD": self.resolve_head()}
    for entry in scan_dir(self.tinygitdir, "refs", "heads"):
      ret["refs/heads/" + entry.name] = resolve_branch(entry.name)
    for entry in scan_dir(self.tinygitdir, "refs", "tags"):
      ret["refs/tags/" + entry.name] = resolve_tag(entry.name)
    return ret


# read a repo from where we are running tinygit from
def repo_find(path="."):
  path = os.path.realpath(path)
  if os.path.isdir(os.path.join(path, ".tinygit")): 
    return GitRepo(path)
  else:
    parentpath = os.path.realpath(os.path.join(path, ".."))
    if parentpath == path:
      print("Not a tinygit repository (or any of the parent directories)")
      sys.exit(1)
    return repo_find(path=parentpath)


# just return hash, don't write to db
def object_hash(obj):
  data = obj.serialize()
  raw = obj.kind.encode() + b' ' + str(len(data)).encode() + b'\x00' + data
  return hashlib.sha1(raw).hexdigest()
  
class GitBlob:
  """Blob class.

  Binary representation of blob is just the blob.

  Attributes:
    kind (str): the kind of obj, namely blob.
    blobbytes (str): contents of file.

  """
  kind = "blob"

  def __init__(self, data=None):
    self.blobbytes = None
    if data != None:
      self.deserialize(data)

  def serialize(self):
    return self.blobbytes

  def deserialize(self, data):
    self.blobbytes = data


class GitTree:
  """Tree class.

  Binary representation of tree is a textual list of (path, objsha) pairs, encoded.

  Attributes:
    kind (str): the kind of obj, namely tree.
    items (list): contents of directory.

  """
  kind = "tree"

  def __init__(self, data=None):
    self.items = []
    if data != None:
      self.deserialize(data)

  def serialize(self):
    return json.dumps(self.items, indent=2).encode()

  def deserialize(self, data):
    self.items = json.loads(data.decode("ascii"))

class GitCommit:
  """Tree class.

  Binary representation of commit is state = {
    "headers": <a string dict of headers>, 
    "body": <a string body>
  }

  Attributes:
    kind (str): the kind of obj, namely commit.
    items (list): contents of directory.

  """
  kind = "commit"

  def __init__(self, data=None):
    if data != None:
      self.deserialize(data)
    else:
      self.state = {"headers": {}, "body": ""}

  def serialize(self):
    return json.dumps(self.state, indent=2).encode()

  def deserialize(self, data):
    self.state = json.loads(data.decode("ascii"))


# valid ref name
def ref_is_name(name):
  #  todo: insert regex match
  return os.path.normpath(name) == name

def is_valid_branch_name(name):
  return not name.contains("/") and name != "HEAD"

