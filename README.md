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