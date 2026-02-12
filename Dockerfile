FROM nvidia/cuda:12.8.1-runtime-ubuntu24.04
LABEL jp.sakuracr.t-shirotani-airepo.version="1.0.0"
LABEL jp.sakuracr.t-shirotani-airepo.release-date="2026-02-12"
ENV DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8
ENV PIP_BREAK_SYSTEM_PACKAGES=1

# 依存関係のインストール。diffusersは最新Pipeline対応版をソースからインストール。
RUN apt-get update && \
    apt-get install -y \
        git \
        ca-certificates \
        curl \
        python3 \
        python3-pip \
        libgl1 \
        libglib2.0-0 && \
    rm -rf /var/lib/apt/lists/* && \
    pip install torch torchvision --index-url https://download.pytorch.org/whl/cu128 && \
    pip install git+https://github.com/huggingface/diffusers@main && \
    pip install \
        accelerate \
        boto3 \
        invisible_watermark \
        numpy \
        omegaconf \
        pillow \
        safetensors \
        transformers \
      && \
    pip cache purge && \
    mkdir /cyberrealisticpony /opt/artifact

WORKDIR /cyberrealisticpony

RUN curl -L "https://civitai.com/api/download/models/2469412?type=Model&format=SafeTensor&size=pruned&fp=fp16&token=4a9b58ac4042e7f623a5d5c9b85fb414" \
         -o /cyberrealisticpony/cyberrealisticPony_v150.safetensors

COPY runner*.py /cyberrealisticpony/
COPY docker-entrypoint*.sh /
RUN chmod +x /docker-entrypoint*.sh /

WORKDIR /
ENTRYPOINT ["/docker-entrypoint.sh"]