import unittest
import tempfile
import shutil
import os
import subprocess
from tinygit.state import * 

class TestInit(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        os.chdir(self.test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_commit_not_a_repo(self):
        os.system("touch a.txt")
        out = subprocess.run(["tinygit", "commit", "this wont' work"], capture_output=True)
        self.assertEqual(out.returncode, 1)

    def test_commit_workdir_empty_runs(self):
        os.system("tinygit init >> /dev/null")
        os.system("tinygit commit 'first commit' >> /dev/null")

    def test_commit_workdir_empty_commit_stored(self):
        os.system("tinygit init >> /dev/null")
        out = subprocess.run(["tinygit", "commit", "message"], capture_output=True).stdout.decode()
        commitsha = out.split()[1]
        self.assertEqual(
            repo_find().object_read(commitsha).serialize(), 
            b'{\n  "headers": {\n    "tree": "01704555d3be59fda548e5524445e25b07c9b509"\n  },\n  "body": "message"\n}'
        )

    def test_commit_workdir_empty_tree_stored(self):
        os.system("tinygit init >> /dev/null")
        out = subprocess.run(["tinygit", "commit", "message"], capture_output=True).stdout.decode()
        commitsha = out.split()[1]
        treesha = repo_find().object_read(commitsha).state["headers"]["tree"]
        self.assertEqual(
            repo_find().object_read(treesha).serialize(), 
            b'[]'
        )

    def test_commit_file_stored(self):
        os.system("tinygit init >> /dev/null")
        repo = repo_find()
        os.system("echo 'aaaaa' > a.txt")
        out = subprocess.run(["tinygit", "commit", "message"], capture_output=True).stdout.decode()
        commitsha = out.split()[1]
        treesha = repo.object_read(commitsha).state["headers"]["tree"]
        filesha = repo.object_read(treesha).items[0][1]
        self.assertEqual(
            repo.object_read(filesha).serialize(), 
            b'aaaaa\n'
        )

    # def test_init(self):
    #     os.system("tinygit init >> /dev/null")
    #     out = subprocess.run(["ls", "-a"], capture_output=True)
    #     self.assertEqual(b".\n..\n.tinygit\n", out.stdout)

if __name__ == '__main__':
    unittest.main()