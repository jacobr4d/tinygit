#!/bin/bash
rm -rf tmp
mkdir tmp
tinygit init tmp
echo foo foo foo > tmp/foo.c
echo bar bar bar > tmp/bar.c
mkdir tmp/baz
echo baz baz baz > tmp/baz/baz
