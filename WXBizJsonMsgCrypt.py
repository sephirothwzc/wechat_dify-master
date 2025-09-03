#!/usr/bin/env python
# coding=utf-8
# 企业微信智能机器人消息加解密工具

import base64
import hashlib
import time
import random
import struct
import socket
import json
from Crypto.Cipher import AES
import xml.etree.ElementTree as ET

class WXBizJsonMsgCrypt:
    """企业微信智能机器人消息加解密工具"""
    
    def __init__(self, token, encoding_aes_key, receiveid):
        self.token = token
        self.encoding_aes_key = encoding_aes_key
        self.receiveid = receiveid
        
        # 解码AES密钥
        self.aes_key = base64.b64decode(encoding_aes_key + "=" * (-len(encoding_aes_key) % 4))
        
    def VerifyURL(self, msg_signature, timestamp, nonce, echostr):
        """验证URL"""
        try:
            # 验证签名
            signature = self._get_signature(timestamp, nonce, echostr)
            if signature != msg_signature:
                return -40001, None
                
            # 解密echostr
            ret, decrypt_echostr = self._decrypt(echostr)
            if ret != 0:
                return ret, None
                
            return 0, decrypt_echostr.decode('utf-8')
            
        except Exception as e:
            return -40000, str(e)
    
    def EncryptMsg(self, reply_msg, nonce, timestamp):
        """加密消息"""
        try:
            print(f"开始加密，AES密钥长度: {len(self.aes_key)} 字节")
            print(f"接收到的消息: {reply_msg}")
            
            # 生成随机字符串
            random_str = self._get_random_str(16)
            print(f"生成的随机字符串: {random_str}")
            
            # 构造待加密字符串
            text = reply_msg.encode('utf-8')
            text_len = len(text)
            print(f"消息长度: {text_len}")
            
            # 构造待加密数据: random_str(16B) + msg_len(4B) + msg + receiveid
            msg_len = struct.pack("I", socket.htonl(text_len))
            text = random_str.encode('utf-8') + msg_len + text + self.receiveid.encode('utf-8')
            print(f"待加密数据总长度: {len(text)} 字节")
            
            # 加密
            encrypted = self._encrypt(text)
            print(f"加密成功，结果长度: {len(encrypted)}")
            
            # 生成签名
            signature = self._get_signature(timestamp, nonce, encrypted)
            print(f"签名生成成功: {signature[:10]}...")
            
            # 构造返回数据
            result = {
                "Encrypt": encrypted,
                "MsgSignature": signature,
                "TimeStamp": timestamp,
                "Nonce": nonce
            }
            
            return 0, json.dumps(result)
            
        except Exception as e:
            print(f"加密过程中出现异常: {e}")
            import traceback
            traceback.print_exc()
            return -40000, str(e)
    
    def DecryptMsg(self, post_data, msg_signature, timestamp, nonce):
        """解密消息"""
        try:
            # 解析POST数据
            if isinstance(post_data, bytes):
                data = json.loads(post_data.decode('utf-8'))
            else:
                data = json.loads(post_data)
            
            # 获取加密数据
            encrypt_msg = data.get('encrypt', '')
            if not encrypt_msg:
                return -40002, None
            
            # 验证签名
            signature = self._get_signature(timestamp, nonce, encrypt_msg)
            if signature != msg_signature:
                return -40001, None
            
            # 解密
            ret, decrypt_msg = self._decrypt(encrypt_msg)
            if ret != 0:
                return ret, None
            
            return 0, decrypt_msg
            
        except Exception as e:
            return -40000, str(e)
    
    def _get_signature(self, timestamp, nonce, encrypt_msg):
        """生成签名"""
        tmp_arr = [self.token, timestamp, nonce, encrypt_msg]
        tmp_arr.sort()
        tmp_str = ''.join(tmp_arr)
        return hashlib.sha1(tmp_str.encode('utf-8')).hexdigest()
    
    def _encrypt(self, text):
        """AES加密"""
        try:
            # 确保AES密钥是32字节
            if len(self.aes_key) != 32:
                raise ValueError(f"AES密钥长度错误: {len(self.aes_key)} 字节，应为32字节")
            
            # PKCS7填充 - 修复Python 3兼容性
            pad_len = 32 - (len(text) % 32)
            text += bytes([pad_len]) * pad_len
            
            # 加密
            iv = self.aes_key[:16]
            cipher = AES.new(self.aes_key, AES.MODE_CBC, iv)
            encrypted = cipher.encrypt(text)
            
            return base64.b64encode(encrypted).decode('utf-8')
            
        except Exception as e:
            print(f"加密过程中出现错误: {e}")
            raise
    
    def _decrypt(self, encrypted_msg):
        """AES解密"""
        try:
            # Base64解码
            encrypted = base64.b64decode(encrypted_msg)
            
            # 解密
            iv = self.aes_key[:16]
            cipher = AES.new(self.aes_key, AES.MODE_CBC, iv)
            decrypted = cipher.decrypt(encrypted)
            
            # 去除填充
            pad_len = decrypted[-1]
            if pad_len > 32:
                return -40007, None
            
            decrypted = decrypted[:-pad_len]
            
            # 解析数据: random_str(16B) + msg_len(4B) + msg + receiveid
            if len(decrypted) < 20:
                return -40007, None
            
            msg_len = socket.ntohl(struct.unpack("I", decrypted[16:20])[0])
            if msg_len <= 0 or msg_len > len(decrypted) - 20:
                return -40007, None
            
            msg = decrypted[20:20+msg_len]
            
            return 0, msg
            
        except Exception as e:
            return -40007, str(e)
    
    def _get_random_str(self, length):
        """生成随机字符串"""
        chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
        return ''.join(random.choice(chars) for _ in range(length))
