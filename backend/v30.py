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
import requests
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
        """获取parseresults集合中所有文档的自定义数据字段"""
        try:
            cursor = self.collection.find({}, {"custom_data": 1, "original_data": 1, "_id": 1})
            results = []

            for document in cursor:
                # 优先使用自定义数据结构，如果没有则使用原始数据
                if "custom_data" in document and document["custom_data"]:
                    result_data = document["custom_data"]
                    # 处理编码
                    result_data = self.ensure_utf8_encoding(result_data)
                    # 添加MongoDB的_id字段
                    result_data["_id"] = str(document["_id"])
                    results.append(result_data)
                elif "original_data" in document and "result" in document["original_data"]:
                    # 如果没有自定义数据，则使用原始数据并尝试映射
                    original_result = document["original_data"]["result"]
                    result_data = self.map_parser_result_to_custom_structure(original_result)
                    result_data = self.ensure_utf8_encoding(result_data)
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
            cursor = self.collection.find({}, {"custom_data": 1, "original_data": 1, "_id": 1}).sort("_id", -1).limit(1)

            for document in cursor:
                # 优先使用自定义数据结构，如果没有则使用原始数据
                if "custom_data" in document and document["custom_data"]:
                    result_data = document["custom_data"]
                    # 处理编码
                    result_data = self.ensure_utf8_encoding(result_data)
                    result_data["_id"] = str(document["_id"])
                    logger.info(f"成功获取最新记录: {document['_id']}")
                    return result_data
                elif "original_data" in document and "result" in document["original_data"]:
                    # 如果没有自定义数据，则使用原始数据并尝试映射
                    original_result = document["original_data"]["result"]
                    result_data = self.map_parser_result_to_custom_structure(original_result)
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
                {"custom_data": 1, "original_data": 1, "_id": 1}
            )

            if document:
                # 优先使用自定义数据结构，如果没有则使用原始数据
                if "custom_data" in document and document["custom_data"]:
                    result_data = document["custom_data"]
                    # 处理编码
                    result_data = self.ensure_utf8_encoding(result_data)
                    result_data["_id"] = str(document["_id"])
                    logger.info(f"成功获取指定记录: {record_id}")
                    return result_data
                elif "original_data" in document and "result" in document["original_data"]:
                    # 如果没有自定义数据，则使用原始数据并尝试映射
                    original_result = document["original_data"]["result"]
                    result_data = self.map_parser_result_to_custom_structure(original_result)
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
                "custom_data": data,  # 使用自定义数据结构
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

    def update_project_name(self, project_id, new_name):
        """修改项目名称"""
        try:
            # 检查新名称是否已存在（排除自身）
            existing = self.projects_collection.find_one({"name": new_name, "_id": {"$ne": ObjectId(project_id)}})
            if existing:
                return None, "项目名称已存在"
            result = self.projects_collection.update_one(
                {"_id": ObjectId(project_id)},
                {"$set": {"name": new_name, "updated_at": datetime.now()}}
            )
            if result.matched_count == 0:
                return None, "项目不存在"
            # 返回更新后的项目
            project = self.get_project_by_id(project_id)
            return project, None
        except Exception as e:
            logger.error(f"修改项目名称失败: {e}")
            return None, str(e)

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
                "parse_date": None,         # 解析完成时间
                # 添加RAG同步状态相关字段
                "sync_status": "pending",   # pending, processing, completed, failed
                "sync_enabled": True,       # 是否启用同步
                "sync_result": None,        # 同步结果
                "sync_error": None,         # 同步错误信息
                "sync_date": None           # 同步完成时间
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
            # 获取文件信息
            file_doc = self.files_collection.find_one({"file_id": file_id})
            if not file_doc:
                return False
            
            # 删除物理文件
            file_path = file_doc.get("file_path")
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logger.info(f"删除物理文件: {file_path}")
                except Exception as e:
                    logger.warning(f"删除物理文件失败: {e}")
            
            # 删除数据库记录
            result = self.files_collection.delete_one({"file_id": file_id})
            
            if result.deleted_count > 0:
                # 如果是项目文件，更新项目文件计数
                if file_doc.get("category") == "project" and file_doc.get("project_id"):
                    self.projects_collection.update_one(
                        {"_id": ObjectId(file_doc["project_id"])},
                        {"$inc": {"file_count": -1}, "$set": {"updated_at": datetime.now()}}
                    )
                
                logger.info(f"成功删除文件: {file_id}")
                return True
            else:
                logger.warning(f"文件删除失败: {file_id}")
                return False
                
        except Exception as e:
            logger.error(f"删除文件失败: {e}")
            return False

    def map_parser_result_to_custom_structure(self, parser_result):
        """
        将第三方API解析结果映射到自定义数据库结构
        完全按照ResumeSDK官方文档的字段结构进行映射
        """
        try:
            custom_data = {}
            
            # 基本信息映射 - 对应官方文档的"基本信息"模块
            if 'profile' in parser_result:
                profile = parser_result['profile']
                custom_data.update({
                    'name': profile.get('name', ''),
                    'gender': profile.get('gender', ''),
                    'age': profile.get('age', ''),
                    'birthday': profile.get('birthday', ''),
                    'mobile': profile.get('mobile', ''),
                    'email': profile.get('email', ''),
                    'living_address': profile.get('living_address', ''),
                    'hometown_address': profile.get('hometown_address', ''),
                    'hukou_address': profile.get('hukou_address', ''),
                    'city': profile.get('city', ''),
                    'race': profile.get('race', ''),
                    'surname': profile.get('surname', ''),
                    'workExpYear': profile.get('workExpYear', ''),
                    'github': profile.get('github', ''),
                    'zhihu': profile.get('zhihu', ''),
                    'wechat': profile.get('wechat', ''),
                    'qq': profile.get('qq', ''),
                    'linkedin': profile.get('linkedin', ''),
                    'blog': profile.get('blog', ''),
                    'website': profile.get('website', ''),
                    'avatar': profile.get('avatar', ''),
                    'expect_job': profile.get('expect_job', ''),
                    'expect_salary': profile.get('expect_salary', ''),
                    'expect_city': profile.get('expect_city', ''),
                    'expect_industry': profile.get('expect_industry', ''),
                    'resume_name': profile.get('resume_name', ''),
                    'resume_update_time': profile.get('resume_update_time', ''),
                    'resume_text': profile.get('resume_text', '')
                })
            
            # 从其他字段提取基本信息
            custom_data.update({
                'gender': parser_result.get('gender', custom_data.get('gender', '')),
                'age': parser_result.get('age', custom_data.get('age', '')),
                'birthday': parser_result.get('birthday', custom_data.get('birthday', '')),
                'mobile': parser_result.get('mobile', parser_result.get('phone', custom_data.get('mobile', ''))),
                'email': parser_result.get('email', custom_data.get('email', '')),
                'living_address': parser_result.get('living_address', custom_data.get('living_address', '')),
                'hometown_address': parser_result.get('hometown_address', custom_data.get('hometown_address', '')),
                'hukou_address': parser_result.get('hukou_address', custom_data.get('hukou_address', '')),
                'city': parser_result.get('city', custom_data.get('city', '')),
                'race': parser_result.get('race', custom_data.get('race', '')),
                'surname': parser_result.get('surname', custom_data.get('surname', '')),
                'workExpYear': parser_result.get('workExpYear', custom_data.get('workExpYear', '')),
                'github': parser_result.get('github', custom_data.get('github', '')),
                'zhihu': parser_result.get('zhihu', custom_data.get('zhihu', '')),
                'wechat': parser_result.get('wechat', custom_data.get('wechat', '')),
                'qq': parser_result.get('qq', custom_data.get('qq', '')),
                'linkedin': parser_result.get('linkedin', custom_data.get('linkedin', '')),
                'blog': parser_result.get('blog', custom_data.get('blog', '')),
                'website': parser_result.get('website', custom_data.get('website', '')),
                'avatar': parser_result.get('avatar', custom_data.get('avatar', '')),
                'expect_job': parser_result.get('expect_job', custom_data.get('expect_job', '')),
                'expect_salary': parser_result.get('expect_salary', custom_data.get('expect_salary', '')),
                'expect_city': parser_result.get('expect_city', custom_data.get('expect_city', '')),
                'expect_industry': parser_result.get('expect_industry', custom_data.get('expect_industry', '')),
                'resume_name': parser_result.get('resume_name', custom_data.get('resume_name', '')),
                'resume_update_time': parser_result.get('resume_update_time', custom_data.get('resume_update_time', '')),
                'resume_text': parser_result.get('resume_text', custom_data.get('resume_text', ''))
            })
            
            # 教育经历映射 - 对应官方文档的"教育经历"模块
            if 'educationList' in parser_result and isinstance(parser_result['educationList'], list):
                education_list = parser_result['educationList']
                if education_list:
                    # 取最新的教育经历作为主要教育信息
                    latest_education = education_list[0]
                    custom_data.update({
                        'college': latest_education.get('college', ''),
                        'major': latest_education.get('major', ''),
                        'education': latest_education.get('education', ''),
                        'degree': latest_education.get('degree', ''),
                        'college_type': latest_education.get('college_type', ''),
                        'college_rank': latest_education.get('college_rank', ''),
                        'grad_time': latest_education.get('grad_time', ''),
                        'education_start_time': latest_education.get('education_start_time', ''),
                        'education_end_time': latest_education.get('education_end_time', ''),
                        'gpa': latest_education.get('gpa', ''),
                        'course': latest_education.get('course', ''),
                        'education_desc': latest_education.get('education_desc', '')
                    })
                # 保存完整的教育经历列表
                custom_data['educationList'] = education_list
            
            # 从其他字段提取教育信息
            custom_data.update({
                'college': parser_result.get('college', custom_data.get('college', '')),
                'major': parser_result.get('major', custom_data.get('major', '')),
                'education': parser_result.get('education', parser_result.get('degree', custom_data.get('education', ''))),
                'degree': parser_result.get('degree', custom_data.get('degree', '')),
                'college_type': parser_result.get('college_type', custom_data.get('college_type', '')),
                'college_rank': parser_result.get('college_rank', custom_data.get('college_rank', '')),
                'grad_time': parser_result.get('grad_time', custom_data.get('grad_time', '')),
                'education_start_time': parser_result.get('education_start_time', custom_data.get('education_start_time', '')),
                'education_end_time': parser_result.get('education_end_time', custom_data.get('education_end_time', '')),
                'gpa': parser_result.get('gpa', custom_data.get('gpa', '')),
                'course': parser_result.get('course', custom_data.get('course', '')),
                'education_desc': parser_result.get('education_desc', custom_data.get('education_desc', ''))
            })
            
            # 工作经历映射 - 对应官方文档的"工作经历及实习经历"模块
            work_experience = []
            if 'workExpList' in parser_result and isinstance(parser_result['workExpList'], list):
                for work in parser_result['workExpList']:
                    work_experience.append({
                        'company_name': work.get('company_name', ''),
                        'department_name': work.get('department_name', ''),
                        'job_position': work.get('job_position', ''),
                        'work_time': work.get('work_time', []),
                        'work_start_time': work.get('work_start_time', ''),
                        'work_end_time': work.get('work_end_time', ''),
                        'work_desc': work.get('work_desc', ''),
                        'salary': work.get('salary', ''),
                        'work_type': work.get('work_type', ''),
                        'industry': work.get('industry', ''),
                        'company_size': work.get('company_size', ''),
                        'company_nature': work.get('company_nature', ''),
                        'report_to': work.get('report_to', ''),
                        'subordinates': work.get('subordinates', ''),
                        'achievement': work.get('achievement', '')
                    })
            elif 'job_exp_objs' in parser_result and isinstance(parser_result['job_exp_objs'], list):
                for job in parser_result['job_exp_objs']:
                    work_experience.append({
                        'company_name': job.get('job_cpy', ''),
                        'department_name': job.get('department_name', ''),
                        'job_position': job.get('job_position', ''),
                        'work_time': [job.get('start_date', ''), job.get('end_date', '')],
                        'work_start_time': job.get('start_date', ''),
                        'work_end_time': job.get('end_date', ''),
                        'work_desc': job.get('job_content', ''),
                        'salary': job.get('salary', ''),
                        'work_type': job.get('work_type', ''),
                        'industry': job.get('industry', ''),
                        'company_size': job.get('company_size', ''),
                        'company_nature': job.get('company_nature', ''),
                        'report_to': job.get('report_to', ''),
                        'subordinates': job.get('subordinates', ''),
                        'achievement': job.get('achievement', '')
                    })
            
            custom_data['work_experience'] = work_experience
            
            # 项目经历映射 - 对应官方文档的"项目经历"模块
            project_experience = []
            if 'projectList' in parser_result and isinstance(parser_result['projectList'], list):
                for project in parser_result['projectList']:
                    project_experience.append({
                        'project_name': project.get('project_name', ''),
                        'project_role': project.get('project_role', ''),
                        'project_time': project.get('project_time', ''),
                        'project_start_time': project.get('project_start_time', ''),
                        'project_end_time': project.get('project_end_time', ''),
                        'project_desc': project.get('project_desc', ''),
                        'project_content': project.get('project_content', ''),
                        'project_technology': project.get('project_technology', ''),
                        'project_result': project.get('project_result', ''),
                        'project_scale': project.get('project_scale', ''),
                        'project_budget': project.get('project_budget', ''),
                        'project_team_size': project.get('project_team_size', '')
                    })
            
            custom_data['project_experience'] = project_experience
            
            # 技能列表映射 - 对应官方文档的"技能列表"模块
            skills = []
            if 'skillList' in parser_result and isinstance(parser_result['skillList'], list):
                for skill in parser_result['skillList']:
                    skills.append({
                        'skill_name': skill.get('skill_name', ''),
                        'skill_level': skill.get('skill_level', ''),
                        'skill_desc': skill.get('skill_desc', ''),
                        'skill_years': skill.get('skill_years', ''),
                        'skill_category': skill.get('skill_category', '')
                    })
            elif 'skills_objs' in parser_result and isinstance(parser_result['skills_objs'], list):
                for skill in parser_result['skills_objs']:
                    skills.append({
                        'skill_name': skill.get('skills_name', ''),
                        'skill_level': skill.get('skills_level', ''),
                        'skill_desc': skill.get('skills_desc', ''),
                        'skill_years': skill.get('skill_years', ''),
                        'skill_category': skill.get('skill_category', '')
                    })
            
            custom_data['skills'] = skills
            
            # 语言技能映射 - 对应官方文档的"语言技能"模块
            language_skills = []
            if 'languageList' in parser_result and isinstance(parser_result['languageList'], list):
                for language in parser_result['languageList']:
                    language_skills.append({
                        'language_name': language.get('language_name', ''),
                        'language_level': language.get('language_level', ''),
                        'language_certificate': language.get('language_certificate', ''),
                        'language_score': language.get('language_score', '')
                    })
            
            custom_data['language_skills'] = language_skills
            
            # 证书奖项映射 - 对应官方文档的"所有证书及奖项"模块
            certificates = []
            if 'awardList' in parser_result and isinstance(parser_result['awardList'], list):
                for award in parser_result['awardList']:
                    certificates.append({
                        'award_info': award.get('award_info', ''),
                        'award_time': award.get('award_time', ''),
                        'award_desc': award.get('award_desc', ''),
                        'award_level': award.get('award_level', ''),
                        'award_issuer': award.get('award_issuer', ''),
                        'certificate_type': award.get('certificate_type', '')
                    })
            
            custom_data['certificates'] = certificates
            
            # 培训经历映射 - 对应官方文档的"培训经历"模块
            training = []
            if 'training' in parser_result and isinstance(parser_result['training'], list):
                for train in parser_result['training']:
                    training.append({
                        'training_name': train.get('training_name', ''),
                        'training_time': train.get('training_time', ''),
                        'training_desc': train.get('training_desc', ''),
                        'training_institution': train.get('training_institution', ''),
                        'training_certificate': train.get('training_certificate', ''),
                        'training_duration': train.get('training_duration', '')
                    })
            
            custom_data['training'] = training
            
            # 社会实践映射 - 对应官方文档的"社会及学校实践经历"模块
            social_practice = []
            if 'practiceList' in parser_result and isinstance(parser_result['practiceList'], list):
                for practice in parser_result['practiceList']:
                    social_practice.append({
                        'practice_name': practice.get('practice_name', ''),
                        'practice_time': practice.get('practice_time', ''),
                        'practice_desc': practice.get('practice_desc', ''),
                        'practice_role': practice.get('practice_role', ''),
                        'practice_organization': practice.get('practice_organization', '')
                    })
            
            custom_data['social_practice'] = social_practice
            
            # 个人评价映射 - 对应官方文档的"基本信息-文本内容"模块
            if 'aboutme' in parser_result:
                aboutme = parser_result['aboutme']
                custom_data.update({
                    'aboutme_desc': aboutme.get('aboutme_desc', ''),
                    'self_introduction': aboutme.get('self_introduction', ''),
                    'hobby': aboutme.get('hobby', ''),
                    'strength': aboutme.get('strength', ''),
                    'weakness': aboutme.get('weakness', ''),
                    'career_goal': aboutme.get('career_goal', '')
                })
            
            # 保留原始数据中的其他字段
            for key, value in parser_result.items():
                if key not in ['profile', 'educationList', 'workExpList', 'projectList', 'skillList', 'languageList', 'awardList', 'training', 'practiceList', 'aboutme', 'job_exp_objs', 'skills_objs']:
                    custom_data[f'custom_{key}'] = value
            
            logger.info(f"数据映射完成，共映射 {len(custom_data)} 个字段")
            return custom_data
            
        except Exception as e:
            logger.error(f"数据映射失败: {e}")
            return parser_result  # 如果映射失败，返回原始数据


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

