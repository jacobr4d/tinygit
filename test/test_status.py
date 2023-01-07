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

    def test_status_not_a_repo(self):
        out = subprocess.run(["tinygit", "status"], capture_output=True)
        self.assertEqual(out.returncode, 1)

    def test_status_no_commits(self):
        os.system("tinygit init >> /dev/null")
        out = subprocess.run(["tinygit", "status"], capture_output=True)
        self.assertEqual(out.stdout, b'HEAD\n{\n  "type": "branch",\n  "id": "master"\n}\n\nNo commits yet\n')

    def test_status_working_clean(self):
        os.system("tinygit init >> /dev/null")
        os.system("tinygit commit 'empty project' >> /dev/null")
        out = subprocess.run(["tinygit", "status"], capture_output=True)
        self.assertIn(b"Nothing to commit", out.stdout)

    def test_status_modified(self):
        os.system("tinygit init >> /dev/null")
        os.system("echo 'a a a' > a")
        os.system("tinygit commit 'created a' >> /dev/null")
        os.system("echo 'b b b' > a")
        out = subprocess.run(["tinygit", "status"], capture_output=True)
        self.assertIn(b"Modified (\'file\', \'a\')", out.stdout)
    
    def test_status_added(self):
        os.system("tinygit init >> /dev/null")
        os.system("tinygit commit 'empty project' >> /dev/null")
        os.system("echo 'foo foo foo' > foo")
        out = subprocess.run(["tinygit", "status"], capture_output=True)
        self.assertIn(b"Added (\'file\', \'foo\')", out.stdout)

    def test_status_delted(self):
        os.system("tinygit init >> /dev/null")
        os.system("echo 'foo foo foo' > foo")
        os.system("tinygit commit 'created foo' >> /dev/null")
        os.system("rm foo")
        out = subprocess.run(["tinygit", "status"], capture_output=True)
        self.assertIn(b"Deleted (\'file\', \'foo\')", out.stdout)

if __name__ == '__main__':
    unittest.main()