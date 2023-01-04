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

    def test_commit_empty_runs(self):
        os.system("tinygit init >> /dev/null")
        os.system("tinygit commit 'first commit' >> /dev/null")

    def test_commit_empty_commit_stored(self):
        os.system("tinygit init >> /dev/null")
        out = subprocess.run(["tinygit", "commit", "message"], capture_output=True).stdout.decode()
        commitsha = out.split()[1]
        self.assertEqual(
            repo_find().object_read(commitsha).serialize(), 
            b'{\n  "headers": {\n    "tree": "01704555d3be59fda548e5524445e25b07c9b509"\n  },\n  "body": "message"\n}'
        )

    def test_commit_empty_tree_stored(self):
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

    def test_head_after_commit_branch(self):
        os.system("tinygit init >> /dev/null")
        os.system("tinygit commit first >> /dev/null")
        self.assertEqual(
            repo_find().get_head(),
            {
                "type": "branch",
                "id": "master"
            }
        )
        self.assertEqual(
            repo_find().resolve_head(),
            "3e1a939bd3fd30ba3d114bedba0fb888183f0b20"
        )

    def test_head_after_commit_detached(self):
        os.system("tinygit init >> /dev/null")
        os.system("tinygit commit first >> /dev/null")
        os.system("tinygit checkout-commit HEAD >> /dev/null")
        self.assertEqual(
            repo_find().get_head(),
            {
                "type": "commit",
                "id": "3e1a939bd3fd30ba3d114bedba0fb888183f0b20"
            }
        )
        self.assertEqual(
            repo_find().resolve_head(),
            "3e1a939bd3fd30ba3d114bedba0fb888183f0b20"
        )


    # test commit detached

if __name__ == '__main__':
    unittest.main()