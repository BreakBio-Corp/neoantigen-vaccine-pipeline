#!/bin/bash

# This script will build the public Docker image, tagging it as latest.

set -ex

# docker hub username
USERNAME=359343221949.dkr.ecr.us-east-2.amazonaws.com
IMAGE_TAG=d0.4.3-el-cut-off-99
# image name
IMAGE=neoantigen-vaccine-pipeline
# directory of this script
BASEDIR=$(dirname "$0")

# Build image
docker build -t $USERNAME/$IMAGE:$IMAGE_TAG -f $BASEDIR/docker/Dockerfile .
