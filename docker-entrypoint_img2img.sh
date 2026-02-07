#!/bin/bash
set -ue
shopt -s nullglob

export TZ=${TZ:-Asia/Tokyo}

if [ -z "${SAKURA_ARTIFACT_DIR:-}" ]; then
      	echo "Environment variable SAKURA_ARTIFACT_DIR is not set" >&2
      	exit 1
fi

if [ -z "${SAKURA_TASK_ID:-}" ]; then
      	echo "Environment variable SAKURA_TASK_ID is not set" >&2
	exit 1
fi

if [ -z "${PROMPT:-}" ]; then
      	echo "Environment variable PROMPT is not set" >&2
	exit 1
fi

pushd /cyberrealisticpony

python3 runner_img2img.py \
  --height="${HEIGHT:-1152}" \
  --output="${SAKURA_ARTIFACT_DIR}" \
  --prompt="${PROMPT}" \
  --s3-bucket="${S3_BUCKET:-}" \
  --s3-endpoint="${S3_ENDPOINT:-}" \
  --s3-secret="${S3_SECRET:-}" \
  --s3-token="${S3_TOKEN:-}" \
  --steps="${STEPS:-20}" \
  --strength="${STRENGTH:-0.75}" \
  --width="${WIDTH:-896}"
popd
