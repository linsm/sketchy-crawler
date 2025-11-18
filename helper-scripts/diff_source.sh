#!/bin/bash

repository_owner="$1"
repository_name="$2"
release_tag="$3"

tarball_directory="$repository_name"-source
mkdir -p "tmp/$tarball_directory"
tarball="https://github.com/$repository_owner/$repository_name/archive/refs/tags/v$release_tag.tar.gz"

cd "tmp"
if wget -q "$tarball"; then
    release_tag=v$release_tag
else
    tarball="https://github.com/$repository_owner/$repository_name/archive/refs/tags/$release_tag.tar.gz"
    wget -q "$tarball"
fi

tar -xf "$release_tag.tar.gz" -C "$tarball_directory" >/dev/null 2>&1

#directory_name=""
#if $(find * -maxdepth 0 -type d | wc -l) -eq 1; then
#    directory_name="/"$(ls -d *)
#    echo $directory_name
#fi

cd $repository_name && git checkout tags/$release_tag >/dev/null 2>&1 && cd ..
differences=$(diff $repository_name $repository_name-source | grep "Only in" | wc -l)
echo "$differences"