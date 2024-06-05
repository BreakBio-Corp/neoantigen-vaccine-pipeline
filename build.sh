#!/bin/bash -e

AWS_PROFILE=${1:-"default"}
VERSION_TAG=${2:-$(date -u +%Y%m%d%H%M)}
#VERSION_TAG=${2:-$("mhcii-longer-peptides")}
IMAGE_NAME="neoantigen-vaccine-pipeline"
DOCKER_REGISTRY="359343221949.dkr.ecr.us-east-2.amazonaws.com"

function run_info() {
    IMAGE_NAME=${1}
    VERSION_TAG=${2:-$(date -u +%Y%m%d%H%M)}
    echo "=================================================="
    echo "  Run locally:"
    echo "  docker run ${IMAGE_NAME}:${VERSION_TAG}"
    echo "=================================================="
}

function build_image() {
    IMAGE_NAME=${1}
    VERSION_TAG=${2:-$(date -u +%Y%m%d%H%M)}

    echo "BUILDING: ${IMAGE_NAME}"
    DOCKER_TAG="${DOCKER_REGISTRY}/${IMAGE_NAME}:${VERSION_TAG}"
    docker build --platform linux/amd64 --no-cache --rm=true --file="docker/Dockerfile" --tag ${IMAGE_NAME}:${VERSION_TAG} .
    docker tag ${IMAGE_NAME}:${VERSION_TAG} ${DOCKER_TAG}
    RET=$?;
    [[ $RET -ne 0 ]] && exit $RET

    echo "Docker build was successful..."
}

function push_image() {
    local IMAGE_NAME=$1
    local VERSION_TAG=$2
    echo "PUSHING: $IMAGE_NAME:${VERSION_TAG}"
    aws ecr get-login-password --region us-east-2 --profile ${AWS_PROFILE} | docker login --username AWS --password-stdin ${DOCKER_REGISTRY}
    DOCKER_TAG="${DOCKER_REGISTRY}/${IMAGE_NAME}:${VERSION_TAG}"
    docker push ${DOCKER_TAG}
}

echo "Building image... "
build_image ${IMAGE_NAME} ${VERSION_TAG}
push_image ${IMAGE_NAME} ${VERSION_TAG}
run_info ${IMAGE_NAME} ${VERSION_TAG}
