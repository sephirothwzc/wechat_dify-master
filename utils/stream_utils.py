#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
流式消息相关的工具函数
"""

import json
from demo.WXBizJsonMsgCrypt import WXBizJsonMsgCrypt

def MakeTextStream(stream_id, content, finish):
    """生成文本流式消息"""
    plain = {
        "msgtype": "stream",
        "stream": {
            "id": stream_id,
            "finish": finish, 
            "content": content
        }
    }
    return json.dumps(plain, ensure_ascii=False)

def EncryptMessage(wxcrypt, receiveid, nonce, timestamp, stream):
    """加密消息"""
    print(f"开始加密消息，receiveid={receiveid}, nonce={nonce}, timestamp={timestamp}")
    print(f"发送流消息: {stream}")

    ret, resp = wxcrypt.EncryptMsg(stream, nonce, timestamp)
    if ret != 0:
        print(f"加密失败，错误码: {ret}")
        return None

    stream_id = json.loads(stream)['stream']['id']
    finish = json.loads(stream)['stream']['finish']
    print(f"回调处理完成, 返回加密的流消息, stream_id={stream_id}, finish={finish}")
    print(f"加密后的消息: {resp}")

    return resp

class DifyStreamHandler:
    """Dify流式响应处理器"""
    
    def __init__(self, wxcrypt, nonce, timestamp):
        self.wxcrypt = wxcrypt
        self.nonce = nonce
        self.timestamp = timestamp
        self.accumulated_content = ""
        
    def process_stream_chunk(self, stream_id, content_chunk, is_finished):
        """
        处理Dify流式响应块
        
        Args:
            stream_id: 流ID
            content_chunk: 内容块
            is_finished: 是否完成
            
        Returns:
            加密后的企微消息
        """
        try:
            # 累积内容
            if content_chunk:
                self.accumulated_content += content_chunk
            
            # 生成流式消息
            stream_message = MakeTextStream(
                stream_id, 
                self.accumulated_content, 
                is_finished
            )
            
            # 加密消息
            encrypted_message = EncryptMessage(
                self.wxcrypt, 
                '', 
                self.nonce, 
                self.timestamp, 
                stream_message
            )
            
            return encrypted_message
            
        except Exception as e:
            print(f"处理流式响应块时发生错误: {e}")
            return None
