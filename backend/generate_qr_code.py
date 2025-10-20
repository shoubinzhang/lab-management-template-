import qrcode
import os
import base64
import io
from datetime import datetime

# 生成QR码方便手机访问
def generate_mobile_access_qr_code():
    # 获取本机IP地址（用于局域网访问）
    def get_local_ip():
        import socket
        try:
            # 创建一个socket连接来获取本机IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # 连接到一个公共DNS服务器（不会实际发送数据）
            s.connect(('8.8.8.8', 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except Exception as e:
            print(f"无法获取本机IP地址: {str(e)}")
            return 'localhost'
    
    # 获取本机IP
    local_ip = get_local_ip()
    
    # 构建移动端登录页面的URL
    local_url = f"http://{local_ip}:8000/mobile_login_final.html"
    localhost_url = "http://localhost:8000/mobile_login_final.html"
    
    print("=" * 80)
    print("移动端访问指南")
    print("=" * 80)
    print("\n以下是您可以通过手机访问应用的方式：\n")
    
    # 生成局域网访问URL的QR码
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(local_url)
    qr.make(fit=True)
    
    # 生成QR码图片
    img = qr.make_image(fill_color="black", back_color="white")
    
    # 保存QR码图片
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    qr_code_path = f"mobile_qr_code_{timestamp}.png"
    img.save(qr_code_path)
    
    # 生成base64编码的QR码（用于在网页中显示）
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    
    # 创建一个简单的HTML页面来显示QR码
    html_content = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>实验室管理系统 - 移动端访问</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
                text-align: center;
            }}
            .container {{
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 20px;
                margin-top: 20px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .qr-code {{
                margin: 20px 0;
                padding: 10px;
                background-color: white;
                display: inline-block;
            }}
            .url-display {{
                word-break: break-all;
                padding: 10px;
                background-color: #f5f5f5;
                border-radius: 4px;
                margin: 10px 0;
            }}
            .instructions {{
                text-align: left;
                margin-top: 20px;
            }}
            .instructions li {{
                margin: 8px 0;
            }}
        </style>
    </head>
    <body>
        <h1>实验室管理系统 - 移动端访问</h1>
        <div class="container">
            <h2>扫描二维码访问</h2>
            <div class="qr-code">
                <img src="data:image/png;base64,{img_str}" alt="移动端访问QR码">
            </div>
            
            <h3>或直接输入以下网址</h3>
            <div class="url-display">
                <strong>局域网地址：</strong><br>{local_url}
            </div>
            <div class="url-display">
                <strong>本机地址：</strong><br>{localhost_url}
            </div>
            
            <div class="instructions">
                <h3>使用说明：</h3>
                <ol>
                    <li>确保您的手机和电脑连接在同一个局域网内</li>
                    <li>打开手机上的浏览器或扫码应用</li>
                    <li>扫描上方的二维码，或手动输入网址</li>
                    <li>系统将自动跳转到移动端登录页面</li>
                    <li>登录后即可使用移动端功能</li>
                </ol>
            </div>
            
            <div class="instructions">
                <h3>常用移动端页面：</h3>
                <ul>
                    <li>登录页面：<code>http://{local_ip}:8000/mobile_login_final.html</code></li>
                    <li>仪表盘：<code>http://{local_ip}:8000/mobile_dashboard.html</code></li>
                    <li>设备管理：<code>http://{local_ip}:8000/mobile_devices.html</code></li>
                    <li>试剂管理：<code>http://{local_ip}:8000/mobile_reagents.html</code></li>
                    <li>扫码页面：<code>http://{local_ip}:8000/mobile_scan.html</code></li>
                </ul>
            </div>
        </div>
    </body>
    </html>
    """
    
    # 保存HTML页面
    html_path = f"mobile_access_guide_{timestamp}.html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    # 输出信息
    print(f"1. 二维码已生成并保存至: {qr_code_path}")
    print(f"2. 移动端访问指南HTML页面已生成至: {html_path}")
    print("\n您可以：")
    print(f"   - 直接打开 {html_path} 文件查看详细的访问指南和QR码")
    print(f"   - 使用手机扫描QR码快速访问应用")
    print(f"   - 手动在手机浏览器中输入: {local_url}")
    print("\n注意：确保您的手机和电脑连接在同一个局域网内才能正常访问！")
    print("=" * 80)
    
    return qr_code_path, html_path

if __name__ == "__main__":
    generate_mobile_access_qr_code()