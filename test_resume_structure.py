#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project : Python
@File    : test_resume_structure.py
@IDE     : PyCharm
@Author  : Gavin
@Date    : 2025/1/16
@DESC    : 测试ResumeSDK字段结构
"""

import json

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

def test_field_structure():
    """测试字段结构定义"""
    print("=== ResumeSDK字段结构测试 ===\n")
    
    # 1. 测试基本信息字段
    print("1. 基本信息字段:")
    basic_info = CUSTOM_FIELD_STRUCTURE['basic_info']
    for field, config in basic_info.items():
        print(f"  - {field}: {config['label']} ({config['type']})")
    print(f"  总计: {len(basic_info)} 个字段\n")
    
    # 2. 测试教育经历字段
    print("2. 教育经历字段:")
    education = CUSTOM_FIELD_STRUCTURE['education']
    for field, config in education.items():
        print(f"  - {field}: {config['label']} ({config['type']})")
    print(f"  总计: {len(education)} 个字段\n")
    
    # 3. 测试工作经历字段
    print("3. 工作经历字段:")
    work_exp = CUSTOM_FIELD_STRUCTURE['work_experience']
    for field, config in work_exp.items():
        print(f"  - {field}: {config['label']} ({config['type']})")
    print(f"  总计: {len(work_exp)} 个字段\n")
    
    # 4. 测试项目经历字段
    print("4. 项目经历字段:")
    project_exp = CUSTOM_FIELD_STRUCTURE['project_experience']
    for field, config in project_exp.items():
        print(f"  - {field}: {config['label']} ({config['type']})")
    print(f"  总计: {len(project_exp)} 个字段\n")
    
    # 5. 测试技能列表字段
    print("5. 技能列表字段:")
    skills = CUSTOM_FIELD_STRUCTURE['skills']
    for field, config in skills.items():
        print(f"  - {field}: {config['label']} ({config['type']})")
    print(f"  总计: {len(skills)} 个字段\n")
    
    # 6. 测试语言技能字段
    print("6. 语言技能字段:")
    language_skills = CUSTOM_FIELD_STRUCTURE['language_skills']
    for field, config in language_skills.items():
        print(f"  - {field}: {config['label']} ({config['type']})")
    print(f"  总计: {len(language_skills)} 个字段\n")
    
    # 7. 测试证书奖项字段
    print("7. 证书奖项字段:")
    certificates = CUSTOM_FIELD_STRUCTURE['certificates']
    for field, config in certificates.items():
        print(f"  - {field}: {config['label']} ({config['type']})")
    print(f"  总计: {len(certificates)} 个字段\n")
    
    # 8. 测试培训经历字段
    print("8. 培训经历字段:")
    training = CUSTOM_FIELD_STRUCTURE['training']
    for field, config in training.items():
        print(f"  - {field}: {config['label']} ({config['type']})")
    print(f"  总计: {len(training)} 个字段\n")
    
    # 9. 测试社会实践字段
    print("9. 社会实践字段:")
    social_practice = CUSTOM_FIELD_STRUCTURE['social_practice']
    for field, config in social_practice.items():
        print(f"  - {field}: {config['label']} ({config['type']})")
    print(f"  总计: {len(social_practice)} 个字段\n")
    
    # 10. 测试个人评价字段
    print("10. 个人评价字段:")
    self_evaluation = CUSTOM_FIELD_STRUCTURE['self_evaluation']
    for field, config in self_evaluation.items():
        print(f"  - {field}: {config['label']} ({config['type']})")
    print(f"  总计: {len(self_evaluation)} 个字段\n")
    
    # 11. 统计总字段数
    total_fields = sum(len(fields) for fields in CUSTOM_FIELD_STRUCTURE.values())
    print(f"=== 总计 ===\n")
    print(f"分组数量: {len(CUSTOM_FIELD_STRUCTURE)}")
    print(f"字段总数: {total_fields}")
    
    # 12. 显示分组配置
    print(f"\n=== 分组显示配置 ===\n")
    for group_key, config in FIELD_GROUPS_DISPLAY.items():
        print(f"{config['icon']} {config['name']} (order: {config['order']})")
        print(f"  描述: {config['description']}")
        print()

def test_sample_data():
    """测试示例数据映射"""
    print("=== 示例数据映射测试 ===\n")
    
    # 模拟ResumeSDK返回的数据结构
    sample_parser_result = {
        "profile": {
            "name": "张三",
            "gender": "男",
            "age": 28,
            "birthday": "1995-01-01",
            "mobile": "13800138000",
            "email": "zhangsan@example.com",
            "living_address": "北京市朝阳区",
            "hometown_address": "山东省济南市",
            "hukou_address": "山东省济南市",
            "city": "北京",
            "race": "汉族",
            "surname": "张",
            "workExpYear": "5年",
            "github": "https://github.com/zhangsan",
            "zhihu": "https://zhihu.com/people/zhangsan",
            "wechat": "zhangsan123",
            "qq": "123456789",
            "linkedin": "https://linkedin.com/in/zhangsan",
            "blog": "https://blog.zhangsan.com",
            "website": "https://zhangsan.com",
            "avatar": "data:image/jpeg;base64,...",
            "expect_job": "高级软件工程师",
            "expect_salary": "25k-35k",
            "expect_city": "北京",
            "expect_industry": "互联网",
            "resume_name": "张三的简历",
            "resume_update_time": "2024-01-16",
            "resume_text": "完整的简历文本内容..."
        },
        "educationList": [
            {
                "college": "北京大学",
                "major": "计算机科学与技术",
                "education": "本科",
                "degree": "学士",
                "college_type": "985",
                "college_rank": "1",
                "grad_time": "2017-07",
                "education_start_time": "2013-09",
                "education_end_time": "2017-07",
                "gpa": "3.8",
                "course": "数据结构、算法、操作系统、计算机网络",
                "education_desc": "主修计算机相关课程，成绩优秀"
            }
        ],
        "workExpList": [
            {
                "company_name": "阿里巴巴",
                "department_name": "技术部",
                "job_position": "高级软件工程师",
                "work_time": ["2020-03", "2024-01"],
                "work_start_time": "2020-03",
                "work_end_time": "2024-01",
                "work_desc": "负责电商平台后端开发，使用Java、Spring Boot等技术栈",
                "salary": "25k",
                "work_type": "全职",
                "industry": "互联网",
                "company_size": "10000+",
                "company_nature": "民营企业",
                "report_to": "技术总监",
                "subordinates": "5人",
                "achievement": "优化系统性能，提升用户体验，获得年度优秀员工"
            }
        ],
        "projectList": [
            {
                "project_name": "电商平台重构",
                "project_role": "技术负责人",
                "project_time": "2022-01至2023-06",
                "project_start_time": "2022-01",
                "project_end_time": "2023-06",
                "project_desc": "对现有电商平台进行微服务架构重构",
                "project_content": "使用Spring Cloud、Docker、Kubernetes等技术",
                "project_technology": "Java, Spring Cloud, Docker, Kubernetes, MySQL, Redis",
                "project_result": "系统性能提升50%，支持千万级用户访问",
                "project_scale": "大型项目",
                "project_budget": "500万",
                "project_team_size": "20人"
            }
        ],
        "skillList": [
            {
                "skill_name": "Java",
                "skill_level": "精通",
                "skill_desc": "熟练掌握Java核心技术",
                "skill_years": "5年",
                "skill_category": "编程语言"
            },
            {
                "skill_name": "Spring Boot",
                "skill_level": "熟练",
                "skill_desc": "熟练使用Spring Boot框架",
                "skill_years": "4年",
                "skill_category": "框架"
            }
        ],
        "languageList": [
            {
                "language_name": "英语",
                "language_level": "CET-6",
                "language_certificate": "CET-6证书",
                "language_score": "580"
            }
        ],
        "awardList": [
            {
                "award_info": "年度优秀员工",
                "award_time": "2023-12",
                "award_desc": "因工作表现优秀获得公司年度优秀员工称号",
                "award_level": "公司级",
                "award_issuer": "阿里巴巴集团",
                "certificate_type": "荣誉证书"
            }
        ],
        "training": [
            {
                "training_name": "微服务架构培训",
                "training_time": "2022-03",
                "training_desc": "参加公司组织的微服务架构培训",
                "training_institution": "阿里巴巴技术学院",
                "training_certificate": "微服务架构认证",
                "training_duration": "3天"
            }
        ],
        "practiceList": [
            {
                "practice_name": "开源项目贡献",
                "practice_time": "2021-2023",
                "practice_desc": "积极参与开源项目，贡献代码",
                "practice_role": "贡献者",
                "practice_organization": "GitHub开源社区"
            }
        ],
        "aboutme": {
            "aboutme_desc": "热爱技术，善于学习，有良好的团队协作能力",
            "self_introduction": "我是一名有5年工作经验的软件工程师，专注于后端开发",
            "hobby": "编程、阅读、运动",
            "strength": "技术能力强，学习能力强，团队协作好",
            "weakness": "有时过于追求完美",
            "career_goal": "成为技术专家，带领团队完成有挑战性的项目"
        }
    }
    
    # 模拟映射函数
    def map_parser_result_to_custom_structure(parser_result):
        """将第三方API解析结果映射到自定义数据库结构"""
        try:
            custom_data = {}
            
            # 基本信息映射
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
            
            # 教育经历映射
            if 'educationList' in parser_result and isinstance(parser_result['educationList'], list):
                education_list = parser_result['educationList']
                if education_list:
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
                custom_data['educationList'] = education_list
            
            # 工作经历映射
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
            custom_data['work_experience'] = work_experience
            
            # 项目经历映射
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
            
            # 技能列表映射
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
            custom_data['skills'] = skills
            
            # 语言技能映射
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
            
            # 证书奖项映射
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
            
            # 培训经历映射
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
            
            # 社会实践映射
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
            
            # 个人评价映射
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
            
            return custom_data
            
        except Exception as e:
            print(f"数据映射失败: {e}")
            return parser_result
    
    # 执行映射
    custom_data = map_parser_result_to_custom_structure(sample_parser_result)
    
    print("映射结果:")
    print(json.dumps(custom_data, ensure_ascii=False, indent=2))
    
    # 验证关键字段
    print(f"\n=== 字段验证 ===\n")
    print(f"姓名: {custom_data.get('name', 'N/A')}")
    print(f"邮箱: {custom_data.get('email', 'N/A')}")
    print(f"手机: {custom_data.get('mobile', 'N/A')}")
    print(f"工作经历数量: {len(custom_data.get('work_experience', []))}")
    print(f"项目经历数量: {len(custom_data.get('project_experience', []))}")
    print(f"技能数量: {len(custom_data.get('skills', []))}")
    print(f"语言技能数量: {len(custom_data.get('language_skills', []))}")
    print(f"证书数量: {len(custom_data.get('certificates', []))}")
    print(f"培训经历数量: {len(custom_data.get('training', []))}")
    print(f"社会实践数量: {len(custom_data.get('social_practice', []))}")

if __name__ == "__main__":
    test_field_structure()
    print("\n" + "="*50 + "\n")
    test_sample_data() 