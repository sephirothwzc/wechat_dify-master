#!/bin/bash

echo "========================================"
echo "企业微信机器人大模型服务启动脚本"
echo "========================================"

# 检查Python版本
python_version=$(python3 --version 2>&1)
echo "Python版本: $python_version"

# 检查是否存在虚拟环境
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "激活虚拟环境..."
source venv/bin/activate

# 安装依赖
echo "安装依赖包..."
pip install -r requirements.txt

# 检查配置文件
if [ ! -f ".env" ]; then
    echo "⚠️  警告: 未找到 .env 配置文件"
    echo "请根据 README.md 创建 .env 文件并配置相关参数"
    echo ""
    echo "必需的配置项："
    echo "- WECHAT_CORP_ID: 企业ID"
    echo "- WECHAT_SECRET: 应用Secret"
    echo "- WECHAT_AGENT_ID: 应用AgentID"
    echo "- WECHAT_TOKEN: 消息验证Token"
    echo "- WECHAT_ENCODING_AES_KEY: 消息加密密钥"
    echo "- OPENAI_API_KEY: 大模型API密钥"
    echo ""
    read -p "是否继续启动服务？(y/n): " continue_start
    if [ "$continue_start" != "y" ]; then
        echo "启动已取消"
        exit 1
    fi
fi

echo "启动服务..."
echo "服务地址: http://localhost:4200"
echo "回调接口: http://localhost:4200/wechat/callback"
echo "健康检查: http://localhost:4200/health"
echo "========================================"

# 启动服务
python run.py
