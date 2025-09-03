#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
流式响应管理器 - 重新设计版本
负责管理Dify流式响应与企微stream_id的对应关系
支持队列式的消息处理机制
"""

import json
import os
import threading
import time
import uuid
import redis
from datetime import datetime
from services.dify_service import DifyService
from config.settings import config


class StreamManager:
    """流式响应管理器"""
    
    def __init__(self):
        self.active_threads = {}  # 存储活跃的Dify处理线程
        self.lock = threading.Lock()
        
        # 初始化Redis连接
        try:
            self.redis_client = redis.Redis(
                host=config.REDIS_HOST,
                port=config.REDIS_PORT,
                password=config.REDIS_PASSWORD,
                db=config.REDIS_DB,
                decode_responses=True  # 自动解码字符串
            )
            # 测试连接
            self.redis_client.ping()
            print("Redis连接成功", flush=True)
        except Exception as e:
            print(f"Redis连接失败: {e}", flush=True)
            raise e
    
    def create_stream(self, stream_id, content, token, user_info, from_user, code):
        """创建新的流式任务并启动独立线程处理Dify响应"""
        try:
            # 创建缓存数据，存储到Redis
            cache_data = {
                "content": content,
                "token": token,
                "user_info": user_info,
                "from_user": from_user,
                "status": "processing",  # pending, processing, completed, error
                "conversation_id": "",
                "created_time": datetime.now().isoformat(),
                "messages": [],  # 消息队列 [{"content": "...", "read": false, "timestamp": "..."}]
                "dify_finished": False,  # Dify是否完成
                "error_message": ""
            }

            print(f"解析cache_data: {cache_data}", flush=True)
            # 存储到Redis，使用stream_id作为key，设置过期时间30分钟
            redis_key = f"dify_stream:{stream_id}"
            self.redis_client.setex(redis_key, 1800, json.dumps(cache_data, ensure_ascii=False))
            
            # 启动独立线程处理Dify流式响应
            thread = threading.Thread(
                target=self._process_dify_stream_thread,
                args=(stream_id, content, token, user_info, code),
                daemon=True
            )
            thread.start()
            
            with self.lock:
                self.active_threads[stream_id] = thread
            
            print(f"创建流式任务并启动处理线程: {stream_id}", flush=True)
            return True
            
        except Exception as e:
            print(f"创建流式任务失败: {e}", flush=True)
            return False
    
    def _process_dify_stream_thread(self, stream_id, content, token, user_info, code):
        """独立线程处理Dify流式响应"""
        try:
            redis_key = f"dify_stream:{stream_id}"
            
            # 读取当前缓存数据
            cache_json = self.redis_client.get(redis_key)
            if not cache_json:
                print(f"Redis中未找到stream数据: {stream_id}", flush=True)
                return
                
            cache_data = json.loads(cache_json)
            
            conversation_id = cache_data.get("conversation_id", "")
            
            print(f"开始处理Dify流式响应: {stream_id}", flush=True)
            
            # 调用Dify服务
            dify_service = DifyService()
            generator = dify_service.send_message(token, user_info, content,code, conversation_id)
            
            accumulated_content = ""
            
            for conv_id, content_chunk, is_finished in generator:
                if conv_id is None:
                    # 出错了
                    cache_data["status"] = "error"
                    cache_data["error_message"] = content_chunk
                    cache_data["dify_finished"] = True
                    
                    # 添加错误消息到队列
                    cache_data["messages"].append({
                        "content": content_chunk,
                        "read": False,
                        "timestamp": datetime.now().isoformat(),
                        "is_error": True
                    })
                    
                    # 保存到Redis
                    self.redis_client.setex(redis_key, 1800, json.dumps(cache_data, ensure_ascii=False))
                    
                    print(f"Dify处理出错: {content_chunk}", flush=True)
                    break
                
                # 更新conversation_id
                if conv_id:
                    cache_data["conversation_id"] = conv_id
                
                # 如果有内容，累积并更新消息队列
                if content_chunk:
                    accumulated_content += content_chunk
                    
                    # 清空之前的未读消息，只保留最新的累积内容
                    # 这样企微就会显示完整的累积内容，而不是片段
                    cache_data["messages"] = [{
                        "content": accumulated_content,  # 完整的累积内容
                        "read": False,
                        "timestamp": datetime.now().isoformat(),
                        "is_error": False
                    }]
                    
                    print(f"[调试] Dify返回内容块 (长度: {len(content_chunk)}): {content_chunk[:100]}...", flush=True)
                    print(f"[调试] 累计内容长度: {len(accumulated_content)}, 消息队列长度: {len(cache_data['messages'])}", flush=True)
                
                # 如果完成了
                if is_finished:
                    cache_data["status"] = "completed"
                    cache_data["dify_finished"] = True
                    
                    # 确保有最终消息并标记为final
                    if cache_data["messages"]:
                        # 将最后一条消息标记为final
                        cache_data["messages"][-1]["is_final"] = True
                    else:
                        # 如果没有任何消息，添加一条默认消息
                        cache_data["messages"] = [{
                            "content": accumulated_content if accumulated_content else "抱歉，我暂时无法回答您的问题",
                            "read": False,
                            "timestamp": datetime.now().isoformat(),
                            "is_final": True,
                            "is_error": False
                        }]
                    
                    print(f"[调试] Dify流式处理完成: {stream_id}", flush=True)
                    print(f"[调试] 总内容长度: {len(accumulated_content)}", flush=True)
                    print(f"[调试] 消息队列总数: {len(cache_data['messages'])}", flush=True)
                    print(f"[调试] Redis key: {redis_key}", flush=True)
                
                # 保存到Redis
                self.redis_client.setex(redis_key, 1800, json.dumps(cache_data, ensure_ascii=False))
                
                if is_finished:
                    break
                    
                # 短暂等待，避免过于频繁的Redis写入
                time.sleep(0.1)
            
        except Exception as e:
            print(f"Dify流式处理线程异常: {e}", flush=True)
            import traceback
            traceback.print_exc()
            
            # 记录错误状态
            try:
                redis_key = f"dify_stream:{stream_id}"
                cache_json = self.redis_client.get(redis_key)
                if cache_json:
                    cache_data = json.loads(cache_json)
                    
                    cache_data["status"] = "error"
                    cache_data["error_message"] = f"处理异常: {str(e)}"
                    cache_data["dify_finished"] = True
                    
                    cache_data["messages"].append({
                        "content": f"处理异常: {str(e)}",
                        "read": False,
                        "timestamp": datetime.now().isoformat(),
                        "is_error": True
                    })
                    
                    # 保存到Redis
                    self.redis_client.setex(redis_key, 1800, json.dumps(cache_data, ensure_ascii=False))
                    
            except Exception as save_error:
                print(f"保存错误状态失败: {save_error}", flush=True)
        
        finally:
            # 清理线程引用
            with self.lock:
                if stream_id in self.active_threads:
                    del self.active_threads[stream_id]
    
    def get_next_unread_message(self, stream_id):
        """从Redis中读取下一条未读消息"""
        try:
            redis_key = f"dify_stream:{stream_id}"
            cache_json = self.redis_client.get(redis_key)
            
            if not cache_json:
                return None, "流式任务不存在", True
            
            cache_data = json.loads(cache_json)
            
            messages = cache_data.get("messages", [])
            dify_finished = cache_data.get("dify_finished", False)
            status = cache_data.get("status", "processing")
            
            # 查找第一条未读消息
            unread_message = None
            unread_index = -1
            
            for i, msg in enumerate(messages):
                if not msg.get("read", False):
                    unread_message = msg
                    unread_index = i
                    break
            
            if unread_message:
                # 标记为已读
                messages[unread_index]["read"] = True
                
                # 保存更新后的数据到Redis
                self.redis_client.setex(redis_key, 1800, json.dumps(cache_data, ensure_ascii=False))
                
                # 判断是否是最后一条消息
                is_final = unread_message.get("is_final", False)
                is_error = unread_message.get("is_error", False)
                
                # 直接返回当前这一段的内容，让企微自己处理累积
                content = unread_message["content"]
                
                print(f"[调试] 读取未读消息 - stream_id: {stream_id}", flush=True)
                print(f"[调试] 消息索引: {unread_index}, 内容长度: {len(content)}", flush=True)
                print(f"[调试] 内容预览: {content[:50]}...", flush=True)
                print(f"[调试] is_final: {is_final}, is_error: {is_error}", flush=True)
                print(f"[调试] 剩余未读消息数: {len([m for m in messages if not m.get('read', False)])}", flush=True)
                
                # 如果是错误消息或最终消息，标记为完成
                if is_error or is_final:
                    print(f"[调试] 返回最终消息，完成流式任务", flush=True)
                    return stream_id, content, True
                else:
                    print(f"[调试] 返回中间消息，继续流式任务", flush=True)
                    return stream_id, content, False
            
            else:
                # 没有未读消息
                if dify_finished or status == "completed":
                    # Dify已完成但没有未读消息，可能所有消息都已读取
                    return stream_id, "", True
                else:
                    # Dify还在处理中，等待更多消息
                    return stream_id, "正在处理中...", False
                
        except Exception as e:
            print(f"读取未读消息失败: {e}", flush=True)
            import traceback
            traceback.print_exc()
            return stream_id, f"读取消息失败: {str(e)}", True
    
    def cleanup_stream(self, stream_id):
        """清理流式任务"""
        try:
            # 从Redis中删除数据
            redis_key = f"dify_stream:{stream_id}"
            self.redis_client.delete(redis_key)
            
            with self.lock:
                if stream_id in self.active_threads:
                    del self.active_threads[stream_id]
                
            print(f"清理流式任务: {stream_id}", flush=True)
            
        except Exception as e:
            print(f"清理流式任务失败: {e}", flush=True)
    
    def get_stream_status(self, stream_id):
        """获取流式任务状态"""
        try:
            redis_key = f"dify_stream:{stream_id}"
            cache_json = self.redis_client.get(redis_key)
            
            if not cache_json:
                return "not_found"
            
            cache_data = json.loads(cache_json)
            return cache_data.get("status", "unknown")
            
        except Exception as e:
            print(f"获取流式任务状态失败: {e}", flush=True)
            return "error"


# 创建全局流管理器实例
stream_manager = StreamManager()