# 自定义数据库结构定义 - 基于ResumeSDK官方文档
CUSTOM_FIELD_STRUCTURE = {
    # 基本信息 - 对应官方文档的"基本信息"模块
    'basic_info': {
        'name': {'type': 'string', 'label': '姓名', 'required': True, 'order': 1},
        'gender': {'type': 'string', 'label': '性别', 'required': False, 'order': 2},
        'age': {'type': 'number', 'label': '年龄', 'required': False, 'order': 3},
        'birthday': {'type': 'string', 'label': '出生日期', 'required': False, 'order': 4},
        'mobile': {'type': 'string', 'label': '手机号码', 'required': False, 'order': 5},
        'email': {'type': 'string', 'label': '邮箱', 'required': False, 'order': 6},
        'living_address': {'type': 'string', 'label': '居住地址', 'required': False, 'order': 7},
        'hometown_address': {'type': 'string', 'label': '籍贯地址', 'required': False, 'order': 8},
        'hukou_address': {'type': 'string', 'label': '户口地址', 'required': False, 'order': 9},
        'city': {'type': 'string', 'label': '所在城市', 'required': False, 'order': 10},
        'race': {'type': 'string', 'label': '民族', 'required': False, 'order': 11},
        'surname': {'type': 'string', 'label': '姓氏', 'required': False, 'order': 12},
        'workExpYear': {'type': 'string', 'label': '工作年限', 'required': False, 'order': 13},
        'github': {'type': 'string', 'label': 'GitHub', 'required': False, 'order': 14},
        'zhihu': {'type': 'string', 'label': '知乎', 'required': False, 'order': 15},
        'wechat': {'type': 'string', 'label': '微信', 'required': False, 'order': 16},
        'qq': {'type': 'string', 'label': 'QQ', 'required': False, 'order': 17},
        'linkedin': {'type': 'string', 'label': 'LinkedIn', 'required': False, 'order': 18},
        'blog': {'type': 'string', 'label': '个人博客', 'required': False, 'order': 19},
        'website': {'type': 'string', 'label': '个人网站', 'required': False, 'order': 20},
        'avatar': {'type': 'string', 'label': '头像', 'required': False, 'order': 21},
        'expect_job': {'type': 'string', 'label': '期望职位', 'required': False, 'order': 22},
        'expect_salary': {'type': 'string', 'label': '期望薪资', 'required': False, 'order': 23},
        'expect_city': {'type': 'string', 'label': '期望城市', 'required': False, 'order': 24},
        'expect_industry': {'type': 'string', 'label': '期望行业', 'required': False, 'order': 25},
        'resume_name': {'type': 'string', 'label': '简历名称', 'required': False, 'order': 26},
        'resume_update_time': {'type': 'string', 'label': '简历更新时间', 'required': False, 'order': 27},
        'resume_text': {'type': 'text', 'label': '简历文本内容', 'required': False, 'order': 28}
    },
    
    # 教育经历 - 对应官方文档的"教育经历"模块
    'education': {
        'college': {'type': 'string', 'label': '学校名称', 'required': False, 'order': 1},
        'major': {'type': 'string', 'label': '专业', 'required': False, 'order': 2},
        'education': {'type': 'string', 'label': '学历', 'required': False, 'order': 3},
        'degree': {'type': 'string', 'label': '学位', 'required': False, 'order': 4},
        'college_type': {'type': 'string', 'label': '学校类型', 'required': False, 'order': 5},
        'college_rank': {'type': 'string', 'label': '学校排名', 'required': False, 'order': 6},
        'grad_time': {'type': 'string', 'label': '毕业时间', 'required': False, 'order': 7},
        'education_start_time': {'type': 'string', 'label': '入学时间', 'required': False, 'order': 8},
        'education_end_time': {'type': 'string', 'label': '毕业时间', 'required': False, 'order': 9},
        'gpa': {'type': 'string', 'label': 'GPA', 'required': False, 'order': 10},
        'course': {'type': 'text', 'label': '主修课程', 'required': False, 'order': 11},
        'education_desc': {'type': 'text', 'label': '教育经历描述', 'required': False, 'order': 12}
    },
    
    # 工作经历 - 对应官方文档的"工作经历及实习经历"模块
    'work_experience': {
        'company_name': {'type': 'string', 'label': '公司名称', 'required': False, 'order': 1},
        'department_name': {'type': 'string', 'label': '部门名称', 'required': False, 'order': 2},
        'job_position': {'type': 'string', 'label': '职位', 'required': False, 'order': 3},
        'work_time': {'type': 'array', 'label': '工作时间', 'required': False, 'order': 4},
        'work_start_time': {'type': 'string', 'label': '开始时间', 'required': False, 'order': 5},
        'work_end_time': {'type': 'string', 'label': '结束时间', 'required': False, 'order': 6},
        'work_desc': {'type': 'text', 'label': '工作描述', 'required': False, 'order': 7},
        'salary': {'type': 'string', 'label': '薪资', 'required': False, 'order': 8},
        'work_type': {'type': 'string', 'label': '工作类型', 'required': False, 'order': 9},
        'industry': {'type': 'string', 'label': '行业', 'required': False, 'order': 10},
        'company_size': {'type': 'string', 'label': '公司规模', 'required': False, 'order': 11},
        'company_nature': {'type': 'string', 'label': '公司性质', 'required': False, 'order': 12},
        'report_to': {'type': 'string', 'label': '汇报对象', 'required': False, 'order': 13},
        'subordinates': {'type': 'string', 'label': '下属人数', 'required': False, 'order': 14},
        'achievement': {'type': 'text', 'label': '工作成就', 'required': False, 'order': 15}
    },
    
    # 项目经历 - 对应官方文档的"项目经历"模块
    'project_experience': {
        'project_name': {'type': 'string', 'label': '项目名称', 'required': False, 'order': 1},
        'project_role': {'type': 'string', 'label': '项目角色', 'required': False, 'order': 2},
        'project_time': {'type': 'string', 'label': '项目时间', 'required': False, 'order': 3},
        'project_start_time': {'type': 'string', 'label': '开始时间', 'required': False, 'order': 4},
        'project_end_time': {'type': 'string', 'label': '结束时间', 'required': False, 'order': 5},
        'project_desc': {'type': 'text', 'label': '项目描述', 'required': False, 'order': 6},
        'project_content': {'type': 'text', 'label': '项目内容', 'required': False, 'order': 7},
        'project_technology': {'type': 'text', 'label': '项目技术', 'required': False, 'order': 8},
        'project_result': {'type': 'text', 'label': '项目成果', 'required': False, 'order': 9},
        'project_scale': {'type': 'string', 'label': '项目规模', 'required': False, 'order': 10},
        'project_budget': {'type': 'string', 'label': '项目预算', 'required': False, 'order': 11},
        'project_team_size': {'type': 'string', 'label': '团队规模', 'required': False, 'order': 12}
    },
    
    # 技能列表 - 对应官方文档的"技能列表"模块
    'skills': {
        'skill_name': {'type': 'string', 'label': '技能名称', 'required': False, 'order': 1},
        'skill_level': {'type': 'string', 'label': '技能等级', 'required': False, 'order': 2},
        'skill_desc': {'type': 'text', 'label': '技能描述', 'required': False, 'order': 3},
        'skill_years': {'type': 'string', 'label': '技能年限', 'required': False, 'order': 4},
        'skill_category': {'type': 'string', 'label': '技能类别', 'required': False, 'order': 5}
    },
    
    # 语言技能 - 对应官方文档的"语言技能"模块
    'language_skills': {
        'language_name': {'type': 'string', 'label': '语言名称', 'required': False, 'order': 1},
        'language_level': {'type': 'string', 'label': '语言等级', 'required': False, 'order': 2},
        'language_certificate': {'type': 'string', 'label': '语言证书', 'required': False, 'order': 3},
        'language_score': {'type': 'string', 'label': '语言分数', 'required': False, 'order': 4}
    },
    
    # 证书奖项 - 对应官方文档的"所有证书及奖项"模块
    'certificates': {
        'award_info': {'type': 'string', 'label': '证书/奖项名称', 'required': False, 'order': 1},
        'award_time': {'type': 'string', 'label': '获得时间', 'required': False, 'order': 2},
        'award_desc': {'type': 'text', 'label': '证书/奖项描述', 'required': False, 'order': 3},
        'award_level': {'type': 'string', 'label': '证书/奖项级别', 'required': False, 'order': 4},
        'award_issuer': {'type': 'string', 'label': '颁发机构', 'required': False, 'order': 5},
        'certificate_type': {'type': 'string', 'label': '证书类型', 'required': False, 'order': 6}
    },
    
    # 培训经历 - 对应官方文档的"培训经历"模块
    'training': {
        'training_name': {'type': 'string', 'label': '培训名称', 'required': False, 'order': 1},
        'training_time': {'type': 'string', 'label': '培训时间', 'required': False, 'order': 2},
        'training_desc': {'type': 'text', 'label': '培训描述', 'required': False, 'order': 3},
        'training_institution': {'type': 'string', 'label': '培训机构', 'required': False, 'order': 4},
        'training_certificate': {'type': 'string', 'label': '培训证书', 'required': False, 'order': 5},
        'training_duration': {'type': 'string', 'label': '培训时长', 'required': False, 'order': 6}
    },
    
    # 社会实践 - 对应官方文档的"社会及学校实践经历"模块
    'social_practice': {
        'practice_name': {'type': 'string', 'label': '实践名称', 'required': False, 'order': 1},
        'practice_time': {'type': 'string', 'label': '实践时间', 'required': False, 'order': 2},
        'practice_desc': {'type': 'text', 'label': '实践描述', 'required': False, 'order': 3},
        'practice_role': {'type': 'string', 'label': '实践角色', 'required': False, 'order': 4},
        'practice_organization': {'type': 'string', 'label': '实践组织', 'required': False, 'order': 5}
    },
    
    # 个人评价 - 对应官方文档的"基本信息-文本内容"模块
    'self_evaluation': {
        'aboutme_desc': {'type': 'text', 'label': '个人评价', 'required': False, 'order': 1},
        'self_introduction': {'type': 'text', 'label': '自我介绍', 'required': False, 'order': 2},
        'hobby': {'type': 'text', 'label': '兴趣爱好', 'required': False, 'order': 3},
        'strength': {'type': 'text', 'label': '个人优势', 'required': False, 'order': 4},
        'weakness': {'type': 'text', 'label': '个人劣势', 'required': False, 'order': 5},
        'career_goal': {'type': 'text', 'label': '职业目标', 'required': False, 'order': 6}
    }
}

