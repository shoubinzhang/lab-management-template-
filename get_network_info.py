#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
网络信息获取脚本
用于获取本机IP地址，帮助配置手机访问
"""

import socket
import subprocess
import sys

def get_local_ip():
    """获取本机IP地址"""
    try:
        # 连接到一个远程地址来获取本机IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return None

def get_all_ips():
    """获取所有网络接口的IP地址"""
    try:
        if sys.platform == "win32":
            result = subprocess.run(['ipconfig'], capture_output=True, text=True, shell=True)
            return result.stdout
        else:
            result = subprocess.run(['ifconfig'], capture_output=True, text=True)
            return result.stdout
    except Exception as e:
        return f"获取网络信息失败: {e}"

def main():
    print("=== 实验室管理系统网络配置诊断 ===")
    print()
    
    # 获取主要IP地址
    local_ip = get_local_ip()
    if local_ip:
        print(f"✅ 检测到主要IP地址: {local_ip}")
        print(f"📱 手机应该使用的API地址: http://{local_ip}:8000")
        print()
        
        # 生成前端配置建议
        print("🔧 前端配置修改建议:")
        print(f"将 frontend/.env 文件中的 REACT_APP_API_URL 修改为:")
        print(f"REACT_APP_API_URL=http://{local_ip}:8000")
        print()
        
        # 生成测试URL
        print("🧪 测试URL:")
        print(f"后端API: http://{local_ip}:8000/docs")
        print(f"前端应用: http://{local_ip}:3000")
        print()
    else:
        print("❌ 无法自动检测IP地址")
    
    print("📋 所有网络接口信息:")
    print("=" * 50)
    network_info = get_all_ips()
    print(network_info)
    
    print("\n💡 使用说明:")
    print("1. 确保电脑和手机连接到同一个WiFi网络")
    print("2. 修改前端 .env 文件中的 API_URL 为上面显示的IP地址")
    print("3. 重启前端开发服务器 (npm start)")
    print("4. 在手机浏览器中访问: http://[IP地址]:3000")
    print("5. 确保Windows防火墙允许端口3000和8000的访问")
    
if __name__ == "__main__":
    main()