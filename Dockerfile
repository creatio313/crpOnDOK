FROM nvidia/cuda:12.8.1-runtime-ubuntu24.04
ENV DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8
ENV PIP_BREAK_SYSTEM_PACKAGES=1
RUN apt-get update && \
    apt-get install -y \
        git \
        ca-certificates \
        curl \
        python3 \
        python3-pip \
        libgl1 \
        libglib2.0-0 \
      && \
    pip install torch torchvision --index-url https://download.pytorch.org/whl/cu128 && \
    pip install git+https://github.com/huggingface/diffusers@main && \
    pip install \
        accelerate \
        safetensors \
        transformers \
        invisible_watermark \
        omegaconf \
        pillow \
        numpy \
        boto3 \
      && \
    pip cache purge && \
    mkdir /cyberrealisticpony /opt/artifact && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /cyberrealisticpony

RUN curl -L "https://civitai.com/api/download/models/2469412?type=Model&format=SafeTensor&size=pruned&fp=fp16&token=アクセストークンに置換" \
         -o /cyberrealisticpony/cyberrealisticPony_v150.safetensors

COPY runner.py /cyberrealisticpony/
COPY docker-entrypoint*.sh /
RUN chmod +x /docker-entrypoint*.sh /

WORKDIR /
CMD ["/bin/bash", "/docker-entrypoint.sh"]