#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置文件
"""

import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Config:
    """应用配置类"""
    
    # Flask配置
    FLASK_HOST = '0.0.0.0'
    FLASK_PORT = int(os.getenv('PORT', 4201))
    FLASK_DEBUG = True
    
    # 企业微信配置
    WECHAT_TOKEN = os.getenv('WECHAT_TOKEN', '')
    WECHAT_ENCODING_AES_KEY = os.getenv('WECHAT_ENCODING_AES_KEY', '')
    WECHAT_CORP_ID = os.getenv('WECHAT_CORP_ID', '')
    
    # 大模型配置
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', 'sk-')
    OPENAI_BASE_URL = os.getenv('OPENAI_BASE_URL', 'https://dashscope.aliyuncs.com/compatible-mode/v1')
    OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'qwen-plus-latest')
    
    # LLM Demo配置
    LLM_CACHE_DIR = os.path.join(os.getcwd(), "llm_demo_cache")
    LLM_MAX_STEPS = int(os.getenv('LLM_MAX_STEPS', 2))
    
    # Redis配置
    REDIS_HOST = os.getenv('REDIS_HOST', '')
    REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
    REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', '')
    REDIS_DB = int(os.getenv('REDIS_DB', 1))
    
    # MySQL配置
    MYSQL_HOST = os.getenv('MYSQL_HOST', '')
    MYSQL_PORT = int(os.getenv('MYSQL_PORT', 3306))
    MYSQL_USER = os.getenv('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '')
    MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', '')
    
    # 认证服务配置
    AUTH_SERVICE_URL = os.getenv('AUTH_SERVICE_URL', '')
    
    # Dify配置
    DIFY_BASE_URL = os.getenv('DIFY_BASE_URL', '')
    DIFY_CHAT_ENDPOINT = os.getenv('DIFY_CHAT_ENDPOINT', '/v1/chat-messages')
    DIFY_AUTH_PREFIX = os.getenv('DIFY_AUTH_PREFIX', '')

# 创建配置实例
config = Config()
