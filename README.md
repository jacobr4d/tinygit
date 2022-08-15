Git but tiny.

### Install

```bash
git clone https://github.com/jacobr4d/tinygit.git
cd tinygit
python3 setup.py develop
```

### Uninstall
```bash
cd tinygit
python setup.py develop -u
```

### Example

```bash
tinygit init myproject
cd myproject
touch x y z
tinygit commit "first commit" # no staging, commits whole work dir every time
tinygit log
```

### Same example in git

```bash
git init myproject
cd myproject
touch x y z
git add .
git commit -m "first commit"
git log
```

# Commands

## Basic Snapshotting
```bash
tinygit status
tinygit commit <msg>
tinygit checkout <commitish>
```

## Branching and Merging (incomplete)
```bash
tinygit log <commitish> 
tinygit tag <name> <objectish>
```

## Notes
1. <objectish> is one of
    1. object sha (e.g. 280beb21fad764ad44e7158e0003eff4459a68f7)
    1. abbr object sha (e.g. 280beb2)
    1. name of ref (e.g. HEAD, sometag, somebranch)
    1. path of a ref (e.g. HEAD, refs/tags/sometag, refs/heads/somebranch)
1. <commitish> is an <objectish> referring to a commit object