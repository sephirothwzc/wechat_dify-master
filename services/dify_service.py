#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dify API调用服务
"""

import requests
import json
import uuid
from config.settings import config

class DifyService:
    """Dify API调用服务类"""
    
    def __init__(self):
        self.base_url = config.DIFY_BASE_URL
        self.chat_endpoint = config.DIFY_CHAT_ENDPOINT
        self.auth_prefix = config.DIFY_AUTH_PREFIX
    
    def send_message(self, token, user_info, content,code, stream_id=None ):
        """
        发送消息到Dify
        
        Args:
            token: 用户token
            user_info: 用户信息字典 {'user_code': '', 'user_name': '', 'gender': ''}
            content: 用户消息内容
            stream_id: 对话ID，如果为空则生成新的
            
        Returns:
            生成器，产生流式响应数据
        """
        try:
            # 构建请求URL
            url = f"{self.base_url}{self.chat_endpoint}"
            
            # 构建请求头
            headers = {
                'Authorization': f"{self.auth_prefix} {code} {token}",
                'Content-Type': 'application/json'
            }
            
            # 如果没有提供stream_id，对于新对话使用空字符串
            if not stream_id:
                conversation_id = ""
            else:
                conversation_id = stream_id
            
            # 获取时间信息
            from services.auth_service import AuthService
            auth_service = AuthService()
            time_info = auth_service.get_time_info()
            
            # 构建请求体
            payload = {
                "inputs": {
                    "token": token,
                    "userCode": user_info.get('user_code', ''),
                    "userName": user_info.get('user_name', ''),
                    "timeinfo": time_info,
                    "role": "all",
                    "isNetwork": "0",
                    "isR1": "0",
                    "gender": user_info.get('gender', '')
                },
                "query": content,
                "response_mode": "streaming",
                "conversation_id": conversation_id,
                "user": user_info.get('user_code', ''),
                "files": []
            }
            
            print(f"发送Dify请求: {url}")
            print(f"请求payload: {json.dumps(payload, ensure_ascii=False)}")
            
            # 发送流式请求
            response = requests.post(
                url, 
                json=payload, 
                headers=headers, 
                stream=True,
                timeout=30
            )
            
            if response.status_code != 200:
                print(f"Dify请求失败，状态码: {response.status_code}, 响应: {response.text}")
                yield None, f"Dify请求失败: {response.status_code}", True
                return
            
            print("开始接收Dify流式响应...")
            
            # 解析流式响应
            accumulated_answer = ""
            actual_conversation_id = conversation_id  # 初始值
            
            for line in response.iter_lines(decode_unicode=True):
                if line and line.startswith('data: '):
                    try:
                        data_str = line[6:]  # 移除 'data: ' 前缀
                        if data_str.strip():
                            data = json.loads(data_str)
                            event_type = data.get('event', '')
                            
                            print(f"收到Dify事件: {event_type}")
                            
                            if event_type == 'message':
                                # 消息事件
                                answer_chunk = data.get('answer', '')
                                print(f"[调试] Dify message事件")
                                print(f"[调试] - answer长度: {len(answer_chunk)}")
                                print(f"[调试] - answer内容: {repr(answer_chunk[:100])}")
                                print(f"[调试] - 累积长度: {len(accumulated_answer)}")
                                
                                if answer_chunk:
                                    # 直接返回这次的answer，让StreamManager决定如何处理
                                    accumulated_answer += answer_chunk  # 简单累积
                                    actual_conversation_id = data.get('conversation_id', actual_conversation_id)
                                    print(f"[调试] - 返回content_chunk长度: {len(answer_chunk)}")
                                    yield actual_conversation_id, answer_chunk, False
                                else:
                                    print(f"[调试] - answer为空，跳过")
                                
                            elif event_type == 'message_end':
                                # 消息结束事件
                                print("Dify消息流结束")
                                actual_conversation_id = data.get('conversation_id', actual_conversation_id)
                                yield actual_conversation_id, "", True
                                break
                                
                            elif event_type == 'workflow_finished':
                                # 工作流结束事件
                                print("Dify工作流结束")
                                actual_conversation_id = data.get('conversation_id', actual_conversation_id)
                                yield actual_conversation_id, "", True
                                break
                                
                            elif event_type in ['workflow_started', 'node_started', 'node_finished']:
                                # 其他事件，继续监听
                                continue
                                
                    except json.JSONDecodeError as e:
                        print(f"解析Dify响应JSON失败: {e}, 原始数据: {data_str}")
                        continue
                    except Exception as e:
                        print(f"处理Dify响应时发生错误: {e}")
                        continue
            
            print(f"Dify完整响应: {accumulated_answer}")
            
        except requests.exceptions.Timeout:
            print("Dify请求超时")
            yield None, "请求超时，请稍后重试", True
        except requests.exceptions.RequestException as e:
            print(f"Dify请求异常: {e}")
            yield None, f"网络请求失败: {str(e)}", True
        except Exception as e:
            print(f"发送Dify消息时发生未知错误: {e}")
            yield None, f"服务异常: {str(e)}", True
    
    def get_conversation_history(self, token, conversation_id):
        """获取对话历史（如果需要的话）"""
        # 这里可以根据需要实现获取历史对话的功能
        pass
