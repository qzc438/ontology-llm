#!/bin/sh
# Bring the stack up, using an NVIDIA GPU if this machine has a usable one.
#
#   ./docker-start.sh                 start in the background
#   ./docker-start.sh --build         rebuild the web image first
#   ./docker-start.sh --cpu           ignore the GPU even if there is one
#
# Anything else is passed through to `docker compose up`.
#
# Two things have to be true before the GPU can be used: the driver has to see
# the card, and Docker has to be able to hand it over, which needs the NVIDIA
# container toolkit. The first is cheap to test with nvidia-smi. For the second
# this simply tries, because the real attempt is one command and its failure is
# recoverable, and falls back to the CPU rather than leaving the stack down.

set -e
cd "$(dirname "$0")"

# rebuild the argument list without --cpu, keeping quoted arguments intact
want_gpu=yes
for arg do
    shift
    if [ "$arg" = "--cpu" ]; then
        want_gpu=no
    else
        set -- "$@" "$arg"
    fi
done

if [ "$want_gpu" = no ]; then
    echo "Starting on the CPU, because --cpu was given."
elif ! command -v nvidia-smi > /dev/null 2>&1; then
    echo "No NVIDIA driver found, so the open models will run on the CPU."
else
    card=$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -1)
    echo "Found ${card:-an NVIDIA GPU}. Starting with it."

    # Output goes to the terminal as it happens, so a --build stays watchable,
    # and to a file as well so the failure can be classified afterwards.
    #
    # The status is carried out through a file because a pipeline reports the
    # exit status of its last command, which is tee's, and tee succeeds whatever
    # docker did. POSIX sh has no pipefail to lean on.
    log=$(mktemp)
    status=$(mktemp)
    trap 'rm -f "$log" "$status"' EXIT
    { docker compose -f docker-compose.yml -f docker-compose.gpu.yml \
        up -d "$@" 2>&1; echo $? > "$status"; } | tee "$log"
    [ "$(cat "$status")" = 0 ] && exit 0

    # Only the device-driver error means the toolkit is missing. Anything else,
    # a port already taken or a build that failed, is its own problem, and
    # saying "install the toolkit" would send the reader somewhere useless.
    if grep -q "could not select device driver" "$log"; then
        echo
        echo "The card is there but Docker cannot hand it over, which means the"
        echo "NVIDIA container toolkit is not installed. The Debian and Ubuntu"
        echo "steps are in DOCKER.md, \"Installing the NVIDIA container toolkit\";"
        echo "for any other distribution:"
        echo "  https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html"
        echo "Starting on the CPU instead."
        echo
    else
        echo
        echo "That failure is not about the GPU, so starting without the card is"
        echo "unlikely to help. Fix it and run this again." >&2
        echo
        exit 1
    fi
fi

exec docker compose -f docker-compose.yml up -d "$@"
