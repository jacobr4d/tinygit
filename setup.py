from setuptools import setup

setup(
	name='tinygit',
	version='0.0.1',
  packages=['tinygit'],
  python_requires='>=3.8',
  entry_points={
    'console_scripts': [
      'tinygit=tinygit.cli:main'
    ]
  },
)
