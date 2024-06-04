#!/bin/bash

# Create a temporary writable directory for apt lists
mkdir -p /tmp/apt/lists/partial

# Bind mount the temporary directory to the apt lists directory
mount --bind /tmp/apt/lists /var/lib/apt/lists

# Update the apt package list and install the required packages
apt-get update
apt-get install -y poppler-utils ghostscript swig

# Clean up
umount /var/lib/apt/lists
rm -rf /tmp/apt
