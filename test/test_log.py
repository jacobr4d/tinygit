import unittest
import tempfile
import shutil
import os
import subprocess

class TestLog(unittest.TestCase):
    def setUp(self):
        # Create a tmp directory before all tests
        self.test_dir = tempfile.mkdtemp()
        os.chdir(self.test_dir)

    def tearDown(self):
        # Remove tmp directory after the test
        shutil.rmtree(self.test_dir)

    def test_log_no_repo(self):
        out = subprocess.run(["tinygit", "log"], capture_output=True)
        self.assertEqual(out.returncode, 1)

    def test_log_new_repo(self):
        os.system("tinygit init >> /dev/null")
        out = subprocess.run(["tinygit", "log"], capture_output=True)
        self.assertEqual(out.returncode, 1)

    def test_log_one_commit_master(self):
        os.system("tinygit init >> /dev/null")
        os.system("tinygit commit first >> /dev/null")
        out = subprocess.run(["tinygit", "log"], capture_output=True)
        self.assertEqual(
            out.stdout, 
            b'\x1b[95mcommit 3e1a939bd3fd30ba3d114bedba0fb888183f0b20\x1b[0m\n{\n  "headers": {\n    "tree": "01704555d3be59fda548e5524445e25b07c9b509"\n  },\n  "body": "first"\n}\n\n'    
        )

    def test_log_two_commits_master(self):
        os.system("tinygit init >> /dev/null")
        os.system("tinygit commit first >> /dev/null")
        os.system("tinygit commit second >> /dev/null")
        out = subprocess.run(["tinygit", "log"], capture_output=True)
        self.assertEqual(
            out.stdout, 
            b'\x1b[95mcommit 44b9c372364f91cd4d0e7c84fee2d1ff27be295d\x1b[0m\n{\n  "headers": {\n    "tree": "01704555d3be59fda548e5524445e25b07c9b509",\n    "parent": "3e1a939bd3fd30ba3d114bedba0fb888183f0b20"\n  },\n  "body": "second"\n}\n\n\x1b[95mcommit 3e1a939bd3fd30ba3d114bedba0fb888183f0b20\x1b[0m\n{\n  "headers": {\n    "tree": "01704555d3be59fda548e5524445e25b07c9b509"\n  },\n  "body": "first"\n}\n\n'
        )

    def test_log_one_commit_detached(self):
        os.system("tinygit init >> /dev/null")
        os.system("tinygit commit first >> /dev/null")
        os.system("tinygit checkout-commit HEAD >> /dev/null")
        out = subprocess.run(["tinygit", "log"], capture_output=True)
        self.assertEqual(
            out.stdout, 
            b'\x1b[95mcommit 3e1a939bd3fd30ba3d114bedba0fb888183f0b20\x1b[0m\n{\n  "headers": {\n    "tree": "01704555d3be59fda548e5524445e25b07c9b509"\n  },\n  "body": "first"\n}\n\n'    
        )

    def test_log_two_commits_detached(self):
        os.system("tinygit init >> /dev/null")
        os.system("tinygit commit first >> /dev/null")
        os.system("tinygit checkout-commit HEAD >> /dev/null")
        os.system("tinygit commit second >> /dev/null")
        out = subprocess.run(["tinygit", "log"], capture_output=True)
        self.assertEqual(
            out.stdout, 
            b'\x1b[95mcommit 44b9c372364f91cd4d0e7c84fee2d1ff27be295d\x1b[0m\n{\n  "headers": {\n    "tree": "01704555d3be59fda548e5524445e25b07c9b509",\n    "parent": "3e1a939bd3fd30ba3d114bedba0fb888183f0b20"\n  },\n  "body": "second"\n}\n\n\x1b[95mcommit 3e1a939bd3fd30ba3d114bedba0fb888183f0b20\x1b[0m\n{\n  "headers": {\n    "tree": "01704555d3be59fda548e5524445e25b07c9b509"\n  },\n  "body": "first"\n}\n\n'
        )
        

if __name__ == '__main__':
    unittest.main()