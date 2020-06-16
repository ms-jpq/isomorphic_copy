#!/usr/bin/env bash

set -eu
set -o pipefail
cd "$(dirname "$0")" || exit 1


RELEASE="$1"
IMAGE="msjpq/isomorphic-copy:$RELEASE"


docker build -t "$IMAGE" . -f "docker/$RELEASE/Dockerfile"


if [[ $# -gt 1 ]]
then
  docker push "$IMAGE"
fi

