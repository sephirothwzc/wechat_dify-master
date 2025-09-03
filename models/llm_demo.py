#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模拟大模型行为的类（从demo移植）
"""

import os
import json
import time
import string
import random
from config.settings import config

class LLMDemo:
    """模拟大模型行为的类"""
    
    def __init__(self):
        self.cache_dir = config.LLM_CACHE_DIR
        self.max_steps = config.LLM_MAX_STEPS
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

    def invoke(self, question):
        """创建任务"""
        stream_id = self._generate_random_string(10)  # 生成一个随机字符串作为任务ID
        # 创建任务缓存文件
        cache_file = os.path.join(self.cache_dir, "%s.json" % stream_id)
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump({
                'question': question,
                'created_time': time.time(),
                'current_step': 0,
                'max_steps': self.max_steps
            }, f)
        return stream_id

    def get_answer(self, stream_id):
        """获取答案"""
        cache_file = os.path.join(self.cache_dir, "%s.json" % stream_id)
        if not os.path.exists(cache_file):
            return "任务不存在或已过期"
            
        with open(cache_file, 'r', encoding='utf-8') as f:
            task_data = json.load(f)
        
        # 更新缓存
        current_step = task_data['current_step'] + 1
        task_data['current_step'] = current_step
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(task_data, f)
            
        response = '收到问题：%s\n' % task_data['question']
        for i in range(current_step):
            response += '处理步骤 %d: 已完成\n' % (i)

        return response

    def is_task_finish(self, stream_id):
        """判断任务是否完成"""
        cache_file = os.path.join(self.cache_dir, "%s.json" % stream_id)
        if not os.path.exists(cache_file):
            return True
            
        with open(cache_file, 'r', encoding='utf-8') as f:
            task_data = json.load(f)
            
        return task_data['current_step'] >= task_data['max_steps']
    
    def _generate_random_string(self, length):
        """生成随机字符串"""
        letters = string.ascii_letters + string.digits
        return ''.join(random.choice(letters) for _ in range(length))