# 字段分组显示配置 - 基于ResumeSDK官方文档结构
FIELD_GROUPS_DISPLAY = {
    'basic_info': {'name': '基本信息', 'icon': '👤', 'order': 1, 'description': '个人基本信息和联系方式'},
    'education': {'name': '教育经历', 'icon': '🎓', 'order': 2, 'description': '学历教育背景'},
    'work_experience': {'name': '工作经历', 'icon': '🏢', 'order': 3, 'description': '工作及实习经历'},
    'project_experience': {'name': '项目经历', 'icon': '📋', 'order': 4, 'description': '项目经验'},
    'skills': {'name': '技能列表', 'icon': '💻', 'order': 5, 'description': '专业技能'},
    'language_skills': {'name': '语言技能', 'icon': '🌍', 'order': 6, 'description': '语言能力'},
    'certificates': {'name': '证书奖项', 'icon': '🏆', 'order': 7, 'description': '证书和获奖情况'},
    'training': {'name': '培训经历', 'icon': '📚', 'order': 8, 'description': '培训学习经历'},
    'social_practice': {'name': '社会实践', 'icon': '🤝', 'order': 9, 'description': '社会及学校实践'},
    'self_evaluation': {'name': '个人评价', 'icon': '📝', 'order': 10, 'description': '个人评价和介绍'}
}

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


