#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
简化版慢性病报告生成系统启动脚本
"""

import webbrowser
import time
import threading
import os
from pathlib import Path
import subprocess
import sys

def start_server():
    """启动Flask服务器"""
    try:
        # 启动simple_server.py
        subprocess.run([sys.executable, 'simple_server.py'], check=True)
    except KeyboardInterrupt:
        print("\n服务已停止")
    except Exception as e:
        print(f"服务启动失败: {e}")

def main():
    print("=" * 50)
    print("    慢性病报告生成系统 - 简化版")
    print("=" * 50)
    print()
    
    # 检查文件是否存在
    current_dir = Path(__file__).parent
    server_file = current_dir / 'simple_server.py'
    frontend_file = current_dir / 'frontend' / 'simple.html'
    
    if not server_file.exists():
        print("❌ 找不到服务器文件: simple_server.py")
        return
        
    if not frontend_file.exists():
        print("❌ 找不到前端文件: frontend/simple.html")
        return
    
    print("✅ 文件检查通过")
    print()
    
    # 启动说明
    print("📋 使用说明:")
    print("1. 系统将启动本地服务器")
    print("2. 自动打开浏览器访问前端界面")
    print("3. 输入患者ID (P001, P002, P003) 测试功能")
    print("4. 按 Ctrl+C 停止服务")
    print()
    
    # 启动服务器
    print("🚀 正在启动服务器...")
    server_thread = threading.Thread(target=start_server)
    server_thread.daemon = True
    server_thread.start()
    
    # 等待服务器启动
    time.sleep(3)
    
    # 打开浏览器
    frontend_url = f"file:///{frontend_file.absolute()}"
    print(f"🌐 打开浏览器: {frontend_url}")
    
    try:
        webbrowser.open(frontend_url)
    except Exception as e:
        print(f"无法自动打开浏览器: {e}")
        print(f"请手动打开: {frontend_url}")
    
    print()
    print("💡 提示:")
    print("- 前端地址: " + frontend_url)
    print("- API地址: http://localhost:5000")
    print("- 可用患者ID: P001, P002, P003")
    print()
    print("⏳ 服务运行中，按 Ctrl+C 停止...")
    
    try:
        # 保持主进程运行
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n👋 感谢使用！")

if __name__ == '__main__':
    main()