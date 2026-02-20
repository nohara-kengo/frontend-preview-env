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

# Node.js/npm のバージョン確認
RUN node --version && npm --version && python3 --version

# Python 仮想環境の作成
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# requirements.txt をコピーして依存関係をインストール
COPY requirements.txt /tmp/
RUN pip install --upgrade pip && \
    pip install -r /tmp/requirements.txt

# AWS CDK CLI のインストール
RUN npm install -g aws-cdk

# 作業ディレクトリを設定
WORKDIR /workspace

# 初期化スクリプトをコピー
COPY entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/entrypoint.sh

# entrypoint を設定
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

# デフォルトシェルを設定
CMD ["/bin/bash"]