@app.route('/api/resume/<record_id>', methods=['PUT'])
def update_resume(record_id):
    """更新指定简历数据，支持动态字段结构"""
    try:
        data = request.get_json()
        if not data:
            return create_json_response({"error": "请求数据为空"}, 400)
        # 直接更新 data.result 字段，支持任意结构
        result = mongo_client.collection.update_one(
            {"_id": ObjectId(record_id)},
            {"$set": {"custom_data": data, "updated_at": datetime.now()}}
        )
        if result.matched_count > 0:
            return create_json_response({"message": "更新成功"})
        else:
            return create_json_response({"error": "未找到指定简历"}, 404)
    except Exception as e:
        logger.error(f"简历更新失败: {e}")
        return create_json_response({"error": "服务器内部错误", "detail": str(e)}, 500)


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


@app.route('/api/resume/<record_id>', methods=['DELETE'])
def delete_resume(record_id):
    """删除指定简历数据"""
    try:
        result = mongo_client.collection.delete_one({"_id": ObjectId(record_id)})
        if result.deleted_count > 0:
            return create_json_response({"message": "删除成功"})
        else:
            return create_json_response({"error": "未找到指定简历"}, 404)
    except Exception as e:
        logger.error(f"简历删除失败: {e}")
        return create_json_response({"error": "服务器内部错误", "detail": str(e)}, 500)


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


