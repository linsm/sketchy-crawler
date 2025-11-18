#!/bin/bash

repo_path="$1"

cd "$repo_path" 
dependencies=$(cargo tree --prefix none | sort | uniq | wc -l)
echo "$dependencies"