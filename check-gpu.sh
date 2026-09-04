#!/bin/sh
# Why is the GPU not being used? Walks the chain and stops at the first break.
#
#   ./check-gpu.sh
#
# There are four links, and all four have to hold: the driver has to see the
# card, Docker has to be able to hand it over, the ollama container has to have
# been started with it, and Ollama has to have actually loaded a model onto it.

cd "$(dirname "$0")"
echo

# 1 -------------------------------------------------------------------------
printf '1. Driver: '
if ! command -v nvidia-smi > /dev/null 2>&1; then
    echo "no nvidia-smi on this machine."
    echo "   There is no NVIDIA driver here, so nothing else can work."
    exit 1
fi
card=$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -1)
if [ -z "$card" ]; then
    echo "nvidia-smi is installed but reports no card."
    exit 1
fi
echo "$card"

# 2 -------------------------------------------------------------------------
printf '2. Docker can reach the card: '
if docker run --rm --gpus all ubuntu nvidia-smi -L > /dev/null 2>&1; then
    echo "yes"
else
    echo "NO"
    echo "   The card is there but Docker cannot pass it through, which means"
    echo "   the NVIDIA container toolkit is missing or not registered:"
    echo "     https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html"
    echo "     sudo nvidia-ctk runtime configure --runtime=docker"
    echo "     sudo systemctl restart docker"
    exit 1
fi

# 3 -------------------------------------------------------------------------
printf '3. The running ollama container was given it: '
container=$(docker compose ps -q ollama 2>/dev/null)
if [ -z "$container" ]; then
    echo "the ollama container is not running."
    echo "   Start the stack with ./start.sh"
    exit 1
fi
if docker inspect "$container" \
    --format '{{json .HostConfig.DeviceRequests}}' 2>/dev/null | grep -q nvidia; then
    echo "yes"
else
    echo "NO"
    echo "   It is running without a GPU reservation, which is what happens"
    echo "   after a plain 'docker compose up'. Recreate it with:"
    echo "     ./start.sh"
    echo "   or: docker compose -f docker-compose.yml -f docker-compose.gpu.yml up -d"
    exit 1
fi

# 4 -------------------------------------------------------------------------
printf '4. Ollama sees the card: '
if docker compose exec -T ollama nvidia-smi -L > /dev/null 2>&1; then
    echo "yes"
else
    echo "NO — the reservation is there but nvidia-smi fails inside the container."
    exit 1
fi

echo
echo "All four hold. To see which processor a model actually loads onto, run a"
echo "matching task and then, while it is running:"
echo
echo "    docker compose exec ollama ollama ps"
echo
echo "The PROCESSOR column says 100% GPU when the card is being used, 100% CPU"
echo "when it is not, and a split such as 40%/60% CPU/GPU when the model is too"
echo "large for the card's memory and only part of it fits."
echo