@app.route('/api/projects/<project_id>/name', methods=['PUT'])
def update_project_name(project_id):
    """修改项目名称"""
    try:
        data = request.get_json()
        if not data or not data.get('name'):
            return create_json_response({"error": "项目名称不能为空"}, 400)
        new_name = data.get('name').strip()
        project, error = mongo_client.update_project_name(project_id, new_name)
        if project:
            return create_json_response({
                "message": "项目名称修改成功",
                "project": project
            })
        else:
            return create_json_response({"error": error}, 400)
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

        # 4. 数据映射转换
        custom_data = None
        if status == 'completed' and 'result' in result:
            # 将第三方API结果映射到自定义结构
            custom_data = mongo_client.map_parser_result_to_custom_structure(result['result'])
            logger.info(f"解析结果已映射到自定义结构，字段数: {len(custom_data)}")

        # 5. 保存解析历史到 parseresults 集合
        parse_record = {
            "file_id": file_id,
            "original_data": result,  # 保存原始解析结果
            "custom_data": custom_data,  # 保存映射后的自定义数据
            "status": status,
            "error": error_msg,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        mongo_client.collection.insert_one(parse_record)

        # 6. 更新文件元数据解析状态和结果
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
        
        response_data = {
            "message": "解析完成", 
            "status": status, 
            "original_result": result,
            "custom_data": custom_data
        }
        return create_json_response(response_data)
        
    except Exception as e:
        logger.error(f"解析文件失败: {e}")
        mongo_client.files_collection.update_one(
            {"file_id": file_id},
            {"$set": {"parse_status": "failed", "parse_error": str(e), "updated_at": datetime.now()}}
        )
        return create_json_response({"error": "解析失败", "detail": str(e)}, 500)


@app.route('/api/files/<file_id>/sync-status', methods=['PUT'])
def update_sync_status(file_id):
    """更新文件同步状态"""
    try:
        data = request.get_json()
        if not data:
            return create_json_response({"error": "请求数据为空"}, 400)

        update_fields = {}
        if 'sync_status' in data:
            update_fields['sync_status'] = data['sync_status']
        if 'sync_enabled' in data:
            update_fields['sync_enabled'] = data['sync_enabled']
        if 'sync_result' in data:
            update_fields['sync_result'] = data['sync_result']
        if 'sync_error' in data:
            update_fields['sync_error'] = data['sync_error']

        if data.get('sync_status') == 'completed':
            update_fields['sync_date'] = datetime.now()

        update_fields['updated_at'] = datetime.now()

        result = mongo_client.files_collection.update_one(
            {"file_id": file_id},
            {"$set": update_fields}
        )

        if result.matched_count > 0:
            return create_json_response({"message": "同步状态更新成功"})
        else:
            return create_json_response({"error": "文件不存在"}, 404)

    except Exception as e:
        logger.error(f"更新同步状态失败: {e}")
        return create_json_response({"error": "服务器内部错误"}, 500)


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


# ============ 字段管理API ============
@app.route('/api/fields/structure', methods=['GET'])
def get_field_structure():
    """获取当前字段结构定义"""
    try:
        return create_json_response(CUSTOM_FIELD_STRUCTURE)
    except Exception as e:
        logger.error(f"API错误: {e}")
        return create_json_response({"error": "服务器内部错误"}, 500)

@app.route('/api/fields/structure', methods=['POST'])
def update_field_structure():
    """更新字段结构定义"""
    try:
        data = request.get_json()
        if not data:
            return create_json_response({"error": "请求数据为空"}, 400)
        
        # 这里可以添加字段验证逻辑
        # 暂时直接返回成功，实际应用中应该保存到配置文件或数据库
        logger.info("字段结构更新请求已接收")
        return create_json_response({"message": "字段结构更新成功"})
    except Exception as e:
        logger.error(f"API错误: {e}")
        return create_json_response({"error": "服务器内部错误"}, 500)

@app.route('/api/fields/groups', methods=['GET'])
def get_field_groups():
    """获取字段分组显示配置"""
    try:
        return create_json_response(FIELD_GROUPS_DISPLAY)
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


@app.route('/api/files/<file_id>', methods=['DELETE'])
def delete_file_api(file_id):
    """删除文件"""
    try:
        success = mongo_client.delete_file(file_id)
        if success:
            return create_json_response({"message": "文件删除成功"})
        else:
            return create_json_response({"error": "文件不存在或删除失败"}, 404)
    except Exception as e:
        logger.error(f"删除文件失败: {e}")
        return create_json_response({"error": "服务器内部错误"}, 500)


@app.route('/api/files/<file_id>/info', methods=['GET'])
def get_file_info(file_id):
    """获取文件详细信息"""
    try:
        file_doc = mongo_client.get_file_by_id(file_id)
        if not file_doc:
            return create_json_response({"error": "文件不存在"}, 404)

        # 返回文件信息，包括原始文件名
        file_info = {
            "file_id": file_doc['file_id'],
            "original_filename": file_doc.get('original_filename', ''),
            "filename": file_doc.get('filename', ''),
            "file_path": file_doc.get('file_path', ''),
            "category": file_doc.get('category', ''),
            "size": file_doc.get('size', 0),
            "mimetype": file_doc.get('mimetype', ''),
            "upload_date": file_doc.get('upload_date'),
            "sync_status": file_doc.get('sync_status', 'pending'),
            "parse_status": file_doc.get('parse_status', 'pending')
        }

        # 处理datetime序列化
        file_info = mongo_client.serialize_datetime(file_info)

        return create_json_response(file_info)

    except Exception as e:
        logger.error(f"获取文件信息错误: {e}")
        return create_json_response({"error": "获取文件信息失败"}, 500)


@app.route('/api/files/<file_id>/server-path', methods=['GET'])
def get_file_server_path(file_id):
    """获取文件在服务器上的路径信息"""
    try:
        file_doc = mongo_client.get_file_by_id(file_id)
        if not file_doc:
            return create_json_response({"error": "文件不存在"}, 404)

        # 获取文件的实际路径
        file_path = file_doc.get('file_path', '')
        
        # 返回文件路径信息
        path_info = {
            "file_id": file_doc['file_id'],
            "original_filename": file_doc.get('original_filename', ''),
            "server_path": file_path,  # 直接使用file_path字段
            "category": file_doc.get('category', ''),
            "size": file_doc.get('size', 0),
            "mimetype": file_doc.get('mimetype', ''),
            "exists": os.path.exists(file_path) if file_path else False
        }

        # 处理datetime序列化
        path_info = mongo_client.serialize_datetime(path_info)

        logger.info(f"获取文件路径信息: {file_id} -> {file_path}")
        return create_json_response(path_info)

    except Exception as e:
        logger.error(f"获取文件服务器路径错误: {e}")
        return create_json_response({"error": "获取文件路径失败"}, 500)


@app.route('/api/files/<file_id>/sync-to-rag', methods=['POST'])
def sync_file_to_rag(file_id):
    """将本地文件直接同步到RAGFlow（后端直传）"""
    try:
        # 1. 查找文件路径
        file_doc = mongo_client.get_file_by_id(file_id)
        if not file_doc:
            return create_json_response({'error': '文件不存在'}, 404)
        file_path = file_doc.get('file_path')
        filename = file_doc.get('original_filename', file_doc.get('filename'))
        if not file_path or not os.path.exists(file_path):
            return create_json_response({'error': '文件路径无效或文件不存在'}, 404)

        # 2. 获取RAG参数
        data = request.get_json(force=True)
        rag_api_url = data.get('rag_api_url')
        rag_api_key = data.get('rag_api_key')
        dataset_id = data.get('dataset_id')
        if not all([rag_api_url, rag_api_key, dataset_id]):
            return create_json_response({'error': '缺少RAG参数'}, 400)

        # 3. 上传到RAG
        url = f"{rag_api_url}/datasets/{dataset_id}/documents"
        headers = {"Authorization": f"Bearer {rag_api_key}"}
        with open(file_path, "rb") as f:
            files = {"file": (filename, f)}
            response = requests.post(url, headers=headers, files=files)
        try:
            result = response.json()
        except Exception:
            result = {'error': 'RAG响应不是JSON', 'text': response.text}
        return create_json_response(result, response.status_code)
    except Exception as e:
        logger.error(f"RAG同步失败: {e}")
        return create_json_response({'error': 'RAG同步失败', 'detail': str(e)}, 500)


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