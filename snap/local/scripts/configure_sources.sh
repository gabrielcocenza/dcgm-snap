#!/bin/bash

DISTRIBUTION="ubuntu2404"
SYSTEM_ARCH=$(uname -m)
# package that configures the apt source
CUDA_PKG="cuda-keyring_1.1-1_all.deb"

if [ "$SYSTEM_ARCH" = "aarch64" ]; then
    ARCH="sbsa"
    SHA256SUM="6ea7d2737648936820e85677177957a0f6521b840d98eb0bbae0a4f003fa7249"
elif [ "$SYSTEM_ARCH" = "x86_64" ]; then
    ARCH="x86_64"
    SHA256SUM="d2a6b11c096396d868758b86dab1823b25e14d70333f1dfa74da5ddaf6a06dba"
else
    echo "Unsupported architecture: $SYSTEM_ARCH"
    exit 1
fi


echo "Architecture is $SYSTEM_ARCH. Downloading cuda-keyring package..."
curl --remote-name "https://developer.download.nvidia.com/compute/cuda/repos/$DISTRIBUTION/$ARCH/$CUDA_PKG"

# Run the checksum verification and install cuda-keyring if valid
if echo "$SHA256SUM  $CUDA_PKG" | sha256sum --check --status; then
    echo "Checksum for $CUDA_PKG is correct."
    dpkg -i $CUDA_PKG
    apt-get update
else
    echo "Checksum for $CUDA_PKG is incorrect."
    exit 1
fi
