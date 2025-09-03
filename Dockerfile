FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY requirements.txt .

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 4201

# 设置环境变量
ENV PYTHONPATH=/app
ENV FLASK_APP=app.py

# 启动命令
CMD ["gunicorn", "--bind", "0.0.0.0:4201", "--workers", "4", "--timeout", "120", "app:app"]
