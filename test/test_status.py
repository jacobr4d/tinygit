import unittest
import tempfile
import shutil
import os
import subprocess

class TestStatus(unittest.TestCase):
    def setUp(self):
        # Create a tmp directory before all tests
        self.test_dir = tempfile.mkdtemp()
        os.chdir(self.test_dir)

    def tearDown(self):
        # Remove tmp directory after the tests
        shutil.rmtree(self.test_dir)

    # def test_not_a_repo(self):
    #     result = subprocess.run(["tinygit", "status"], capture_output=True)
    #     self.assertEqual(result.returncode, 1)
    #     self.assertIn(b"Not a tinygit repository (or any of the parent directories)", result.stdout)

    # def test_master(self):
    #     os.system("tinygit init >> /dev/null")
    #     result = subprocess.run(["tinygit", "status"], capture_output=True)
    #     self.assertEqual(result.returncode, 0)
    #     self.assertIn(b"On branch refs/heads/master", result.stdout)

    # def test_other_branch(self):
    #     os.system("tinygit init >> /dev/null")
    #     os.system("tinygit commit first >> /dev/null")
    #     os.system("tinygit branch somebranch >> /dev/null")
    #     os.system("tinygit checkout somebranch >> /dev/null")
    #     result = subprocess.run(["tinygit", "status"], capture_output=True)
    #     self.assertEqual(result.returncode, 0)
    #     self.assertIn(b"On branch refs/heads/somebranch", result.stdout)

if __name__ == '__main__':
    unittest.main()