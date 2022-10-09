import hashlib
import json

from tinygit.fsutils import *
from tinygit.ref import *


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
    return json.dumps(self.items).encode()

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
    self.state = {"headers": {}, "body": ""}
    if data != None:
      self.deserialize(data)

  def serialize(self):
    return json.dumps(self.state, indent=2).encode()

  def deserialize(self, data):
    self.state = json.loads(data.decode("ascii"))

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
  return [sha for sha in shas if not sha or object_read(sha, repo=repo).kind == "commit"]

# branch is 
# 1. name of branch (e.g. somebranch)
def branch_resolve(branchish, repo=None):
  if not repo:
    repo = repo_find()
  # name of ref case
  if ref_is_name(branchish) and file_exists(repo.gitdir, "refs", "heads", branchish):
    return ref_resolve("refs", "heads", branchish, repo=repo)
  return None  




