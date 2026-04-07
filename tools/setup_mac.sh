#!/bin/bash
# Mac 一键部署脚本

set -e

echo "================================"
echo "  Slide-to-Video Mac 部署脚本"
echo "================================"

# 检测架构
ARCH=$(uname -m)
echo "检测到架构: $ARCH"

# 1. 安装 Homebrew（如未安装）
if ! command -v brew &> /dev/null; then
    echo "安装 Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
else
    echo "Homebrew 已安装 ✓"
fi

# 2. 安装 FFmpeg
echo ""
echo "安装 FFmpeg..."
brew install ffmpeg-full

# 3. 设置模型目录
echo ""
echo "配置模型目录..."
MODEL_DIR="$HOME/models/tts"
mkdir -p "$MODEL_DIR"

# 添加环境变量到 shell 配置
SHELL_RC=""
if [ -f "$HOME/.zshrc" ]; then
    SHELL_RC="$HOME/.zshrc"
elif [ -f "$HOME/.bashrc" ]; then
    SHELL_RC="$HOME/.bashrc"
fi

if [ -n "$SHELL_RC" ]; then
    if ! grep -q "TTS_HOME" "$SHELL_RC"; then
        echo "" >> "$SHELL_RC"
        echo "# TTS 模型路径" >> "$SHELL_RC"
        echo "export TTS_HOME=\"\$HOME/models/tts\"" >> "$SHELL_RC"
        echo "已添加环境变量到 $SHELL_RC"
    else
        echo "环境变量已存在 ✓"
    fi
fi

export TTS_HOME="$MODEL_DIR"

# 4. 创建 Python 虚拟环境
echo ""
echo "创建 Python 虚拟环境..."
cd "$(dirname "$0")/.."
python3 -m venv .venv
source .venv/bin/activate

# 5. 安装项目
echo ""
echo "安装项目依赖..."
pip install --upgrade pip
pip install .

# 6. 预下载常用 TTS 模型（可选）
echo ""
read -p "是否预下载 TTS 模型？(y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "下载多语言 TTS 模型..."
    python -c "from TTS.api import TTS; TTS(model_name='tts_models/multilingual/multi-dataset/xtts_v2', progress_bar=True)"
fi

# 7. 验证安装
echo ""
echo "================================"
echo "验证安装..."
echo "================================"
slide-to-video --help

echo ""
echo "✅ 部署完成!"
echo ""
echo "模型目录: $MODEL_DIR"
echo "项目目录: $(pwd)"
echo ""
echo "使用方式:"
echo "  source .venv/bin/activate"
echo "  slide-to-video --config config.yaml"
