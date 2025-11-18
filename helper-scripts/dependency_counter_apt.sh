#!/bin/bash

package="$1"

build_dependencies=$(apt-rdepends -b "$package"  2>/dev/null | sed -n '/Build-Depends/p' | head -n 100 | sort -u | wc -l)
package_dependencies=$(apt-rdepends "$package" 2>/dev/null | sed 's/^  Depends: //;s/ (.*)$//' | sort -u | wc -l)
reverese_dependencies=$(apt-rdepends -r "$package" 2>/dev/null | sed 's/^  Reverse Depends: //;s/ (.*)$//' | sort -u | wc -l)

echo "$build_dependencies $package_dependencies $reverese_dependencies"
