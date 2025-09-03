#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
企业微信机器人服务启动脚本
"""

import os
from app import app

if __name__ == '__main__':
    # 从环境变量获取配置
    debug = os.getenv('DEBUG', 'True').lower() == 'true'
    port = int(os.getenv('PORT', 5000))
    
    print("=" * 50)
    print("企业微信机器人大模型服务")
    print("=" * 50)
    print(f"服务端口: {port}")
    print(f"调试模式: {debug}")
    print(f"回调接口: http://localhost:{port}/wechat/callback")
    print(f"健康检查: http://localhost:{port}/health")
    print("=" * 50)
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )
