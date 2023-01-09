import unittest
import tempfile
import shutil
import os
import subprocess
from tinygit.state import * 

class TestCheckoutBranch(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        os.chdir(self.test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_checkout_branch_not_a_repo(self):
        out = subprocess.run(["tinygit", "checkout-branch", "master"], capture_output=True)
        self.assertEqual(out.returncode, 1)

    def test_checkout_branch_bad_branch(self):
        os.system("tinygit init >> /dev/null")
        out = subprocess.run(["tinygit", "checkout-branch", "dne"], capture_output=True)
        self.assertEqual(out.returncode, 1)

    def test_checkout_branch_changes_HEAD(self):
        os.system("tinygit init >> /dev/null")
        os.system("tinygit commit first >> /dev/null")
        os.system("tinygit branch otherbranch >> /dev/null")
        os.system("tinygit checkout-branch otherbranch >> /dev/null")
        self.assertEqual(
            repo_find().get_head(),
            {'type': 'branch', 'id': 'otherbranch'}
        )

    def test_checkout_branch_changes_working_tree(self):
        os.system("tinygit init >> /dev/null")
        os.system("touch a.txt")
        os.system("tinygit commit first >> /dev/null")
        os.system("tinygit branch otherbranch >> /dev/null")
        os.system("tinygit checkout-branch otherbranch")
        os.system("rm a.txt")
        os.system("touch b.txt")
        subprocess.run(["tinygit", "commit", "deleted a, added b"], capture_output=True)
        os.system(f"tinygit checkout-branch master >> /dev/null")
        out = subprocess.run(["ls"], capture_output=True)
        self.assertEqual(out.stdout, b'a.txt\n')

if __name__ == '__main__':
    unittest.main()