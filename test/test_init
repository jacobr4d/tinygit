import unittest
import tempfile
import shutil
import os
import subprocess

class TestInit(unittest.TestCase):
    def setUp(self):
        # Create a tmp directory before all tests
        self.test_dir = tempfile.mkdtemp()
        os.chdir(self.test_dir)

    def tearDown(self):
        # Remove tmp directory after the tests
        shutil.rmtree(self.test_dir)

    def test_workdir_not_a_dir(self):
        os.system("touch somefile")
        result = subprocess.run(["tinygit", "init", "somefile"], capture_output=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn(b"is not a directory", result.stdout)

    def test_already_exists(self):
        os.system("tinygit init >> /dev/null")
        result = subprocess.run(["tinygit", "init"], capture_output=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn(b"already contains a tinygit repository", result.stdout)

    def test_simple(self):
        os.system("tinygit init >> /dev/null")
        result = subprocess.run(["ls", "-a"], capture_output=True)
        self.assertIn(b".git", result.stdout)


if __name__ == '__main__':
    unittest.main()