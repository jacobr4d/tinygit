Git but simple, with no staging area.
Inspired by Git.

### Install

```bash
git clone https://github.com/jacobr4d/tinygit.git
cd tinygit
python3 setup.py develop
```

### Uninstall
```bash
cd tinygit
python3 setup.py develop -u
```

### Example

```bash
mkdir myproject
cd myproject
tinygit init
touch x y z
tinygit commit "first commit"   # no staging, commits workdir as it is
tinygit log
```

### Same example in git

```bash
mkdir myproject
cd myproject
git init
touch x y z
git add .
git commit -m "first commit"
git log
```

# Commands

## Basic Snapshotting
```bash
tinygit init                    
tinygit status
tinygit commit <message>
tinygit checkout-commit <commit-alias>
tinygit log [<commit-alias>]
tinygit tag <name> [<object-alias>]
```

## Branching and Merging
```bash
tinygit branch                  
tinygit branch <branch>     
tinygit checkout-branch <branch>
tinygit merge <branch>
```

I learned about the internals of Git from
- Chapter 9 of *Pro Git* by Scott Chacon
- https://github.com/git
- Articles like
    - https://www.cloudbees.com/blog/git-detached-head
    - https://github.com/thblt/write-yourself-a-git 