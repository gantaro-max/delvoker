# Python 3.11の公式Dev Containerイメージを使用
FROM mcr.microsoft.com/devcontainers/python:3.11

# コンテナのOSにPyxel用のライブラリ、Git、およびNode.jsをインストールするための準備
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends \
    libsdl2-2.0-0 \
    libsdl2-image-2.0-0 \
    libgl1 \
    libegl1 \
    xvfb \
    git \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean -y \
    && rm -rf /var/lib/apt/lists/*

# pipのアップデートとPyxelのインストール
RUN pip install --upgrade pip
RUN pip install pyxel

# Claude Codeのグローバルインストール
RUN npm install -g @anthropic-ai/claude-code