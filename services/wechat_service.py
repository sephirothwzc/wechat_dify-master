#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
企业微信机器人服务类
"""

import hashlib
from demo.WXBizJsonMsgCrypt import WXBizJsonMsgCrypt
from config.settings import config

class WechatBotService:
    """企业微信机器人服务类"""
    
    def __init__(self):
        self.token = config.WECHAT_TOKEN
        self.encoding_aes_key = config.WECHAT_ENCODING_AES_KEY
        # 智能机器人的receiveid是空串
        self.receiveid = ''
        
        # 初始化加密工具
        if self.token and self.encoding_aes_key:
            try:
                self.wxcrypt = WXBizJsonMsgCrypt(self.token, self.encoding_aes_key, self.receiveid)
                print("加密工具初始化成功")
            except Exception as e:
                print(f"加密工具初始化失败: {e}")
                self.wxcrypt = None
        else:
            print("加密工具初始化失败: 缺少必要参数")
            self.wxcrypt = None
    
    def verify_signature(self, signature, timestamp, nonce, echostr=None):
        """验证企业微信签名"""
        try:
            if echostr:
                # URL验证
                if not self.wxcrypt:
                    print("加密工具未初始化")
                    return False, None
                
                ret, reply = self.wxcrypt.VerifyURL(signature, timestamp, nonce, echostr)
                return ret == 0, reply
            else:
                # 消息验证
                tmp_arr = [self.token, timestamp, nonce]
                tmp_arr.sort()
                tmp_str = ''.join(tmp_arr)
                signature_check = hashlib.sha1(tmp_str.encode('utf-8')).hexdigest()
                return signature_check == signature, None
        except Exception as e:
            print(f"签名验证错误: {e}")
            return False, None
    
    def decrypt_message(self, msg_signature, timestamp, nonce, encrypt_msg):
        """解密企业微信消息"""
        try:
            ret, msg = self.wxcrypt.DecryptMsg(encrypt_msg, msg_signature, timestamp, nonce)
            if ret == 0:
                return True, msg
            else:
                print(f"消息解密失败，错误码: {ret}")
                return False, None
        except Exception as e:
            print(f"消息解密错误: {e}")
            return False, None
    
    def parse_message(self, json_content):
        """解析企业微信机器人JSON消息"""
        try:
            import json
            
            # 处理不同类型的输入
            if isinstance(json_content, bytes):
                json_data = json.loads(json_content.decode('utf-8'))
            elif isinstance(json_content, str):
                json_data = json.loads(json_content)
            else:
                print(f"不支持的消息内容类型: {type(json_content)}")
                return None
                
            print(f"解析JSON消息: {json_data}")
            
            message_info = {
                'msg_type': json_data.get('msgtype', ''),
                'from_user': json_data.get('from', {}).get('userid', ''),
                'content': '',
                'msg_id': json_data.get('msgid', '')
            }
            
            # 根据消息类型提取内容
            if message_info['msg_type'] == 'text':
                message_info['content'] = json_data.get('text', {}).get('content', '')
                print(f"提取的文本内容: {message_info['content']}")
            elif message_info['msg_type'] == 'stream':
                message_info['stream_id'] = json_data.get('stream', {}).get('id', '')
            elif message_info['msg_type'] == 'image':
                message_info['content'] = f"[图片消息]"
            elif message_info['msg_type'] == 'voice':
                message_info['content'] = f"[语音消息]"
            
            return message_info
                
        except Exception as e:
            print(f"消息解析错误: {e}")
            return None
