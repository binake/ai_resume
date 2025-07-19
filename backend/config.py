
#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project : Python
@File    : config.py
@IDE     : PyCharm
@Author  : Gavin
@Date    : 2025/7/11 18:28
@DESC    : 
"""
from flask import Flask, jsonify, request
# from flask_cors import CORS
import pymongo
import json
from pymongo import MongoClient
from bson import ObjectId
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建Flask应用
app = Flask(__name__)
CORS(app)  # 允许跨域请求


class MongoDBClient:
    def __init__(self, connection_string="mongodb://localhost:27017/", database_name="ai_resume-python"):
        """
        初始化MongoDB连接

        Args:
            connection_string: MongoDB连接字符串
            database_name: 数据库名称
        """
        try:
            self.client = MongoClient(connection_string)
            self.db = self.client[database_name]
            self.collection = self.db["parseresults"]
            logger.info(f"成功连接到数据库: {database_name}")
        except Exception as e:
            logger.error(f"连接数据库失败: {e}")
            raise

    def get_all_result_data(self):
        """
        获取parseresults集合中所有文档的data.result字段

        Returns:
            list: 包含所有data.result字段的列表
        """
        try:
            cursor = self.collection.find({}, {"data.result": 1, "_id": 1})
            results = []

            for document in cursor:
                if "data" in document and "result" in document["data"]:
                    result_data = document["data"]["result"]
                    # 添加MongoDB的_id字段
                    result_data["_id"] = str(document["_id"])
                    results.append(result_data)

            logger.info(f"成功获取 {len(results)} 条记录")
            return results

        except Exception as e:
            logger.error(f"查询数据失败: {e}")
            return []

    def get_latest_result_data(self):
        """
        获取最新的一条简历数据

        Returns:
            dict: 最新的data.result字段数据
        """
        try:
            # 按_id降序排列，获取最新的一条记录
            cursor = self.collection.find({}, {"data.result": 1, "_id": 1}).sort("_id", -1).limit(1)

            for document in cursor:
                if "data" in document and "result" in document["data"]:
                    result_data = document["data"]["result"]
                    result_data["_id"] = str(document["_id"])
                    logger.info(f"成功获取最新记录: {document['_id']}")
                    return result_data

            logger.warning("没有找到任何记录")
            return None

        except Exception as e:
            logger.error(f"查询最新数据失败: {e}")
            return None

    def get_result_data_by_id(self, record_id):
        """
        根据ID获取特定的简历数据

        Args:
            record_id: MongoDB记录ID

        Returns:
            dict: 对应的data.result字段数据
        """
        try:
            document = self.collection.find_one(
                {"_id": ObjectId(record_id)},
                {"data.result": 1, "_id": 1}
            )

            if document and "data" in document and "result" in document["data"]:
                result_data = document["data"]["result"]
                result_data["_id"] = str(document["_id"])
                logger.info(f"成功获取指定记录: {record_id}")
                return result_data

            logger.warning(f"未找到ID为 {record_id} 的记录")
            return None

        except Exception as e:
            logger.error(f"查询指定ID数据失败: {e}")
            return None

    def save_result_data(self, data):
        """
        保存简历数据到数据库

        Args:
            data: 要保存的简历数据

        Returns:
            str: 保存成功返回记录ID，失败返回None
        """
        try:
            # 构造完整的文档结构
            document = {
                "data": {
                    "result": data
                },
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }

            # 如果数据中包含_id，则删除它（MongoDB会自动生成）
            if "_id" in data:
                del data["_id"]

            result = self.collection.insert_one(document)
            logger.info(f"成功保存数据，ID: {result.inserted_id}")
            return str(result.inserted_id)

        except Exception as e:
            logger.error(f"保存数据失败: {e}")
            return None


# 创建MongoDB客户端实例
# 如果你的MongoDB有用户名密码，请修改连接字符串
connection_string = "mongodb://localhost:27017/"
mongo_client = MongoDBClient(connection_string, "ai_resume-python")


@app.route('/api/resume/latest', methods=['GET'])
def get_latest_resume():
    """获取最新的简历数据"""
    try:
        data = mongo_client.get_latest_result_data()
        if data:
            return jsonify(data)
        else:
            return jsonify({"error": "未找到简历数据"}), 404
    except Exception as e:
        logger.error(f"API错误: {e}")
        return jsonify({"error": "服务器内部错误"}), 500


@app.route('/api/resume/all', methods=['GET'])
def get_all_resumes():
    """获取所有简历数据"""
    try:
        data = mongo_client.get_all_result_data()
        return jsonify(data)
    except Exception as e:
        logger.error(f"API错误: {e}")
        return jsonify({"error": "服务器内部错误"}), 500


@app.route('/api/resume/<record_id>', methods=['GET'])
def get_resume_by_id(record_id):
    """根据ID获取特定简历数据"""
    try:
        data = mongo_client.get_result_data_by_id(record_id)
        if data:
            return jsonify(data)
        else:
            return jsonify({"error": "未找到指定简历数据"}), 404
    except Exception as e:
        logger.error(f"API错误: {e}")
        return jsonify({"error": "服务器内部错误"}), 500


@app.route('/api/resume', methods=['POST'])
def save_resume():
    """保存简历数据"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "请求数据为空"}), 400

        record_id = mongo_client.save_result_data(data)
        if record_id:
            return jsonify({"message": "保存成功", "id": record_id}), 201
        else:
            return jsonify({"error": "保存失败"}), 500
    except Exception as e:
        logger.error(f"API错误: {e}")
        return jsonify({"error": "服务器内部错误"}), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查端点"""
    return jsonify({"status": "healthy", "message": "API服务正常运行"})


@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "API端点不存在"}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "服务器内部错误"}), 500


def find_available_port(start_port=5000, max_attempts=10):
    """寻找可用端口"""
    import socket
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                return port
        except socket.error:
            continue
    return None


if __name__ == '__main__':
    # 寻找可用端口
    available_ports = [5000, 5001, 8000, 8080, 3001, 4000]
    port = None

    for test_port in available_ports:
        try:
            import socket

            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', test_port))
                port = test_port
                break
        except socket.error:
            continue

    if port is None:
        port = find_available_port()

    if port is None:
        print("❌ 无法找到可用端口，请手动指定端口")
        exit(1)

    print("=== MongoDB + Flask API 服务启动 ===")
    print(f"🚀 服务运行在: http://localhost:{port}")
    print("📋 API端点说明：")
    print(f"GET  http://localhost:{port}/api/resume/latest - 获取最新简历数据")
    print(f"GET  http://localhost:{port}/api/resume/all - 获取所有简历数据")
    print(f"GET  http://localhost:{port}/api/resume/<id> - 根据ID获取特定简历数据")
    print(f"POST http://localhost:{port}/api/resume - 保存简历数据")
    print(f"GET  http://localhost:{port}/api/health - 健康检查")
    print("=====================================")
    print(f"⚠️  请将前端页面中的API_BASE_URL修改为: http://localhost:{port}/api")
    print("=====================================")

    try:
        # 启动Flask服务
        app.run(
            host='127.0.0.1',  # 只允许本地访问，避免权限问题
            port=port,
            debug=True
        )
    except Exception as e:
        print(f"❌ 服务启动失败: {e}")
        print("💡 解决方案：")
        print("1. 以管理员身份运行命令提示符")
        print("2. 检查防火墙设置")
        print("3. 确保端口未被其他程序占用")
        print("4. 尝试使用不同的端口")