#!/bin/bash

git_ignore="$1"
sketchy_files="$2"

IFS=',' read -r -a files <<< "$sketchy_files"

count=0
for file in "${files[@]}"; do
    count=$((count + $(grep -o "$file" "$git_ignore" | wc -l)))
done

echo "$count"