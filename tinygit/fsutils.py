import os

def file_exists(*path):
  return os.path.isfile(os.path.join(*path))

def dir_exists(*path):
  return os.path.isdir(os.path.join(*path))

def dir_scan(*path):
  return os.scandir(os.path.join(*path))

def dir_make(*path):
  return os.makedirs(os.path.join(*path))

def file_write(*path, data=None, mkdir=False, mode="w"):
  if len(path) > 1:
    penultimatepath = os.path.join(*path[:-1])
    if mkdir and not os.path.exists(penultimatepath): 
      os.makedirs(penultimatepath)
  with open(os.path.join(*path), mode) as f: 
    f.write(data)

def file_read(*path, mode="r"):
  if not os.path.isfile(os.path.join(*path)): return None
  with open(os.path.join(*path), mode) as f: return f.read()
