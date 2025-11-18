#!/bin/bash

repository_url="$1"
repository_name="$2"
sketchy_files="$3"
sketchy_mime_types="$4"

printf "Cloning repository from %s\n" "$repository_url"
git clone $repository_url tmp/$repository_name
cd tmp || exit 1
printf "Finding sketchy files...\n"

IFS=',' read -r -a files <<< "$sketchy_files"

IFS=',' read -r -a mime_types <<< "$sketchy_mime_types"

count=0
total=0

# Find sketchy files
for file in "${files[@]}"; do
    ((total++))
    count=$((count + $(find . -type f -name "$file" | wc -l)))
done

# Find suspicious mime types
sketchy_mime_types=0

for file in $(find . -type f); do    
    for mime_type in "${mime_types[@]}"; do
        if file -b --mime-type "$file" | grep -q "$mime_type"; then
            ((sketchy_mime_types++))
        fi
    done
done

#rm -rf ../tmp

echo "Found $count sketchy files out of $total searched file names."
echo "Found $sketchy_mime_types sketchy mime types files."

echo "$count $sketchy_mime_types"