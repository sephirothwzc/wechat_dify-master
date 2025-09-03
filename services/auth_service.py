#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户认证服务
"""

import redis
import pymysql
import requests
import json
from datetime import datetime
from config.settings import config

class AuthService:
    """用户认证服务类"""
    
    def __init__(self):
        return
        # # 初始化Redis连接
        # self.redis_client = redis.Redis(
        #     host=config.REDIS_HOST,
        #     port=config.REDIS_PORT,
        #     password=config.REDIS_PASSWORD,
        #     db=config.REDIS_DB,
        #     decode_responses=True
        # )
        
        # # 测试Redis连接
        # try:
        #     self.redis_client.ping()
        #     print(f"Redis连接成功: {config.REDIS_HOST}:{config.REDIS_PORT}, DB: {config.REDIS_DB}")
        # except Exception as e:
        #     print(f"Redis连接失败: {e}")
        
        # # MySQL连接配置
        # self.mysql_config = {
        #     'host': config.MYSQL_HOST,
        #     'port': config.MYSQL_PORT,
        #     'user': config.MYSQL_USER,
        #     'password': config.MYSQL_PASSWORD,
        #     'database': config.MYSQL_DATABASE,
        #     'charset': 'utf8mb4'
        # }
    
    def get_user_token(self, from_user):
        """
        获取用户token
        1. 先从Redis中查找token
        2. 如果没有，从MySQL查询用户信息并获取新token
        """
        # try:
        #     # 步骤1: 从Redis获取token
        #     token_key = f"authorization:wechatid:{from_user}"
        #     token = self.redis_client.get(token_key)
            
        #     if token:
        #         # 步骤2: 验证token是否有效
        #         token_valid_key = f"authorization:token:{token}"
        #         if self.redis_client.exists(token_valid_key):
        #             print(f"从Redis获取到有效token: {token}")
        #             # 尝试获取用户信息
        #             user_info_key = f"userinfo:wechatid:{from_user}"
        #             user_info_str = self.redis_client.get(user_info_key)
        #             if user_info_str:
        #                 try:
        #                     user_info = json.loads(user_info_str)
        #                     print(f"从Redis获取到用户信息: {user_info['user_name']}")
        #                     return token, user_info
        #                 except json.JSONDecodeError:
        #                     print("用户信息JSON解析失败")
                    
        #             # 如果没有用户信息，从MySQL重新获取
        #             print("Redis中没有用户信息，从MySQL重新获取")
        #             user_info = self._get_user_info_from_mysql(from_user)
        #             if user_info:
        #                 # 保存用户信息到Redis
        #                 try:
        #                     user_info_json = json.dumps(user_info, ensure_ascii=False)
        #                     self.redis_client.set(user_info_key, user_info_json, ex=604800)
        #                     print(f"用户信息已保存到Redis")
        #                 except Exception as e:
        #                     print(f"保存用户信息到Redis失败: {e}")
                    
        #             return token, user_info
        #         else:
        #             print(f"token已失效: {token}")
        #             # token无效，删除旧token和用户信息
        #             self.redis_client.delete(token_key)
        #             user_info_key = f"userinfo:wechatid:{from_user}"
        #             self.redis_client.delete(user_info_key)
            
        #     # 步骤3: 从MySQL查询用户信息
        #     user_info = self._get_user_info_from_mysql(from_user)
        #     if not user_info:
        #         print(f"在MySQL中未找到用户: {from_user}")
        #         return None, None
            
        #     # 步骤4: 获取新token
        #     new_token = self._get_token_from_auth_service(user_info)
        #     if new_token:
        #         # 保存新token和用户信息到Redis，设置7天过期时间
        #         try:
        #             # 设置token，过期时间7天（604800秒）
        #             self.redis_client.set(token_key, new_token, ex=604800)
        #             print(f"获取到新token并保存到Redis: {new_token}")
                    
        #             # 同时保存用户信息
        #             user_info_key = f"userinfo:wechatid:{from_user}"
        #             user_info_json = json.dumps(user_info, ensure_ascii=False)
        #             self.redis_client.set(user_info_key, user_info_json, ex=604800)
        #             print(f"用户信息已保存到Redis")
                    
        #         except Exception as redis_error:
        #             print(f"Redis操作异常: {redis_error}")
        #             return None, user_info
        #         return new_token, user_info
        #     else:
        #         print(f"获取token失败，用户编码: {user_info['user_code']}")
        #         return None, user_info
                
        # except Exception as e:
        #     print(f"获取用户token时发生错误: {e}")
        #     return None, None
          # 模拟token和用户信息
        token = "mock_token_123456"
        user_info = {
            'phone': '13800000000',
            'user_code': 'MOCK_USER',
            'user_name': '测试用户',
            'gender': '未知',
            'password': 'mock_password'
        }
        print(f"跳过所有验证，直接返回token和用户信息: {token}, {user_info}")
        return token, user_info

    def _get_user_info_from_mysql(self, from_user):
        """从MySQL查询用户信息"""
        try:
            connection = pymysql.connect(**self.mysql_config)
            cursor = connection.cursor(pymysql.cursors.DictCursor)
            
            sql = """
            SELECT ACCOUNT_PHONE, ACCOUNT_CODE, ACCOUNT_NAME, ACCOUNT_SEX, ACCOUNT_PASSWORD 
            FROM je_rbac_account jra 
            LEFT JOIN je_rbac_cpuser jrc ON (jra.JE_RBAC_ACCOUNT_ID = jrc.CPUSER_BDYH_ID) 
            WHERE jrc.CPUSER_USER_ID = %s
            """
            
            cursor.execute(sql, (from_user,))
            result = cursor.fetchone()
            
            if result:
                user_info = {
                    'phone': result['ACCOUNT_PHONE'],
                    'user_code': result['ACCOUNT_CODE'],
                    'user_name': result['ACCOUNT_NAME'],
                    'gender': result['ACCOUNT_SEX'],
                    'password': result['ACCOUNT_PASSWORD']
                }
                print(f"从MySQL查询到用户信息: {user_info}")
                return user_info
            else:
                return None
                
        except Exception as e:
            print(f"MySQL查询用户信息时发生错误: {e}")
            return None
        finally:
            if 'connection' in locals():
                connection.close()
    
    def _get_token_from_auth_service(self, user_info):
        """从认证服务获取token"""
        try:
            url = config.AUTH_SERVICE_URL
            
            # GET请求参数
            params = {
                "usercode": user_info['user_code'],
                "password": user_info['password']
            }
            
            print(f"调用认证服务: {url}, 参数: usercode={params['usercode']}")
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                print(f"认证服务响应: {result}")
                
                # 检查返回格式
                if result.get('success') and result.get('data'):
                    token = result.get('data')
                    print(f"获取到token: {token}")
                    return token
                else:
                    print(f"认证失败: {result.get('message', '未知错误')}")
                    return None
            else:
                print(f"认证服务请求失败，状态码: {response.status_code}, 响应: {response.text}")
                return None
                
        except Exception as e:
            print(f"请求认证服务时发生错误: {e}")
            return None
    
    def get_time_info(self):
        """获取当前时间信息"""
        now = datetime.now()
        
        # 星期映射
        weekdays = {
            0: '星期一', 1: '星期二', 2: '星期三', 3: '星期四',
            4: '星期五', 5: '星期六', 6: '星期日'
        }
        
        # 季节判断
        month = now.month
        if month in [3, 4, 5]:
            season = '春季'
        elif month in [6, 7, 8]:
            season = '夏季'
        elif month in [9, 10, 11]:
            season = '秋季'
        else:
            season = '冬季'
        
        # 时间段判断
        hour = now.hour
        if 5 <= hour < 12:
            time_period = '上午'
        elif 12 <= hour < 18:
            time_period = '下午'
        elif 18 <= hour < 22:
            time_period = '晚上'
        else:
            time_period = '深夜'
        
        # 是否白天
        is_daytime = 6 <= hour < 18
        
        time_info = {
            "当前日期": now.strftime("%Y年%m月%d日"),
            "星期": weekdays[now.weekday()],
            "当前时间": now.strftime("%H:%M:%S"),
            "时间段": time_period,
            "是否白天": is_daytime,
            "季节": season
        }
        
        return json.dumps(time_info, ensure_ascii=False)
    
    def test_redis_operations(self, test_key="test_key", test_value="test_value"):
        """
        测试Redis操作
        用于调试Redis连接和存储问题
        """
        try:
            print(f"开始测试Redis操作...")
            
            # 测试1: 基本存储和读取
            print(f"测试1: 设置键值 {test_key} = {test_value}")
            result = self.redis_client.set(test_key, test_value, ex=300)  # 5分钟过期
            print(f"设置结果: {result}")
            
            # 验证存储
            stored_value = self.redis_client.get(test_key)
            print(f"读取结果: {stored_value}")
            
            # 检查过期时间
            ttl = self.redis_client.ttl(test_key)
            print(f"过期时间: {ttl}秒")
            
            # 测试2: 检查Redis信息
            info = self.redis_client.info('memory')
            print(f"Redis内存使用: {info.get('used_memory_human', 'unknown')}")
            
            # 测试3: 列出一些键
            keys = self.redis_client.keys("authorization.*")[:5]  # 最多显示5个
            print(f"现有的authorization键: {keys}")
            
            # 清理测试键
            self.redis_client.delete(test_key)
            print(f"测试完成，已清理测试键")
            
            return True
            
        except Exception as e:
            print(f"Redis测试失败: {e}")
            return False
