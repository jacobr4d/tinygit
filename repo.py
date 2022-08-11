# imports
import os 
import configparser

# internal representation of a repo 
class GitRepo:

  def __init__(self, workdir):
    self.workdir = workdir
    self.gitdir = os.path.join(workdir, ".git")
    self.config = configparser.ConfigParser()
    
    if not os.path.isdir(self.gitdir):
      raise Exception("Not a git repository %s" % workdir)

    if os.path.exists(os.path.join(self.gitdir, "config")): 
      self.config.read(os.path.join(self.gitdir, "config"))
    else: 
      raise Exception("No config for git repository %s" % self.workdir)

def file_exists(*path):
  return os.path.isfile(os.path.join(*path))

def dir_exists(*path):
  return os.path.isdir(os.path.join(*path))

def dir_scan(*path):
  return os.path.scandir(os.path.join(*path))

# write in .git directory
def file_write(*path, data=None, mkdir=False, mode="w"):
  penultimatepath = os.path.join(*path[:-1])
  if mkdir and not os.path.exists(penultimatepath): 
    os.makedirs(penultimatepath)
  with open(os.path.join(*path), mode) as f: f.write(data)

def file_read(*path, mode="r"):
  if not os.path.isfile(os.path.join(*path)): return None
  with open(os.path.join(*path), mode) as f: return f.read()



# read a repo from where we are running this command
def repo_find(path="."):
  path = os.path.realpath(path)
  if os.path.isdir(os.path.join(path, ".git")): 
    return GitRepo(path)
  else:
    parentpath = os.path.realpath(os.path.join(path, ".."))
    if parentpath == path: raise Exception("No repository")
    return repo_find(path=parentpath)

