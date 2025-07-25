#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
API测试脚本
"""
import requests
import json

def test_api():
    base_url = "http://localhost:5000"
    
    # 测试字段结构API
    print("=== 测试字段结构API ===")
    try:
        response = requests.get(f"{base_url}/api/fields/structure")
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("字段结构数据:")
            print(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            print(f"错误: {response.text}")
    except Exception as e:
        print(f"请求失败: {e}")
    
    print("\n=== 测试字段分组API ===")
    try:
        response = requests.get(f"{base_url}/api/fields/groups")
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("字段分组数据:")
            print(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            print(f"错误: {response.text}")
    except Exception as e:
        print(f"请求失败: {e}")
    
    print("\n=== 测试简历数据API ===")
    try:
        response = requests.get(f"{base_url}/api/resume/latest")
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("最新简历数据:")
            print(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            print(f"错误: {response.text}")
    except Exception as e:
        print(f"请求失败: {e}")

if __name__ == "__main__":
    test_api() 