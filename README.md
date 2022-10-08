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
mkdir myproject; cd myproject
tinygit init
cd myproject
touch x y z
tinygit commit "first commit" # no staging, commits workdir as it is
tinygit log
```

### Same example in git

```bash
mkdir myproject; cd myproject
git init
cd myproject
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
tinygit checkout <commitish>    # updates workdir to commitish as it is
tinygit log
tinygit tag <name> [<objectish>]
```

## Branching and Merging
```bash
tinygit branch                  # list branches
tinygit branch <branchname>     # create branch
tinygit checkout <branchname>   # updates workdir to branchname as it is
tinygit merge <branchname>      # brings in data, doesn't commit
```

## Notes
1. Key difference between git and tinygit is how merging is handled.
    - In git, merge automatically makes a new commit with the merge
    - In tinygit, merge updates the workdir with the merge, but you have to commit after that

I learned about the internals of Git from
- Chapter 9 of *Pro Git* by Scott Chacon
- https://github.com/thblt/write-yourself-a-git 