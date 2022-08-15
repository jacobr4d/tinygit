#!/bin/bash
rm -rf test
mkdir test
tinygit init test
echo foo foo foo > test/foo.c
echo bar bar bar > test/bar.c
mkdir test/baz
echo baz baz baz > test/baz/baz
