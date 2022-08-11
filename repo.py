# imports
import os 
import configparser

# internal representation of a repo 
class GitRepo:
  workdir = None
  gitdir = None
  config = None

  def __init__(self, workdir):
    self.workdir = workdir
    self.gitdir = os.path.join(workdir, ".git")
    self.config = configparser.ConfigParser()
    
    if not os.path.isdir(self.gitdir):
      raise Exception("Not a git repository %s" % workdir)

    configpath = git_path(self, "config")
    if os.path.exists(configpath): self.config.read(configpath)
    else: raise Exception("No config for git repository %s" % workdir)

def git_path(repo, *path):
  return os.path.join(repo.gitdir, *path)

# write in .git directory
def git_write(repo, *path, data=None, mkdir=False, mode="w"):
  penultimatepath = git_path(repo, *path[:-1])
  if mkdir and not os.path.exists(penultimatepath): 
    os.makedirs(penultimatepath)
  with open(git_path(repo, *path), mode) as f: f.write(data)

def git_read(repo, *path, mode="r"):
  if not os.path.isfile(git_path(repo, *path)): return None
  with open(git_path(repo, *path), mode) as f: return f.read()

def git_exists(repo, *path, mode="file"):
  if mode == "file":
    return os.path.isfile(git_path(repo, *path))
  elif mode == "dir":
    return os.path.isdir(git_path(repo, *path))

# read a repo from where we are running this command
def repo_find(path="."):
  path = os.path.realpath(path)
  if os.path.isdir(os.path.join(path, ".git")): 
    return GitRepo(path)
  else:
    parentpath = os.path.realpath(os.path.join(path, ".."))
    if parentpath == path: raise Exception("No repository")
    return repo_find(path=parentpath)

