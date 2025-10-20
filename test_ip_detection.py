#!/usr/bin/env python3
"""
测试本地IP地址获取功能
"""

import socket
import subprocess
import platform

def get_local_ip_socket():
    """使用socket方法获取本地IP"""
    try:
        # 创建一个UDP socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # 连接到一个远程地址（不会实际发送数据）
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception as e:
        print(f"Socket方法获取IP失败: {e}")
        return None

def get_local_ip_command():
    """使用系统命令获取本地IP"""
    try:
        if platform.system() == "Windows":
            # Windows系统
            result = subprocess.run(['ipconfig'], capture_output=True, text=True, encoding='gbk')
            lines = result.stdout.split('\n')
            for line in lines:
                if 'IPv4' in line and '192.168.' in line:
                    ip = line.split(':')[-1].strip()
                    return ip
        else:
            # Linux/Mac系统
            result = subprocess.run(['hostname', '-I'], capture_output=True, text=True)
            return result.stdout.strip().split()[0]
    except Exception as e:
        print(f"命令行方法获取IP失败: {e}")
        return None

def main():
    print("🔍 测试本地IP地址获取功能")
    print("=" * 50)
    
    # 方法1: Socket方法
    ip1 = get_local_ip_socket()
    print(f"📡 Socket方法获取的IP: {ip1}")
    
    # 方法2: 系统命令方法
    ip2 = get_local_ip_command()
    print(f"💻 命令行方法获取的IP: {ip2}")
    
    # 显示推荐的IP地址
    recommended_ip = ip1 or ip2
    if recommended_ip:
        print(f"\n✅ 推荐使用的IP地址: {recommended_ip}")
        print(f"📱 手机扫码地址应该是: http://{recommended_ip}:3000")
        print(f"🔗 后端API地址应该是: http://{recommended_ip}:8000")
    else:
        print("\n❌ 无法获取本地IP地址")
        print("💡 请检查网络连接或手动配置IP地址")
    
    print("\n" + "=" * 50)
    print("📋 使用说明:")
    print("1. 确保电脑和手机在同一个WiFi网络")
    print("2. 使用上面显示的IP地址生成二维码")
    print("3. 手机扫描二维码即可访问系统")

if __name__ == "__main__":
    main()