#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI简历管理系统 - 一键启动脚本
运行此脚本将自动启动整个系统
"""

import os
import sys
import time
import subprocess
import webbrowser
from pathlib import Path


def print_banner():
    """打印启动横幅"""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                   AI简历管理系统                              ║
    ║                  一键启动脚本 v1.0                           ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)


def check_dependencies():
    """检查依赖是否安装"""
    print("🔍 检查系统依赖...")

    # 检查Python版本
    if sys.version_info < (3, 7):
        print("❌ Python版本过低，请使用Python 3.7+")
        return False

    # 检查必要的包
    required_packages = ['flask', 'pymongo', 'flask_cors']
    missing_packages = []

    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} 已安装")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package} 未安装")

    if missing_packages:
        print(f"\n📦 正在安装缺失的包: {', '.join(missing_packages)}")
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install'] + missing_packages)
            print("✅ 依赖安装完成")
        except subprocess.CalledProcessError:
            print("❌ 依赖安装失败，请手动安装")
            return False

    return True


def check_mongodb():
    """检查MongoDB是否运行"""
    print("🔍 检查MongoDB连接...")
    try:
        from pymongo import MongoClient
        client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=3000)
        client.server_info()
        print("✅ MongoDB连接正常")
        return True
    except Exception as e:
        print(f"❌ MongoDB连接失败: {e}")
        print("💡 请确保MongoDB服务已启动")
        return False


def find_available_port(start_port=5000):
    """寻找可用端口"""
    import socket
    for port in range(start_port, start_port + 20):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                return port
        except OSError:
            continue
    return None


def start_backend():
    """启动后端服务"""
    print("🚀 启动后端API服务...")

    # 检查v23.py是否存在
    backend_file = Path('v23.py')
    if not backend_file.exists():
        backend_file = Path('backend/v23.py')
        if not backend_file.exists():
            print("❌ 未找到v23.py文件")
            return None

    # 启动后端服务
    try:
        process = subprocess.Popen([
            sys.executable, str(backend_file)
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        # 等待服务启动
        time.sleep(3)

        if process.poll() is None:
            print("✅ 后端服务启动成功")
            return process
        else:
            stdout, stderr = process.communicate()
            print(f"❌ 后端服务启动失败: {stderr}")
            return None

    except Exception as e:
        print(f"❌ 后端服务启动失败: {e}")
        return None


def start_frontend():
    """启动前端服务"""
    print("🌐 启动前端服务...")

    # 检查前端文件
    frontend_files = ['dashboard.html', 'index.html', 'frontend/dashboard.html']
    frontend_file = None

    for file in frontend_files:
        if Path(file).exists():
            frontend_file = file
            break

    if not frontend_file:
        print("❌ 未找到前端文件")
        return None

    # 启动HTTP服务器
    try:
        frontend_dir = Path(frontend_file).parent
        port = find_available_port(3000)

        if port is None:
            print("❌ 无法找到可用端口")
            return None

        process = subprocess.Popen([
            sys.executable, '-m', 'http.server', str(port)
        ], cwd=frontend_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        time.sleep(2)

        if process.poll() is None:
            print(f"✅ 前端服务启动成功，端口: {port}")
            return process, port
        else:
            print("❌ 前端服务启动失败")
            return None

    except Exception as e:
        print(f"❌ 前端服务启动失败: {e}")
        return None


def open_browser(port):
    """打开浏览器"""
    print("🌍 正在打开浏览器...")
    try:
        webbrowser.open(f'http://localhost:{port}')
        print("✅ 浏览器已打开")
    except Exception as e:
        print(f"❌ 无法自动打开浏览器: {e}")
        print(f"请手动访问: http://localhost:{port}")


def main():
    """主函数"""
    print_banner()

    # 检查依赖
    if not check_dependencies():
        input("按回车键退出...")
        return

    # 检查MongoDB
    if not check_mongodb():
        print("请先启动MongoDB服务")
        input("按回车键退出...")
        return

    # 启动后端
    backend_process = start_backend()
    if not backend_process:
        input("按回车键退出...")
        return

    # 启动前端
    frontend_result = start_frontend()
    if not frontend_result:
        backend_process.terminate()
        input("按回车键退出...")
        return

    frontend_process, frontend_port = frontend_result

    # 打开浏览器
    open_browser(frontend_port)

    # 显示系统信息
    print("\n" + "=" * 60)
    print("🎉 AI简历管理系统启动成功!")
    print(f"📊 前端界面: http://localhost:{frontend_port}")
    print(f"🔧 后端API: http://localhost:5000/api")
    print("=" * 60)
    print("\n💡 提示:")
    print("- 按 Ctrl+C 停止所有服务")
    print("- 系统日志会显示在此窗口")
    print("- 如需帮助，请查看README.md")
    print("-" * 60)

    try:
        # 保持服务运行
        while True:
            time.sleep(1)

            # 检查进程状态
            if backend_process.poll() is not None:
                print("❌ 后端服务已停止")
                break

            if frontend_process.poll() is not None:
                print("❌ 前端服务已停止")
                break

    except KeyboardInterrupt:
        print("\n🛑 正在停止服务...")

        # 停止所有进程
        try:
            backend_process.terminate()
            frontend_process.terminate()

            # 等待进程结束
            backend_process.wait(timeout=5)
            frontend_process.wait(timeout=5)

            print("✅ 所有服务已停止")

        except subprocess.TimeoutExpired:
            print("⚠️ 强制终止进程...")
            backend_process.kill()
            frontend_process.kill()

        except Exception as e:
            print(f"❌ 停止服务时出错: {e}")

    print("👋 谢谢使用AI简历管理系统！")


if __name__ == "__main__":
    main()