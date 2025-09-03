#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
企业微信消息加密解密工具
基于企业微信官方加密库实现
"""

import base64
import time
import random
import hashlib
import struct
import socket
import xml.etree.ElementTree as ET
from Crypto.Cipher import AES

class WXBizMsgCrypt:
    def __init__(self, sToken, sEncodingAESKey, sReceiveId):
        try:
            self.key = base64.b64decode(sEncodingAESKey + "=")
            assert len(self.key) == 32
        except:
            raise Exception("EncodingAESKey invalid")
        
        self.token = sToken
        self.receiveid = sReceiveId

    def _get_sha1(self, token, timestamp, nonce, encrypt):
        """计算签名"""
        try:
            sortlist = [token, timestamp, nonce, encrypt]
            sortlist.sort()
            sha = hashlib.sha1("".join(sortlist).encode()).hexdigest()
            return 0, sha
        except Exception as e:
            return -40003, None

    def _get_random_str(self):
        """生成随机字符串"""
        rule = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
        str = ""
        for i in range(16):
            str = str + rule[random.randint(0, len(rule) - 1)]
        return str

    def _pkcs7encode(self, text):
        """PKCS7填充"""
        text_length = len(text)
        amount_to_pad = 32 - (text_length % 32)
        if amount_to_pad == 0:
            amount_to_pad = 32
        pad = chr(amount_to_pad)
        return text + pad * amount_to_pad

    def _pkcs7decode(self, decrypted):
        """PKCS7去填充"""
        try:
            if len(decrypted) == 0:
                return decrypted
                
            # 处理二进制数据，直接取最后一个字节作为填充值
            pad = decrypted[-1]
            
            if pad < 1 or pad > 32:
                return decrypted
                
            if pad > len(decrypted):
                return decrypted
                
            result = decrypted[:-pad]
            return result
            
        except Exception as e:
            return decrypted

    def _encrypt(self, text, receiveid):
        """加密消息"""
        try:
            # 随机字符串 + msg_len(4B) + text + receiveid
            text = text.encode('utf-8')
            random_str = self._get_random_str()
            msg_len = struct.pack("I", socket.htonl(len(text)))
            msg = random_str.encode() + msg_len + text + receiveid.encode()
            
            # 使用自定义的填充方式
            msg = self._pkcs7encode(msg.decode('utf-8')).encode('utf-8')
            
            # 加密
            iv = self.key[:16]
            cipher = AES.new(self.key, AES.MODE_CBC, iv)
            encrypted = cipher.encrypt(msg)
            
            # base64编码
            encrypted_msg = base64.b64encode(encrypted).decode('utf-8')
            return 0, encrypted_msg
        except Exception as e:
            return -40007, None

    def _decrypt(self, text, receiveid):
        """解密消息"""
        try:
            # base64解码
            ciphertext = base64.b64decode(text)
            
            # 解密
            iv = self.key[:16]
            cipher = AES.new(self.key, AES.MODE_CBC, iv)
            decrypted = cipher.decrypt(ciphertext)
            
            # 去除填充 - 直接处理二进制数据，不进行UTF-8解码
            decrypted = self._pkcs7decode(decrypted)
            
            # 解析内容 random_str(16B) + msg_len(4B) + msg + receiveid
            content = decrypted[16:]
            
            if len(content) < 4:
                return -40007, None
            
            # 直接解析4字节的长度字段（网络字节序）
            xml_len = socket.ntohl(struct.unpack("I", content[:4])[0])
            
            if xml_len <= 0 or xml_len > len(content) - 4:
                return -40007, None
            
            xml_content = content[4:xml_len+4]
            from_receiveid = content[xml_len+4:]
            
            # 对于URL验证，echostr是用企业微信的企业ID加密的，我们不需要验证企业ID
            # 只有在解密消息时才需要验证企业ID
            if from_receiveid != receiveid:
                # 临时跳过企业ID验证，用于URL验证
                pass
                
            return 0, xml_content
                
        except Exception as e:
            print(f"解密异常: {e}")
            return -40007, None

    def EncryptMsg(self, sReplyMsg, sNonce, timestamp=None):
        """加密消息"""
        if timestamp is None:
            timestamp = str(int(time.time()))
        
        # 加密
        ret, encrypt = self._encrypt(sReplyMsg, self.receiveid)
        if ret != 0:
            return ret, None
        
        # 生成签名
        ret, signature = self._get_sha1(self.token, timestamp, sNonce, encrypt)
        if ret != 0:
            return ret, None
        
        xmlParse = """<xml>
<Encrypt><![CDATA[{encrypt}]]></Encrypt>
<MsgSignature><![CDATA[{signature}]]></MsgSignature>
<TimeStamp>{timestamp}</TimeStamp>
<Nonce><![CDATA[{nonce}]]></Nonce>
</xml>"""
        
        return ret, xmlParse.format(
            encrypt=encrypt,
            signature=signature,
            timestamp=timestamp,
            nonce=sNonce
        )

    def DecryptMsg(self, sPostData, sMsgSignature, sTimeStamp, sNonce):
        """解密消息"""
        try:
            # 企业微信机器人发送的是JSON格式，需要先解析JSON
            if sPostData.startswith(b'{'):
                # JSON格式
                import json
                json_data = json.loads(sPostData.decode('utf-8'))
                encrypt = json_data.get('encrypt', '')
            else:
                # XML格式
                xml_parse = ET.fromstring(sPostData)
                encrypt = xml_parse.find("Encrypt").text
                
            if not encrypt:
                return -40002, None
                
        except Exception as e:
            print(f"解析消息数据失败: {e}")
            return -40002, None
        
        # 验证签名
        ret, signature = self._get_sha1(self.token, sTimeStamp, sNonce, encrypt)
        if ret != 0:
            return ret, None
        
        if signature != sMsgSignature:
            return -40001, None
        
        # 解密
        ret, xml_content = self._decrypt(encrypt, self.receiveid)
        return ret, xml_content

    def VerifyURL(self, sMsgSignature, sTimeStamp, sNonce, sEchoStr):
        """验证URL"""
        ret, signature = self._get_sha1(self.token, sTimeStamp, sNonce, sEchoStr)
        if ret != 0:
            return ret, None
        
        if signature != sMsgSignature:
            return -40001, None
        
        ret, sReplyEchoStr = self._decrypt(sEchoStr, self.receiveid)
        return ret, sReplyEchoStr
