# AWS Linux 2023をベース
FROM public.ecr.aws/amazonlinux/amazonlinux:2023

# 基本パッケージのインストール
RUN yum update -y && \
    yum install --allowerasing -y \
    python3 \
    python3-pip \
    nodejs \
    npm \
    git \
    curl \
    wget \
    vim \
    tar \
    gzip \
    sed \
    grep \
    findutils \
    diffutils \
    xz \
    && yum clean all

# 作業ディレクトリを設定
WORKDIR /workspace

# デフォルトシェルを設定
CMD ["/bin/bash"]
