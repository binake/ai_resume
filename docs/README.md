AI简历管理系统项目结构
目录结构
ai_resume_system/
├── backend/
│   ├── v23.py                 # 主API服务器（推荐使用）
│   ├── config.py              # 配置文件版本
│   ├── requirements.txt       # Python依赖
│   └── models/
│       └── resume_model.py    # 数据模型定义
├── frontend/
│   ├── index.html             # 原始管理页面
│   ├── dashboard.html         # 新版仪表板系统
│   ├── assets/
│   │   ├── css/
│   │   │   └── styles.css
│   │   ├── js/
│   │   │   └── main.js
│   │   └── images/
├── data/
│   └── mongodb_backup/        # 数据库备份
├── docs/
│   ├── API.md                 # API文档
│   └── README.md              # 项目文档
└── scripts/
    ├── start.bat              # Windows启动脚本
    ├── start.sh               # Linux/Mac启动脚本
    └── setup.py               # 环境设置脚本
启动指南
1. 环境准备
安装Python依赖
bashcd backend
pip install -r requirements.txt
requirements.txt 内容:
Flask==2.3.3
Flask-CORS==4.0.0
pymongo==4.5.0
启动MongoDB
bash# Windows
mongod --dbpath "C:\data\db"

# Linux/Mac
mongod --dbpath /data/db
2. 启动后端服务
bashcd backend
python v23.py
服务将在以下端口启动（自动寻找可用端口）：

默认: http://localhost:5000
备选: http://localhost:5001, 8000, 8080, 3001, 4000

3. 启动前端
方式1：直接打开HTML文件
bash# 在浏览器中打开
firefox frontend/dashboard.html
# 或
chrome frontend/dashboard.html
方式2：使用HTTP服务器（推荐）
bash# 使用Python内置服务器
cd frontend
python -m http.server 3000

# 或使用Node.js
npx http-server -p 3000
然后访问：http://localhost:3000
4. 系统功能
后端API端点

GET /api/resume/all - 获取所有简历数据
GET /api/resume/latest - 获取最新简历
GET /api/resume/<id> - 获取指定简历
POST /api/resume - 保存简历数据
GET /api/health - 健康检查
GET /api/test/encoding - 编码测试

前端功能

📊 仪表板: 数据统计和概览
📋 简历管理: 查看、编辑、删除简历
📁 文件上传: 拖放上传简历文件
📈 数据分析: 统计分析和报表
⚙️ 系统设置: 配置和连接状态

部署建议
开发环境
bash# 1. 启动MongoDB
mongod

# 2. 启动Flask后端
cd backend && python v23.py

# 3. 启动前端服务
cd frontend && python -m http.server 3000
生产环境
bash# 使用Gunicorn部署Flask
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 v23:app

# 使用Nginx提供静态文件服务
# nginx.conf 配置示例在下面
Nginx配置示例
nginxserver {
    listen 80;
    server_name localhost;
    
    # 前端静态文件
    location / {
        root /path/to/frontend;
        index dashboard.html;
        try_files $uri $uri/ =404;
    }
    
    # API代理
    location /api/ {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
快速启动脚本
Windows (start.bat)
batch@echo off
echo Starting AI Resume Management System...

echo Starting MongoDB...
start "MongoDB" mongod --dbpath "C:\data\db"

echo Starting Backend API...
cd backend
start "Backend" python v23.py

echo Starting Frontend...
cd ../frontend
start "Frontend" python -m http.server 3000

echo System started successfully!
echo Backend: http://localhost:5000
echo Frontend: http://localhost:3000
pause
Linux/Mac (start.sh)
bash#!/bin/bash
echo "Starting AI Resume Management System..."

echo "Starting MongoDB..."
mongod --fork --dbpath /data/db --logpath /var/log/mongodb.log

echo "Starting Backend API..."
cd backend
python v23.py &

echo "Starting Frontend..."
cd ../frontend
python -m http.server 3000 &

echo "System started successfully!"
echo "Backend: http://localhost:5000"
echo "Frontend: http://localhost:3000"
功能扩展建议
1. 文件上传功能

实现PDF/DOC解析
集成OCR文字识别
批量上传处理

2. 数据分析

技能分布统计
学历层次分析
地区分布图表

3. 权限管理

用户登录系统
角色权限控制
操作日志记录

4. 数据库优化

添加索引
数据分页
缓存机制

故障排除
常见问题

端口被占用: 脚本会自动寻找可用端口
MongoDB连接失败: 检查MongoDB服务是否启动
中文乱码: 使用v23.py，包含编码处理
CORS错误: 确保Flask-CORS已安装

调试模式
bash# 启用Flask调试模式
export FLASK_ENV=development
python v23.py
日志查看
bash# 查看MongoDB日志
tail -f /var/log/mongodb.log

# 查看Flask日志
# 日志会输出到控制台
后续开发计划
短期目标

 完善文件上传功能
 添加数据验证
 实现简历编辑功能
 优化移动端体验

长期目标

 机器学习简历匹配
 自动化招聘建议
 第三方系统集成
 多语言支持

技术栈

后端: Flask + MongoDB + Python
前端: HTML5 + CSS3 + JavaScript
数据库: MongoDB
部署: Nginx + Gunicorn
工具: Git, Docker (可选)

许可证
MIT License - 详见LICENSE文件