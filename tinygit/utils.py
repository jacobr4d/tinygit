import os

def dir_exists(*path):
  return os.path.isdir(os.path.join(*path))

def make_dir(*path):
  return os.makedirs(os.path.join(*path))

def scan_dir(*path):
  return os.scandir(os.path.join(*path))

def file_exists(*path):
  return os.path.isfile(os.path.join(*path))

def write_file(*path, data=None, mode="w"):
  if len(path) > 1 and not os.path.exists(os.path.join(*path[:-1])): 
    os.makedirs(os.path.join(*path[:-1]))
  with open(os.path.join(*path), mode) as f: 
    f.write(data)

def read_file(*path, mode="r"):
  if not os.path.isfile(os.path.join(*path)): 
    return None
  with open(os.path.join(*path), mode) as f: 
    return f.read()

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'