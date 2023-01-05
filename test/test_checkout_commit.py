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

    def test_checkout_commit_not_a_repo(self):
        out = subprocess.run(["tinygit", "checkout-commit", "HEAD"], capture_output=True)
        self.assertEqual(out.returncode, 1)

    def test_checkout_commit_bad_commit_alias(self):
        os.system("tinygit init >> /dev/null")
        out = subprocess.run(["tinygit", "checkout-commit", "dne"], capture_output=True)
        self.assertEqual(out.returncode, 1)

    def test_checkout_commit_ambiguous_commit_alias(self):
        os.system("tinygit init >> /dev/null")
        out = subprocess.run(["tinygit", "commit", "first"], capture_output=True).stdout.decode()
        first_sha = out.split()[1]
        out = subprocess.run(["tinygit", "commit", "second"], capture_output=True).stdout.decode()
        second_sha = out.split()[1]
        # a quite devious tag... so evil!!!
        os.system(f"tinygit tag {first_sha[:7]} {second_sha}")
        out = subprocess.run(["tinygit", "checkout-commit", first_sha[:7]], capture_output=True)
        self.assertEqual(out.returncode, 1)

    def test_checkout_commit_affect_HEAD(self):
        os.system("tinygit init >> /dev/null")
        os.system("tinygit commit first >> /dev/null")
        os.system("tinygit checkout-commit HEAD >> /dev/null")
        self.assertEqual(
            repo_find().get_head(),
            {'type': 'commit', 'id': '3e1a939bd3fd30ba3d114bedba0fb888183f0b20'}
        )

    def test_checkout_commit_affect_workdir(self):
        os.system("tinygit init >> /dev/null")
        os.system("touch a.txt")
        out = subprocess.run(["tinygit", "commit", "first"], capture_output=True).stdout.decode()
        first_sha = out.split()[1]
        os.system("rm a.txt")
        os.system("touch b.txt")
        subprocess.run(["tinygit", "commit", "second"], capture_output=True)
        os.system(f"tinygit checkout-commit {first_sha} >> /dev/null")
        out = subprocess.run(["ls"], capture_output=True)
        self.assertEqual(out.stdout, b'a.txt\n')

if __name__ == '__main__':
    unittest.main()