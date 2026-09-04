#!/bin/sh
# Bring the stack up, using an NVIDIA GPU if this machine has a usable one.
#
#   ./start.sh                 start in the background
#   ./start.sh --build         rebuild the web image first
#   ./start.sh --cpu           ignore the GPU even if there is one
#
# Anything else is passed through to `docker compose up`.
#
# Two things have to be true before the GPU can be used: the driver has to see
# the card, and Docker has to be able to hand it over, which needs the NVIDIA
# container toolkit. The first is cheap to test with nvidia-smi. The second is
# not worth probing, because the honest test is the thing itself, so this
# starts with the GPU and falls back to the CPU if the daemon refuses. That
# makes a missing toolkit a message rather than a stack that will not start.

set -e
cd "$(dirname "$0")"

BASE="-f docker-compose.yml"
GPU="-f docker-compose.gpu.yml"

want_gpu=yes
args=""
for arg in "$@"; do
    if [ "$arg" = "--cpu" ]; then
        want_gpu=no
    else
        args="$args $arg"
    fi
done

if [ "$want_gpu" = no ]; then
    echo "Starting on the CPU, because --cpu was given."
    # shellcheck disable=SC2086
    exec docker compose $BASE up -d $args
fi

if ! command -v nvidia-smi > /dev/null 2>&1; then
    echo "No NVIDIA driver found, so the open models will run on the CPU."
    # shellcheck disable=SC2086
    exec docker compose $BASE up -d $args
fi

card=$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -1)
echo "Found ${card:-an NVIDIA GPU}. Starting with it."

# shellcheck disable=SC2086
if docker compose $BASE $GPU up -d $args; then
    exit 0
fi

echo
echo "Docker could not hand the GPU over, so the stack is starting on the CPU"
echo "instead. The card is there but the NVIDIA container toolkit is not:"
echo "  https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html"
echo "Install it and run this again to use the card."
echo
# shellcheck disable=SC2086
exec docker compose $BASE up -d $args
