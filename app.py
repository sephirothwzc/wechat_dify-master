#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
企业微信机器人接口服务
接收企业微信消息，调用大模型，返回响应
"""

import json
import time
import random
from flask import Flask, request, jsonify, Response

# 导入配置和服务
from config.settings import config
from services.wechat_service import WechatBotService
from models.llm_demo import LLMDemo
from utils.stream_utils import MakeTextStream, EncryptMessage

app = Flask(__name__)

# 初始化服务
wechat_service = WechatBotService()

@app.route('/wechat/callback', methods=['GET', 'POST'])
# @app.route('/wechat/callback/<code>', methods=['GET', 'POST'])
# def wechat_callback(code):
def wechat_callback():
    """企业微信回调接口"""
    # code = 'default'

    if request.method == 'GET':
        # URL验证
        msg_signature = request.args.get('msg_signature', '')
        timestamp = request.args.get('timestamp', '')
        nonce = request.args.get('nonce', '')
        echostr = request.args.get('echostr', '')
        
        print(f"URL验证请求: msg_signature={msg_signature}, timestamp={timestamp}, nonce={nonce}, echostr={echostr}")
        
        # 企业微信使用 msg_signature 参数
        success, reply = wechat_service.verify_signature(msg_signature, timestamp, nonce, echostr)
        
        if success:
            print("URL验证成功")
            return reply
        else:
            print("URL验证失败")
            return 'URL验证失败', 500
    
    elif request.method == 'POST':
        # 处理消息
        msg_signature = request.args.get('msg_signature', '')
        timestamp = request.args.get('timestamp', '')
        nonce = request.args.get('nonce', '')
        
        try:
            # 获取加密的消息数据
            encrypt_msg = request.data
            print(f"收到原始消息数据: {encrypt_msg[:200]}...", flush=True)
            print(f"消息数据类型: {type(encrypt_msg)}", flush=True)
            print(f"消息数据长度: {len(encrypt_msg)}", flush=True)
            
            # 解密消息
            success, decrypted_msg = wechat_service.decrypt_message(
                msg_signature, timestamp, nonce, encrypt_msg
            )
            
            if not success:
                print("消息解密失败", flush=True)
                return 'Decryption failed', 400
            
            print(f"解密后的消息: {decrypted_msg}", flush=True)
            
            # 解析消息
            message_info = wechat_service.parse_message(decrypted_msg)
            if not message_info:
                print("消息解析失败", flush=True)
                return 'Parse failed', 400
            
            print(f"解析后的消息信息: {message_info}", flush=True)
            from_user = message_info["from_user"]
            msgtype = message_info['msg_type']
            stream_id = message_info.get('stream_id', '')

            
            if msgtype == 'text' and message_info['content']:
                # 文本消息处理 - 启动思考流程
                content = message_info['content']
                print(f"收到文本消息: {content}", flush=True)

                # 获取用户认证信息
                from services.auth_service import AuthService
                from services.dify_service import DifyService
                import uuid
                
                auth_service = AuthService()
                token, user_info = auth_service.get_user_token(from_user)
                
                if not token:
                    # 认证失败，返回错误消息
                    error_message = "用户认证失败，请联系管理员"
                    stream = MakeTextStream(f"error_{timestamp}", error_message, True)
                    resp = EncryptMessage(wechat_service.wxcrypt, '', nonce, timestamp, stream)
                    if resp:
                        return Response(response=resp, mimetype="text/plain")
                    else:
                        return 'Encryption failed', 500
                
                if not user_info:
                    # 用户信息获取失败
                    error_message = "获取用户信息失败，请联系管理员"
                    stream = MakeTextStream(f"error_{timestamp}", error_message, True)
                    resp = EncryptMessage(wechat_service.wxcrypt, '', nonce, timestamp, stream)
                    if resp:
                        return Response(response=resp, mimetype="text/plain")
                    else:
                        return 'Encryption failed', 500

                # 1. 生成stream_id
                stream_id = str(uuid.uuid4())
                
                # 2. 创建流式任务（立即启动独立线程处理Dify）
                from services.stream_manager import stream_manager
                
                print("stream_manager 初始化成功", flush=True)
                code = random.randint(100000, 999999)  # 生成 6 位数字
                success = stream_manager.create_stream(
                    stream_id, content, token, user_info, from_user, code
                )
                
                if not success:
                    error_message = "创建思考任务失败"
                    stream = MakeTextStream(f"error_{timestamp}", error_message, True)
                    resp = EncryptMessage(wechat_service.wxcrypt, '', nonce, timestamp, stream)
                    if resp:
                        return Response(response=resp, mimetype="text/plain")
                    else:
                        return 'Encryption failed', 500
                
                # 3. 立即返回"思考中"消息，finish=false，触发企微发送stream请求
                thinking_message = "来宝在思考中......"
                stream = MakeTextStream(stream_id, thinking_message, False)
                resp = EncryptMessage(wechat_service.wxcrypt, '', nonce, timestamp, stream)
                
                print(f"创建流式任务成功，返回思考中消息，stream_id: {stream_id}", flush=True)
                
                if resp:
                    return Response(response=resp, mimetype="text/plain")
                else:
                    return 'Encryption failed', 500
                    
            elif msgtype == 'stream':
                # 流式消息处理 - 逐步返回Dify流式内容
                if stream_id:
                    msg_id = message_info.get('msg_id', '')
                    print(f"收到流式消息请求，stream_id: {stream_id}, msg_id: {msg_id}", flush=True)
                    
                    # 简单的重复请求检测
                    import os
                    duplicate_check_file = f"dify_cache/{stream_id}_last_msg.txt"
                    
                    try:
                        # 检查是否是重复请求
                        if os.path.exists(duplicate_check_file):
                            with open(duplicate_check_file, 'r') as f:
                                last_msg_id = f.read().strip()
                            
                            if last_msg_id == msg_id:
                                print(f"检测到重复请求，忽略: {msg_id}", flush=True)
                                return Response(response="success", mimetype="text/plain")
                        
                        # 记录当前请求ID
                        with open(duplicate_check_file, 'w') as f:
                            f.write(msg_id)
                    
                    except Exception as e:
                        print(f"重复请求检测失败: {e}", flush=True)
                    
                    try:
                        from services.stream_manager import stream_manager
                        
                        # 获取下一条未读消息
                        response_stream_id, content, is_finished = stream_manager.get_next_unread_message(stream_id)
                        
                        if response_stream_id is None:
                            # 流式任务不存在
                            print(f"流式任务不存在: {stream_id}", flush=True)
                            return Response(response="success", mimetype="text/plain")
                        
                        # 生成企微流式消息
                        stream = MakeTextStream(stream_id, content, is_finished)
                        resp = EncryptMessage(wechat_service.wxcrypt, '', nonce, timestamp, stream)
                        
                        print(f"返回流式消息，stream_id: {stream_id}, 内容长度: {len(content)}, 是否完成: {is_finished}", flush=True)
                        
                        # 如果完成了，清理重复检测文件和缓存
                        if is_finished:
                            try:
                                if os.path.exists(duplicate_check_file):
                                    os.remove(duplicate_check_file)
                                print(f"流式任务完成，清理重复检测文件: {stream_id}", flush=True)
                                
                                # 延迟清理缓存文件，给企微一些时间重新请求
                                import threading
                                def delayed_cleanup():
                                    import time
                                    time.sleep(5)  # 等待5秒后清理缓存
                                    stream_manager.cleanup_stream(stream_id)
                                
                                cleanup_thread = threading.Thread(target=delayed_cleanup)
                                cleanup_thread.daemon = True
                                cleanup_thread.start()
                            except Exception as e:
                                print(f"清理资源时发生错误: {e}", flush=True)
                        
                        if resp:
                            return Response(response=resp, mimetype="text/plain")
                        else:
                            return 'Encryption failed', 500
                    
                    except Exception as e:
                        print(f"处理stream请求时发生错误: {e}")
                        import traceback
                        traceback.print_exc()
                        
                        error_stream = MakeTextStream(stream_id, "处理请求时发生错误", True)
                        resp = EncryptMessage(wechat_service.wxcrypt, '', nonce, timestamp, error_stream)
                        if resp:
                            return Response(response=resp, mimetype="text/plain")
                        else:
                            return 'Encryption failed', 500
                
                return Response(response="success", mimetype="text/plain")
                
            elif msgtype == 'image':
                # 图片消息处理
                print("收到图片消息")
                return Response(response="success", mimetype="text/plain")
                
            elif msgtype == 'mixed':
                # 图文混排消息处理
                print("收到图文混排消息")
                return Response(response="success", mimetype="text/plain")
                
            elif msgtype == 'event':
                # 事件消息处理
                print("收到事件消息")
                return Response(response="success", mimetype="text/plain")
                
            else:
                # 不支持的消息类型
                print(f"不支持的消息类型: {msgtype}")
                return Response(response="success", mimetype="text/plain")
            
        except Exception as e:
            print(f"处理消息时发生错误: {e}", flush=True)
            return 'Internal error', 500

@app.route('/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({
        'status': 'ok',
        'timestamp': int(time.time()),
        'service': 'wechat-bot'
    })

if __name__ == '__main__':
    print("企业微信机器人服务启动中...")
    
    print(f"回调地址: http://localhost:{config.FLASK_PORT}/wechat/callback/你的机器人ID")
    print(f"健康检查: http://localhost:{config.FLASK_PORT}/health")
    
    app.run(
        host=config.FLASK_HOST,
        port=config.FLASK_PORT,
        debug=config.FLASK_DEBUG
    )
