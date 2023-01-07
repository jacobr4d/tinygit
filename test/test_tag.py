import unittest
import tempfile
import shutil
import os
import subprocess

from tinygit.state import * 
from tinygit.utils import * 

class TestTag(unittest.TestCase):
    def setUp(self):
        # Create a tmp directory before all tests
        self.test_dir = tempfile.mkdtemp()
        os.chdir(self.test_dir)

    def tearDown(self):
        # Remove tmp directory after the tests
        shutil.rmtree(self.test_dir)

    def test_tag_not_a_repo(self):
        out = subprocess.run(["tinygit", "tag", "name", "sha"], capture_output=True)
        self.assertEqual(out.returncode, 1)

    def test_tag_invalid_tag_name(self):
        os.system("tinygit init >> /dev/null")
        out = subprocess.run(["tinygit", "commit", "'empty project'"], capture_output=True)
        commit_sha = out.stdout.decode().split()[1]
        out = subprocess.run(["tinygit", "tag", "no_underscores", commit_sha], capture_output=True)
        self.assertEqual(out.returncode, 1)

    def test_tag_duplicate(self):
        os.system("tinygit init >> /dev/null")
        out = subprocess.run(["tinygit", "commit", "'empty project'"], capture_output=True)
        commit_sha = out.stdout.decode().split()[1]
        out = subprocess.run(["tinygit", "tag", "first-commit", commit_sha], capture_output=True)
        out = subprocess.run(["tinygit", "tag", "first-commit", commit_sha], capture_output=True)
        self.assertEqual(out.returncode, 1)

    def test_tag_bad_obj(self):
        os.system("tinygit init >> /dev/null")
        out = subprocess.run(["tinygit", "tag", "first-commit", "dne"], capture_output=True)
        self.assertEqual(out.returncode, 1)
    
    def test_tag_writes_correctly(self):
        os.system("tinygit init >> /dev/null")
        out = subprocess.run(["tinygit", "commit", "'empty project'"], capture_output=True)
        commit_sha = out.stdout.decode().split()[1]
        out = subprocess.run(["tinygit", "tag", "first-commit", commit_sha], capture_output=True)
        self.assertEqual(read_file(repo_find().tinygitdir, "refs", "tags", "first-commit"), commit_sha)

if __name__ == '__main__':
    unittest.main()