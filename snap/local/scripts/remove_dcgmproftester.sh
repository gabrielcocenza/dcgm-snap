#!/bin/bash


FILES_TO_REMOVE=(
    "dcgmproftester*"
    "libdcgm_cublas_proxy*"
)


echo "Removing dcgmproftester files"


for pattern in "${FILES_TO_REMOVE[@]}"; do
    find "$SNAPCRAFT_PRIME" -type f -name "$pattern" | while read -r file; do
        echo "Removing file $file"
        rm -f "$file"
    done
done


echo "Removing cuda directories"
find "$SNAPCRAFT_PRIME" -type d -name "cuda[0-9]*" | while read -r dir; do
    echo "Removing directory $dir"
    rm -rf "$dir"
done

echo "Finished cleanup"
