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
        # Remove tmp directory after the tests
        shutil.rmtree(self.test_dir)

    # def test_no_repo(self):
    #     result = subprocess.run(["tinygit", "log"], capture_output=True)
    #     self.assertIn(b"Not a tinygit repository (or any of the parent directories)", result.stdout)
    #     self.assertEqual(result.returncode, 1)

    # def test_no_commits(self):
    #     os.system("tinygit init >> /dev/null")
    #     result = subprocess.run(["tinygit", "log"], capture_output=True)
    #     self.assertIn(b"Your current branch does not have any commits yet", result.stdout)
    #     self.assertEqual(result.returncode, 1)

    # def test_bad_commit(self):
    #     os.system("tinygit init >> /dev/null")
    #     os.system("echo hello world > somefile")
    #     os.system("tinygit commit first >> /dev/null")
    #     result = subprocess.run(["tinygit", "log", "f1009bb7524f542ec70ab959af15bdf5ce1d3dc9"], capture_output=True)
    #     self.assertIn(b"Commitish 'f1009bb7524f542ec70ab959af15bdf5ce1d3dc9' did not match any commits known to tinygit", result.stdout)
    #     self.assertEqual(result.returncode, 1)

    # def test_one_commit(self):
    #     os.system("tinygit init >> /dev/null")
    #     os.system("echo hello world > somefile")
    #     os.system("tinygit commit first >> /dev/null")
    #     result = subprocess.run(["tinygit", "log"], capture_output=True)
    #     self.assertIn(b"commit e1009bb7524f542ec70ab959af15bdf5ce1d3dc9", result.stdout)
    #     self.assertIn(b"first", result.stdout)

    # def test_two_commits(self):
    #     os.system("tinygit init >> /dev/null")
    #     os.system("tinygit commit first >> /dev/null")
    #     os.system("echo hello world > somefile")
    #     os.system("tinygit commit second >> /dev/null")
    #     result = subprocess.run(["tinygit", "log"], capture_output=True)
    #     self.assertIn(b"commit fbda78878bd67c2aa802629536b98bce329abe9b", result.stdout)
    #     self.assertIn(b"second", result.stdout)
    #     self.assertIn(b"commit 3e1a939bd3fd30ba3d114bedba0fb888183f0b20", result.stdout)
    #     self.assertIn(b"first", result.stdout)


if __name__ == '__main__':
    unittest.main()