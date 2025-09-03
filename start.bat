@echo off
chcp 65001
cls

echo ========================================
echo 企业微信机器人大模型服务启动脚本
echo ========================================

REM 检查Python版本
python --version
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python 3.7+
    pause
    exit /b 1
)

REM 检查是否存在虚拟环境
if not exist "venv" (
    echo 创建虚拟环境...
    python -m venv venv
)

REM 激活虚拟环境
echo 激活虚拟环境...
call venv\Scripts\activate.bat

REM 安装依赖
echo 安装依赖包...
pip install -r requirements.txt

REM 检查配置文件
if not exist ".env" (
    echo.
    echo ⚠️  警告: 未找到 .env 配置文件
    echo 请根据 README.md 创建 .env 文件并配置相关参数
    echo.
    echo 必需的配置项：
    echo - WECHAT_CORP_ID: 企业ID
    echo - WECHAT_SECRET: 应用Secret
    echo - WECHAT_AGENT_ID: 应用AgentID
    echo - WECHAT_TOKEN: 消息验证Token
    echo - WECHAT_ENCODING_AES_KEY: 消息加密密钥
    echo - OPENAI_API_KEY: 大模型API密钥
    echo.
    set /p continue_start="是否继续启动服务？(y/n): "
    if not "%continue_start%"=="y" (
        echo 启动已取消
        pause
        exit /b 1
    )
)

echo 启动服务...
echo 服务地址: http://localhost:5000
echo 回调接口: http://localhost:5000/wechat/callback
echo 健康检查: http://localhost:5000/health
echo ========================================

REM 启动服务
python run.py

pause
