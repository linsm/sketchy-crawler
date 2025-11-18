#!/bin/bash

IFS=','

awk '{print $1 "," $2 "," $3}' debian-popcon > test.csv

while read -r id package install
do
  if apt show "$package" 2>/dev/null | grep -q "Built-Using: rustc"; then
    echo "Package $package is built using Rust."
  fi
done < "test.csv"

rm test.csv

