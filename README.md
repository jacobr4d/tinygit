Git but tiny.

I learned about the internals of Git from
- chapter 9 of by *Pro Git* by Scott Chacon
- https://github.com/thblt/write-yourself-a-git 

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
tinygit init myproject
cd myproject
touch x y z
tinygit commit "first commit" # no staging, commits workdir as it is every time
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
tinygit init <workdir>
tinygit status
tinygit commit <message>
tinygit checkout <commitish>
```

## Branching and Merging (incomplete)
```bash
tinygit log [<commitish>]
tinygit tag <name> [<objectish>]
tinygit show-ref 
```

## Note
1. ```<objectish>``` is an object recognized by git, either
    1. object hash (e.g. 280beb21fad764ad44e7158e0003eff4459a68f7)
    1. abbr object hash (e.g. 280beb2)
    1. name of ref (e.g. HEAD, sometag, somebranch)
    1. path of a ref (e.g. HEAD, refs/tags/sometag, refs/heads/somebranch)
1. ```<commitish>``` is an ```<objectish>``` which resolves to a commit (e.g. HEAD, 280beb21fad764ad44e7158e0003eff4459a68f7, or sometagpointingtoacommit)
1. for a more thorough explanation of a command, use ```tinygit <command> -h``` (e.g. tinygit tag -h)