# 企业微信机器人配置指南

## 第一步：创建企业微信应用

1. 登录企业微信管理后台: https://work.weixin.qq.com/
2. 进入"应用管理" -> "自建" -> "创建应用"
3. 填写应用信息：
   - 应用名称：例如"AI助手"
   - 应用介绍：AI智能回复机器人
   - 应用logo：上传一个图标

## 第二步：配置应用接收消息

1. 在应用详情页面，点击"接收消息"
2. 配置服务器信息：
   - **URL**: `https://你的域名/wechat/callback` 
   - **Token**: 自定义，例如：`MyWechatBot2024`
   - **EncodingAESKey**: 点击"随机生成"或自定义43位字符
3. 保存配置

## 第三步：获取应用信息

在应用详情页面记录以下信息：
- **企业ID** (CorpId): 在"我的企业" -> "企业信息"中查看
- **应用AgentId**: 在应用详情页面查看
- **应用Secret**: 在应用详情页面查看（需要管理员权限）

## 第四步：配置环境变量

1. 复制 `.env.example` 为 `.env`：
```bash
cp .env.example .env
```

2. 编辑 `.env` 文件，填入实际配置：
```env
# 企业微信配置
WECHAT_CORP_ID=ww1234567890abcdef     # 企业ID
WECHAT_SECRET=ABC123def456GHI789      # 应用Secret
WECHAT_AGENT_ID=1000001               # 应用AgentId
WECHAT_TOKEN=MyWechatBot2024          # 自定义Token
WECHAT_ENCODING_AES_KEY=ABC123def456GHI789jkl012MNO345pqr678STU90v # 43位字符

# 大模型配置
OPENAI_API_KEY=sk-1234567890abcdef    # OpenAI API密钥
OPENAI_BASE_URL=https://api.openai.com/v1  # API基础URL
```

## 第五步：安装依赖和启动服务

1. 安装Python依赖：
```bash
pip install -r requirements.txt
```

2. 启动服务：
```bash
python run.py
```

服务将在 http://localhost:5000 启动

## 第六步：配置内网穿透（开发环境）

如果在本地开发，需要使用内网穿透工具让企业微信能访问到你的服务：

### 使用 ngrok
```bash
# 安装 ngrok
# 启动穿透
ngrok http 5000

# 获取公网URL，例如: https://abc123.ngrok.io
```

### 使用 frp
```bash
# 配置 frp 客户端
# 获取公网URL
```

## 第七步：企业微信URL验证

1. 将内网穿透得到的公网URL填入企业微信应用配置
   - 例如：`https://abc123.ngrok.io/wechat/callback`
2. 点击"保存"，企业微信会进行URL验证
3. 如果验证成功，状态会显示"已启用"

## 第八步：测试功能

1. 在企业微信中找到你创建的应用
2. 发送文本消息测试
3. 查看服务器日志，应该能看到：
   - 接收到消息
   - 调用大模型
   - 发送回复

## 常见问题排查

### 1. URL验证失败
- 检查Token和EncodingAESKey是否正确
- 确认服务器可以访问
- 查看服务器日志的错误信息

### 2. 收不到消息
- 确认应用在企业微信中可见
- 检查应用权限设置
- 验证用户是否在应用的可见范围内

### 3. 消息解密失败
- 检查EncodingAESKey格式（必须43位）
- 确认企业ID配置正确
- 检查消息加密设置

### 4. 无法发送回复
- 验证Secret是否正确
- 检查应用是否有发送消息权限
- 确认access_token获取成功

### 5. 大模型调用失败
- 检查API密钥有效性
- 验证网络连接
- 确认API配额和费用

## 生产环境部署

### 使用 Docker
```bash
# 构建镜像
docker build -t wechat-bot .

# 运行容器
docker-compose up -d
```

### 使用 systemd (Linux)
创建服务文件 `/etc/systemd/system/wechat-bot.service`：
```ini
[Unit]
Description=Wechat Bot Service
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/your/app
Environment=PATH=/path/to/your/venv/bin
ExecStart=/path/to/your/venv/bin/gunicorn --bind 0.0.0.0:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

启动服务：
```bash
sudo systemctl enable wechat-bot
sudo systemctl start wechat-bot
```

### 反向代理配置 (Nginx)
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

## 安全建议

1. 使用HTTPS协议
2. 定期轮换API密钥
3. 限制服务器访问权限
4. 启用日志记录和监控
5. 定期更新依赖包

## 支持的消息类型

当前版本支持：
- ✅ 文本消息
- ❌ 图片消息（显示提示）
- ❌ 语音消息（显示提示）
- ❌ 文件消息（暂不支持）

## 扩展功能

可以基于此项目扩展：
- 多轮对话记忆
- 图片识别功能
- 语音转文字
- 文件处理
- 自定义指令
- 数据库存储
- 用户管理

## 技术支持

如果遇到问题，请检查：
1. 服务器日志输出
2. 企业微信管理后台的错误提示
3. 网络连接状态
4. 配置参数的正确性
