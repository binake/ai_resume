#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project : Python
@File    : v26.py
@IDE     : PyCharm
@Author  : Gavin
@Date    : 2025/7/16 22:50
@DESC    : 
"""
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
import pymongo
import json
from pymongo import MongoClient
from bson import ObjectId
import logging
from datetime import datetime
import re
import os
import shutil
from werkzeug.utils import secure_filename
from pathlib import Path
import uuid
from parser_service import ResumeParserService
# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 创建Flask应用
app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 关键配置：确保中文字符不被转义
app.config['JSON_AS_ASCII'] = False
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size

# 文件存储配置
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"

# 文件类型分类
FILE_CATEGORIES = {
    'resume': '个人简历',
    'company': '公司介绍',
    'job': '工作条件',
    'knowledge': '知识纪要',
    'project': '项目文件'
}

# 允许的文件类型
ALLOWED_EXTENSIONS = {
    'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'md'
}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def ensure_directory_exists(path):
    """确保目录存在"""
    Path(path).mkdir(parents=True, exist_ok=True)


def init_data_directories():
    """初始化数据目录结构"""
    for category in FILE_CATEGORIES.keys():
        category_dir = DATA_DIR / category
        ensure_directory_exists(category_dir)

    # 创建项目文件的子目录将在创建项目时动态创建
    projects_dir = DATA_DIR / "projects"
    ensure_directory_exists(projects_dir)

    logger.info(f"数据目录初始化完成: {DATA_DIR}")


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

            # 简历数据集合
            self.collection = self.db["parseresults"]

            # 项目管理集合
            self.projects_collection = self.db["projects"]

            # 文件元数据集合
            self.files_collection = self.db["files"]

            logger.info(f"成功连接到数据库: {database_name}")
        except Exception as e:
            logger.error(f"连接数据库失败: {e}")
            raise

    def serialize_datetime(self, data):
        """
        将数据中的datetime对象转换为ISO格式字符串，使其可以被JSON序列化
        """
        if isinstance(data, dict):
            return {key: self.serialize_datetime(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self.serialize_datetime(item) for item in data]
        elif isinstance(data, datetime):
            return data.isoformat()
        elif isinstance(data, ObjectId):
            return str(data)
        else:
            return data

    def ensure_utf8_encoding(self, data):
        """
        确保数据使用正确的UTF-8编码，处理Unicode转义序列
        """
        if isinstance(data, dict):
            return {key: self.ensure_utf8_encoding(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self.ensure_utf8_encoding(item) for item in data]
        elif isinstance(data, str):
            # 处理Unicode转义序列
            if '\\u' in data:
                try:
                    def replace_unicode(match):
                        try:
                            unicode_int = int(match.group(1), 16)
                            return chr(unicode_int)
                        except (ValueError, OverflowError):
                            return match.group(0)

                    # 使用正则表达式替换所有Unicode转义序列
                    decoded = re.sub(r'\\u([0-9a-fA-F]{4})', replace_unicode, data)
                    logger.debug(f"Unicode解码: '{data[:50]}...' -> '{decoded[:50]}...'")
                    return decoded
                except Exception as e:
                    logger.warning(f"Unicode解码失败: {e}")
                    return data
            else:
                return data
        else:
            return data

    # ============ 简历数据相关方法 ============
    def get_all_result_data(self):
        """获取parseresults集合中所有文档的data.result字段"""
        try:
            cursor = self.collection.find({}, {"data.result": 1, "_id": 1})
            results = []

            for document in cursor:
                if "data" in document and "result" in document["data"]:
                    result_data = document["data"]["result"]
                    # 处理编码
                    result_data = self.ensure_utf8_encoding(result_data)
                    # 添加MongoDB的_id字段
                    result_data["_id"] = str(document["_id"])
                    results.append(result_data)

            logger.info(f"成功获取 {len(results)} 条记录")
            return results

        except Exception as e:
            logger.error(f"查询数据失败: {e}")
            return []

    def get_latest_result_data(self):
        """获取最新的一条简历数据"""
        try:
            # 按_id降序排列，获取最新的一条记录
            cursor = self.collection.find({}, {"data.result": 1, "_id": 1}).sort("_id", -1).limit(1)

            for document in cursor:
                if "data" in document and "result" in document["data"]:
                    result_data = document["data"]["result"]
                    # 处理编码
                    result_data = self.ensure_utf8_encoding(result_data)
                    result_data["_id"] = str(document["_id"])
                    logger.info(f"成功获取最新记录: {document['_id']}")
                    return result_data

            logger.warning("没有找到任何记录")
            return None

        except Exception as e:
            logger.error(f"查询最新数据失败: {e}")
            return None

    def get_result_data_by_id(self, record_id):
        """根据ID获取特定的简历数据"""
        try:
            document = self.collection.find_one(
                {"_id": ObjectId(record_id)},
                {"data.result": 1, "_id": 1}
            )

            if document and "data" in document and "result" in document["data"]:
                result_data = document["data"]["result"]
                # 处理编码
                result_data = self.ensure_utf8_encoding(result_data)
                result_data["_id"] = str(document["_id"])
                logger.info(f"成功获取指定记录: {record_id}")
                return result_data

            logger.warning(f"未找到ID为 {record_id} 的记录")
            return None

        except Exception as e:
            logger.error(f"查询指定ID数据失败: {e}")
            return None

    def save_result_data(self, data):
        """保存简历数据到数据库"""
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

    # ============ 项目管理相关方法 ============
    def get_all_projects(self):
        """获取所有项目"""
        try:
            cursor = self.projects_collection.find({}).sort("created_at", -1)
            projects = []

            for project in cursor:
                # 处理datetime序列化
                project = self.serialize_datetime(project)
                projects.append(project)

            logger.info(f"成功获取 {len(projects)} 个项目")
            return projects
        except Exception as e:
            logger.error(f"获取项目列表失败: {e}")
            return []

    def create_project(self, name, description=""):
        """创建新项目"""
        try:
            # 检查项目名是否已存在
            existing = self.projects_collection.find_one({"name": name})
            if existing:
                return None, "项目名称已存在"

            project = {
                "name": name,
                "description": description,
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                "file_count": 0
            }

            result = self.projects_collection.insert_one(project)
            project_id = str(result.inserted_id)

            # 创建项目文件目录
            project_dir = DATA_DIR / "projects" / project_id
            ensure_directory_exists(project_dir)

            # 重新获取插入的项目数据，包含_id
            project = self.projects_collection.find_one({"_id": result.inserted_id})
            # 处理datetime序列化
            project = self.serialize_datetime(project)

            logger.info(f"成功创建项目: {name}, 目录: {project_dir}")
            return project, None
        except Exception as e:
            logger.error(f"创建项目失败: {e}")
            return None, str(e)

    def get_project_by_id(self, project_id):
        """根据ID获取项目"""
        try:
            project = self.projects_collection.find_one({"_id": ObjectId(project_id)})
            if project:
                # 处理datetime序列化
                project = self.serialize_datetime(project)
                return project
            return None
        except Exception as e:
            logger.error(f"获取项目失败: {e}")
            return None

    def delete_project(self, project_id):
        """删除项目及其所有文件"""
        try:
            # 删除项目文件目录
            project_dir = DATA_DIR / "projects" / project_id
            if project_dir.exists():
                shutil.rmtree(project_dir)
                logger.info(f"删除项目目录: {project_dir}")

            # 删除项目文件的数据库记录
            self.files_collection.delete_many({"project_id": project_id})

            # 删除项目
            result = self.projects_collection.delete_one({"_id": ObjectId(project_id)})

            if result.deleted_count > 0:
                logger.info(f"成功删除项目 {project_id}")
                return True
            else:
                logger.warning(f"项目 {project_id} 不存在")
                return False

        except Exception as e:
            logger.error(f"删除项目失败: {e}")
            return False

    # ============ 文件管理相关方法 ============
    def save_file_to_disk(self, file, category, project_id=None, filename=None):
        """保存文件到磁盘"""
        try:
            if not filename:
                filename = secure_filename(file.filename)

            # 生成唯一文件名避免冲突
            file_id = str(uuid.uuid4())
            file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
            unique_filename = f"{file_id}.{file_ext}" if file_ext else file_id

            # 确定保存路径
            if category == 'project' and project_id:
                file_path = DATA_DIR / "projects" / project_id / unique_filename
            else:
                file_path = DATA_DIR / category / unique_filename

            # 确保目录存在
            ensure_directory_exists(file_path.parent)

            # 保存文件
            file.save(str(file_path))

            return {
                'file_id': file_id,
                'unique_filename': unique_filename,
                'file_path': str(file_path),
                'original_filename': filename
            }
        except Exception as e:
            logger.error(f"保存文件到磁盘失败: {e}")
            return None

    def upload_file(self, file, category, project_id=None, original_filename=None):
        """上传文件"""
        try:
            if not original_filename:
                original_filename = file.filename
                # 添加调试信息
            print(f"[DEBUG] 接收到的原始文件名: {repr(original_filename)}")
            print(f"[DEBUG] file.filename: {repr(file.filename)}")
            # 如果是项目文件，检查项目是否存在
            if category == 'project' and project_id:
                project = self.get_project_by_id(project_id)
                if not project:
                    return None, "项目不存在"

            # 保存文件到磁盘
            file_info = self.save_file_to_disk(file, category, project_id, original_filename)
            if not file_info:
                return None, "文件保存失败"

            # 获取文件信息
            file_size = os.path.getsize(file_info['file_path'])

            # 保存文件元数据到数据库
            file_document = {
                "file_id": file_info['file_id'],
                "original_filename": file.filename,
                "filename": file_info['unique_filename'],
                "file_path": file_info['file_path'],
                "category": category,
                "project_id": project_id,
                "size": file_size,
                "mimetype": getattr(file, 'content_type', 'application/octet-stream'),
                "upload_date": datetime.now(),
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                # 添加解析状态相关字段
                "parse_status": "pending",  # pending, processing, completed, failed
                "parse_enabled": True,      # 是否启用解析
                "parse_result": None,       # 解析结果
                "parse_error": None,        # 解析错误信息
                "parse_date": None          # 解析完成时间
            }
            print(f"[DEBUG] 保存到数据库的original_filename: {repr(file_document['original_filename'])}")
            result = self.files_collection.insert_one(file_document)
            file_document['_id'] = str(result.inserted_id)

            # 如果是项目文件，更新项目文件计数
            if category == 'project' and project_id:
                self.projects_collection.update_one(
                    {"_id": ObjectId(project_id)},
                    {"$inc": {"file_count": 1}, "$set": {"updated_at": datetime.now()}}
                )

            # 处理datetime序列化
            file_document = self.serialize_datetime(file_document)

            logger.info(f"成功上传文件: {original_filename} 到 {category}")
            return file_document, None

        except Exception as e:
            logger.error(f"上传文件失败: {e}")
            return None, str(e)

    def get_files_by_category(self, category, project_id=None):
        """根据类别获取文件"""
        try:
            query = {"category": category}
            if project_id:
                query["project_id"] = project_id

            cursor = self.files_collection.find(query).sort("upload_date", -1)
            files = []

            for file_doc in cursor:
                # 检查文件是否还存在
                if os.path.exists(file_doc['file_path']):
                    file_info = self.serialize_datetime(file_doc)
                    files.append(file_info)
                else:
                    # 文件不存在，删除数据库记录
                    logger.warning(f"文件不存在，删除记录: {file_doc['file_path']}")
                    self.files_collection.delete_one({"_id": file_doc["_id"]})

            logger.info(f"获取 {category} 类别文件: {len(files)} 个")
            return files

        except Exception as e:
            logger.error(f"获取文件列表失败: {e}")
            return []

    def get_project_files(self, project_id):
        """获取项目文件"""
        return self.get_files_by_category('project', project_id)

    def get_file_by_id(self, file_id):
        """根据ID获取文件"""
        try:
            file_doc = self.files_collection.find_one({"file_id": file_id})
            if file_doc and os.path.exists(file_doc['file_path']):
                return file_doc
            elif file_doc:
                # 文件记录存在但文件不存在，删除记录
                self.files_collection.delete_one({"_id": file_doc["_id"]})
                logger.warning(f"文件不存在，已删除记录: {file_doc['file_path']}")
            return None
        except Exception as e:
            logger.error(f"获取文件失败: {e}")
            return None

    def delete_file(self, file_id):
        """删除文件"""
        try:
            file_doc = self.files_collection.find_one({"file_id": file_id})
            if not file_doc:
                return False

            # 删除磁盘上的文件
            if os.path.exists(file_doc['file_path']):
                os.remove(file_doc['file_path'])

            # 删除数据库记录
            self.files_collection.delete_one({"_id": file_doc["_id"]})

            # 如果是项目文件，更新项目文件计数
            if file_doc.get('category') == 'project' and file_doc.get('project_id'):
                self.projects_collection.update_one(
                    {"_id": ObjectId(file_doc['project_id'])},
                    {"$inc": {"file_count": -1}, "$set": {"updated_at": datetime.now()}}
                )

            logger.info(f"成功删除文件: {file_doc['originalname']}")
            return True

        except Exception as e:
            logger.error(f"删除文件失败: {e}")
            return False


def create_json_response(data, status_code=200):
    """创建正确编码的JSON响应"""
    return app.response_class(
        response=json.dumps(data, ensure_ascii=False, indent=2),
        status=status_code,
        mimetype='application/json; charset=utf-8'
    )


# 初始化数据目录
init_data_directories()

# 创建MongoDB客户端实例
connection_string = "mongodb://localhost:27017/"
mongo_client = MongoDBClient(connection_string, "ai_resume-python")

# 解析服务配置（可根据实际情况放到 config.py 或环境变量）
PARSER_URL = 'https://ap-beijing.cloudmarket-apigw.com/service-9wsy8usn/ResumeParser'
PARSER_SECRET_ID = 'RrIawnDnCs4ha4hs'
PARSER_SECRET_KEY = 'JQSIHcT3xjgVAD1p33kvcn3I6KG4TcrB'
parser_service = ResumeParserService(PARSER_URL, PARSER_SECRET_ID, PARSER_SECRET_KEY)

# ============ 简历数据API ============
@app.route('/api/resume/latest', methods=['GET'])
def get_latest_resume():
    """获取最新的简历数据"""
    try:
        data = mongo_client.get_latest_result_data()
        if data:
            return create_json_response(data)
        else:
            return create_json_response({"error": "未找到简历数据"}, 404)
    except Exception as e:
        logger.error(f"API错误: {e}")
        return create_json_response({"error": "服务器内部错误"}, 500)


@app.route('/api/resume/all', methods=['GET'])
def get_all_resumes():
    """获取所有简历数据"""
    try:
        data = mongo_client.get_all_result_data()
        return create_json_response(data)
    except Exception as e:
        logger.error(f"API错误: {e}")
        return create_json_response({"error": "服务器内部错误"}, 500)


@app.route('/api/resume/<record_id>', methods=['GET'])
def get_resume_by_id(record_id):
    """根据ID获取特定简历数据"""
    try:
        data = mongo_client.get_result_data_by_id(record_id)
        if data:
            return create_json_response(data)
        else:
            return create_json_response({"error": "未找到指定简历数据"}, 404)
    except Exception as e:
        logger.error(f"API错误: {e}")
        return create_json_response({"error": "服务器内部错误"}, 500)


@app.route('/api/resume', methods=['POST'])
def save_resume():
    """保存简历数据"""
    try:
        data = request.get_json()
        if not data:
            return create_json_response({"error": "请求数据为空"}, 400)

        record_id = mongo_client.save_result_data(data)
        if record_id:
            return create_json_response({"message": "保存成功", "id": record_id}, 201)
        else:
            return create_json_response({"error": "保存失败"}, 500)
    except Exception as e:
        logger.error(f"API错误: {e}")
        return create_json_response({"error": "服务器内部错误"}, 500)


# ============ 项目管理API ============
@app.route('/api/projects', methods=['GET'])
def get_projects():
    """获取所有项目"""
    try:
        projects = mongo_client.get_all_projects()
        return create_json_response(projects)
    except Exception as e:
        logger.error(f"API错误: {e}")
        return create_json_response({"error": "服务器内部错误"}, 500)


@app.route('/api/projects', methods=['POST'])
def create_project():
    """创建新项目"""
    try:
        data = request.get_json()
        if not data or not data.get('name'):
            return create_json_response({"error": "项目名称不能为空"}, 400)

        name = data.get('name').strip()
        description = data.get('description', '').strip()

        project, error = mongo_client.create_project(name, description)
        if project:
            return create_json_response({
                "message": "项目创建成功",
                "project": project
            }, 201)
        else:
            return create_json_response({"error": error}, 400)

    except Exception as e:
        logger.error(f"API错误: {e}")
        return create_json_response({"error": "服务器内部错误"}, 500)


@app.route('/api/projects/<project_id>', methods=['GET'])
def get_project(project_id):
    """获取单个项目信息"""
    try:
        project = mongo_client.get_project_by_id(project_id)
        if project:
            return create_json_response(project)
        else:
            return create_json_response({"error": "项目不存在"}, 404)
    except Exception as e:
        logger.error(f"API错误: {e}")
        return create_json_response({"error": "服务器内部错误"}, 500)


@app.route('/api/projects/<project_id>', methods=['DELETE'])
def delete_project(project_id):
    """删除项目"""
    try:
        success = mongo_client.delete_project(project_id)

        if success:
            return create_json_response({"message": "项目删除成功"})
        else:
            return create_json_response({"error": "项目不存在或删除失败"}, 404)

    except Exception as e:
        logger.error(f"API错误: {e}")
        return create_json_response({"error": "服务器内部错误"}, 500)


# ============ 项目文件上传API ============
@app.route('/api/projects/<project_id>/files', methods=['POST'])
def upload_project_files(project_id):
    """上传文件到项目"""
    try:
        if 'files' not in request.files:
            return create_json_response({"error": "没有选择文件"}, 400)

        files = request.files.getlist('files')
        if not files or all(f.filename == '' for f in files):
            return create_json_response({"error": "没有选择文件"}, 400)

        # 获取项目信息，用于显示正确的项目名称
        project = mongo_client.get_project_by_id(project_id)
        if not project:
            return create_json_response({"error": "项目不存在"}, 404)

        uploaded_files = []
        errors = []

        for file in files:
            if file and file.filename != '':
                filename = secure_filename(file.filename)

                if not allowed_file(filename):
                    errors.append(f"文件类型不支持: {filename}")
                    continue

                file_info, error = mongo_client.upload_file(file, 'project', project_id, filename)
                if file_info:
                    uploaded_files.append(file_info)
                else:
                    errors.append(f"上传失败 {filename}: {error}")

        response_data = {
            "message": f"成功上传 {len(uploaded_files)} 个文件到项目: {project['name']}",
            "uploaded_files": uploaded_files,
            "project_name": project['name'],  # 添加项目名称到响应
            "project_id": project_id
        }

        if errors:
            response_data["errors"] = errors

        return create_json_response(response_data, 201)

    except Exception as e:
        logger.error(f"文件上传API错误: {e}")
        return create_json_response({"error": "服务器内部错误"}, 500)


@app.route('/api/projects/<project_id>/files', methods=['GET'])
def get_project_files(project_id):
    """获取项目文件列表"""
    try:
        files = mongo_client.get_project_files(project_id)
        return create_json_response(files)
    except Exception as e:
        logger.error(f"API错误: {e}")
        return create_json_response({"error": "服务器内部错误"}, 500)


# ============ 分类文件上传API ============
@app.route('/api/files/category/<category>', methods=['POST'])
def upload_category_files(category):
    """上传分类文件"""
    try:
        if category not in ['resume', 'company', 'job', 'knowledge']:
            return create_json_response({"error": "无效的文件类别"}, 400)

        if 'files' not in request.files:
            return create_json_response({"error": "没有选择文件"}, 400)

        files = request.files.getlist('files')
        if not files or all(f.filename == '' for f in files):
            return create_json_response({"error": "没有选择文件"}, 400)

        uploaded_files = []
        errors = []

        for file in files:
            if file and file.filename != '':
                filename = secure_filename(file.filename)

                if not allowed_file(filename):
                    errors.append(f"文件类型不支持: {filename}")
                    continue

                file_info, error = mongo_client.upload_file(file, category, None, filename)
                if file_info:
                    uploaded_files.append(file_info)
                else:
                    errors.append(f"上传失败 {filename}: {error}")

        response_data = {
            "message": f"成功上传 {len(uploaded_files)} 个文件到{FILE_CATEGORIES[category]}",
            "uploaded_files": uploaded_files
        }

        if errors:
            response_data["errors"] = errors

        return create_json_response(response_data, 201)

    except Exception as e:
        logger.error(f"分类文件上传API错误: {e}")
        return create_json_response({"error": "服务器内部错误"}, 500)


@app.route('/api/files/category/<category>', methods=['GET'])
def get_category_files(category):
    """获取分类文件列表"""
    try:
        if category not in ['resume', 'company', 'job', 'knowledge']:
            return create_json_response({"error": "无效的文件类别"}, 400)

        files = mongo_client.get_files_by_category(category)
        return create_json_response(files)
    except Exception as e:
        logger.error(f"API错误: {e}")
        return create_json_response({"error": "服务器内部错误"}, 500)


# ============ 通用文件操作API ============
@app.route('/api/files/<file_id>/download', methods=['GET'])
def download_file(file_id):
    """下载文件"""
    try:
        file_doc = mongo_client.get_file_by_id(file_id)
        if not file_doc:
            return create_json_response({"error": "文件不存在"}, 404)

        if not os.path.exists(file_doc['file_path']):
            return create_json_response({"error": "文件已被删除"}, 404)

        return send_file(
            file_doc['file_path'],
            as_attachment=True,
            download_name=file_doc['original_filename'],  # 修复：使用正确的字段名
            mimetype=file_doc.get('mimetype', 'application/octet-stream')
        )

    except Exception as e:
        logger.error(f"文件下载错误: {e}")
        return create_json_response({"error": "文件下载失败"}, 500)

@app.route('/api/files/<file_id>/parse-status', methods=['PUT'])
def update_parse_status(file_id):
    """更新文件解析状态"""
    try:
        data = request.get_json()
        if not data:
            return create_json_response({"error": "请求数据为空"}, 400)

        update_fields = {}
        if 'parse_status' in data:
            update_fields['parse_status'] = data['parse_status']
        if 'parse_enabled' in data:
            update_fields['parse_enabled'] = data['parse_enabled']
        if 'parse_result' in data:
            update_fields['parse_result'] = data['parse_result']
        if 'parse_error' in data:
            update_fields['parse_error'] = data['parse_error']

        if data.get('parse_status') == 'completed':
            update_fields['parse_date'] = datetime.now()

        update_fields['updated_at'] = datetime.now()

        result = mongo_client.files_collection.update_one(
            {"file_id": file_id},
            {"$set": update_fields}
        )

        if result.matched_count > 0:
            return create_json_response({"message": "解析状态更新成功"})
        else:
            return create_json_response({"error": "文件不存在"}, 404)

    except Exception as e:
        logger.error(f"更新解析状态失败: {e}")
        return create_json_response({"error": "服务器内部错误"}, 500)


@app.route('/api/files/<file_id>/parse', methods=['POST'])
def parse_file(file_id):
    """解析指定文件，保存解析历史"""
    try:
        # 1. 查找文件元数据
        file_doc = mongo_client.files_collection.find_one({"file_id": file_id})
        if not file_doc:
            return create_json_response({"error": "文件不存在"}, 404)
        file_path = file_doc.get("file_path")
        if not file_path or not os.path.exists(file_path):
            return create_json_response({"error": "文件路径无效或文件不存在"}, 404)

        # 2. 更新解析状态为 processing
        mongo_client.files_collection.update_one({"file_id": file_id}, {"$set": {"parse_status": "processing", "updated_at": datetime.now()}})

        # 3. 调用解析服务
        result = parser_service.parse(file_path)
        status = 'completed' if 'error' not in result else 'failed'
        error_msg = result.get('error') if status == 'failed' else None

        # 4. 保存解析历史到 parseresults 集合
        parse_record = {
            "file_id": file_id,
            "data": result,
            "status": status,
            "error": error_msg,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        mongo_client.collection.insert_one(parse_record)

        # 5. 更新文件元数据解析状态和结果
        mongo_client.files_collection.update_one(
            {"file_id": file_id},
            {"$set": {
                "parse_status": status,
                "parse_result": result,
                "parse_error": error_msg,
                "parse_date": datetime.now(),
                "updated_at": datetime.now()
            }}
        )
        return create_json_response({"message": "解析完成", "status": status, "result": result})
    except Exception as e:
        logger.error(f"解析文件失败: {e}")
        mongo_client.files_collection.update_one(
            {"file_id": file_id},
            {"$set": {"parse_status": "failed", "parse_error": str(e), "updated_at": datetime.now()}}
        )
        return create_json_response({"error": "解析失败", "detail": str(e)}, 500)


# ============ 系统信息API ============
@app.route('/api/system/info', methods=['GET'])
def get_system_info():
    """获取系统信息"""
    try:
        # 统计各类别文件数量
        file_stats = {}
        for category, display_name in FILE_CATEGORIES.items():
            if category == 'project':
                continue
            count = mongo_client.files_collection.count_documents({"category": category})
            file_stats[category] = {
                "name": display_name,
                "count": count
            }

        # 项目统计
        project_count = mongo_client.projects_collection.count_documents({})
        project_file_count = mongo_client.files_collection.count_documents({"category": "project"})

        # 磁盘使用情况
        data_dir_size = 0
        for root, dirs, files in os.walk(DATA_DIR):
            for file in files:
                file_path = os.path.join(root, file)
                if os.path.exists(file_path):
                    data_dir_size += os.path.getsize(file_path)

        system_info = {
            "data_directory": str(DATA_DIR),
            "file_categories": file_stats,
            "project_count": project_count,
            "project_file_count": project_file_count,
            "total_disk_usage": data_dir_size,
            "total_disk_usage_mb": round(data_dir_size / 1024 / 1024, 2)
        }

        return create_json_response(system_info)
    except Exception as e:
        logger.error(f"API错误: {e}")
        return create_json_response({"error": "服务器内部错误"}, 500)



@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查端点"""
    try:
        # 测试数据库连接
        mongo_client.db.command('ping')

        # 检查数据目录
        data_dir_exists = DATA_DIR.exists()

        return create_json_response({
            "status": "healthy",
            "message": "API服务正常运行",
            "encoding": "UTF-8 支持正常",
            "database": "连接正常",
            "data_directory": str(DATA_DIR),
            "data_directory_exists": data_dir_exists,
            "file_storage": "本地存储",
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return create_json_response({
            "status": "unhealthy",
            "message": "服务异常",
            "error": str(e)
        }, 500)


# ============ 错误处理 ============
@app.errorhandler(404)
def not_found(error):
    return create_json_response({"error": "API端点不存在"}, 404)


@app.errorhandler(500)
def internal_error(error):
    return create_json_response({"error": "服务器内部错误"}, 500)


@app.errorhandler(413)
def too_large(error):
    return create_json_response({"error": "文件过大，最大限制100MB"}, 413)


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

    print("=== AI简历分析系统 API服务启动 ===")
    print(f"🚀 服务运行在: http://localhost:{port}")
    print(f"📁 数据目录: {DATA_DIR}")
    print("📋 API端点说明：")
    print("📊 简历数据：")
    print(f"  GET  http://localhost:{port}/api/resume/latest - 获取最新简历数据")
    print(f"  GET  http://localhost:{port}/api/resume/all - 获取所有简历数据")
    print(f"  GET  http://localhost:{port}/api/resume/<id> - 根据ID获取特定简历数据")
    print(f"  POST http://localhost:{port}/api/resume - 保存简历数据")
    print("🗂️ 项目管理：")
    print(f"  GET  http://localhost:{port}/api/projects - 获取所有项目")
    print(f"  POST http://localhost:{port}/api/projects - 创建新项目")
    print(f"  GET  http://localhost:{port}/api/projects/<id> - 获取项目信息")
    print(f"  DELETE http://localhost:{port}/api/projects/<id> - 删除项目")
    print("📁 项目文件管理：")
    print(f"  POST http://localhost:{port}/api/projects/<id>/files - 上传文件到项目")
    print(f"  GET  http://localhost:{port}/api/projects/<id>/files - 获取项目文件列表")
    print("📄 分类文件管理：")
    print(f"  POST http://localhost:{port}/api/files/category/<category> - 上传分类文件")
    print(f"  GET  http://localhost:{port}/api/files/category/<category> - 获取分类文件列表")
    print("🔧 文件操作：")
    print(f"  GET  http://localhost:{port}/api/files/<id>/download - 下载文件")
    print(f"  DELETE http://localhost:{port}/api/files/<id> - 删除文件")
    print("🔧 系统：")
    print(f"  GET  http://localhost:{port}/api/health - 健康检查")
    print(f"  GET  http://localhost:{port}/api/system/info - 系统信息")
    print("=====================================")
    print("💾 文件存储方式：本地文件系统")
    print("📂 文件分类：")
    print("  - data/resume/ - 个人简历")
    print("  - data/company/ - 公司介绍")
    print("  - data/job/ - 工作条件")
    print("  - data/knowledge/ - 知识纪要")
    print("  - data/projects/<project_id>/ - 项目文件")
    print("🗃️ 数据库：只存储文件元数据")
    print("=====================================")

    try:
        # 启动Flask服务
        app.run(
            host='127.0.0.1',
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
        print("5. 确保MongoDB服务正在运行")