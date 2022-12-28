import unittest
import tempfile
import shutil
import os
import subprocess

class TestInit(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        os.chdir(self.test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_init_loc_not_a_dir(self):
        os.system("touch a.txt")
        result = subprocess.run(["tinygit", "init", "a.txt"], capture_output=True)
        self.assertEqual(result.returncode, 1)

    def test_init_loc_already_a_repo(self):
        os.system("tinygit init >> /dev/null")
        result = subprocess.run(["tinygit", "init"], capture_output=True)
        self.assertEqual(result.returncode, 1)

    def test_init(self):
        os.system("tinygit init >> /dev/null")
        out = subprocess.run(["ls", "-a"], capture_output=True)
        self.assertIn(b".git", out.stdout)

if __name__ == '__main__':
    unittest.main()