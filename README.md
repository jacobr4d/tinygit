Git-like CLI program, written in Python.

~500 lines.

# Installation
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

# Example
### Tinygit example
```bash
mkdir myproject
cd myproject
tinygit init
touch x y z
tinygit commit "first commit"
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

# More Information
Some things tinygit doesn't do that I might add in the future
- [git diff](https://git-scm.com/docs/git-diff)
- [recursive merge](https://git-scm.com/docs/git-merge#_merge_strategies)
    - Currently, conflicting files are both present after a merge
- [git config](https://git-scm.com/docs/git-config)

Some things that tinygit does that git doesn't do
- tinygit allows you to track an empty directory, while git doesn't
    - this was surprising to me, becuase empty directories are occasionally useful in projects
    - [read more about it](https://git.wiki.kernel.org/index.php/GitFaq#Can_I_add_empty_directories.3F)
- tinygit allows you to commit an empty working directory and git does not
- tinygit allows you to commit an unchanged working directory and git does not

Where I learned about how git really works
- Chapter 10 of [Pro Git](https://git-scm.com/book/en/v2) by Scott Chacon
- [The source code](https://github.com/git)
- [Other similar endevours](https://wyag.thb.lt/#orgf4e54f0)

# Even More Details
