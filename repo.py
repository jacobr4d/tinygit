# imports
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

    configpath = repo_path(self, "config")
    if os.path.exists(repo_path):
      self.config.read(repo_path)
    else:
      raise Exception("No config for git repository %s" % workdir)

def repo_path(repo, *path):
    return os.path.join(repo.gitdir, *path)

def repo_file(repo, *path, mkdir=False):
    if repo_dir(repo, *path[:-1], mkdir=mkdir):
        return repo_path(repo, *path)

def repo_dir(repo, *path, mkdir=False):
    path = repo_path(repo, *path)
    if os.path.exists(path):
        if (os.path.isdir(path)):
            return path
        else:
            raise Exception("Not a directory %s" % path)
    if mkdir:
        os.makedirs(path)
        return path
    else:
        return None

# read a repo from where we are running this command
def repo_find(path="."):
  path = os.path.realpath(path)
  if os.path.isdir(os.path.join(path, ".git")):
    return GitRepo(path)
  else:
    parent = os.path.realpath(os.path.join(path, ".."))
    if parent == path:
      raise Exception("No repository")
    return repo_find(parent)
