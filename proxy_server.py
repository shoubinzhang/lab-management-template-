#!/usr/bin/env python3
"""
简单的CORS代理服务器
用于解决前端跨域访问问题
"""

from http.server import HTTPServer, SimpleHTTPRequestHandler
import urllib.request
import urllib.parse
import json
import sys

class CORSProxyHandler(SimpleHTTPRequestHandler):
    def do_OPTIONS(self):
        """处理预检请求"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.send_header('Access-Control-Max-Age', '86400')
        self.end_headers()
    
    def do_GET(self):
        """处理GET请求"""
        if self.path.startswith('/api/'):
            self.proxy_request('GET')
        else:
            super().do_GET()
    
    def do_POST(self):
        """处理POST请求"""
        if self.path.startswith('/api/'):
            self.proxy_request('POST')
        else:
            super().do_POST()
    
    def proxy_request(self, method):
        """代理请求到后端API"""
        try:
            # 构建目标URL
            target_url = f'http://localhost:8000{self.path}'
            print(f"代理请求: {method} {target_url}")
            
            # 获取请求头
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = None
            
            if content_length > 0:
                post_data = self.rfile.read(content_length)
                print(f"请求数据: {post_data.decode('utf-8')}")
            
            # 创建请求
            req = urllib.request.Request(target_url, data=post_data, method=method)
            
            # 复制必要的头
            for header, value in self.headers.items():
                if header.lower() in ['content-type', 'authorization']:
                    req.add_header(header, value)
                    print(f"添加头: {header}: {value}")
            
            # 发送请求
            with urllib.request.urlopen(req) as response:
                response_data = response.read()
                response_code = response.getcode()
                
                print(f"响应状态: {response_code}")
                print(f"响应数据: {response_data.decode('utf-8')[:200]}...")
                
                # 发送响应
                self.send_response(response_code)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Credentials', 'true')
                
                # 复制响应头
                for header, value in response.headers.items():
                    if header.lower() not in ['content-encoding', 'transfer-encoding']:
                        self.send_header(header, value)
                
                self.end_headers()
                self.wfile.write(response_data)
                
        except Exception as e:
            print(f"代理错误: {str(e)}")
            self.send_error(500, f'Proxy error: {str(e)}')

def run_server(port=3001):
    """运行代理服务器"""
    server_address = ('', port)
    httpd = HTTPServer(server_address, CORSProxyHandler)
    print(f"CORS代理服务器运行在 http://localhost:{port}")
    print(f"API代理地址: http://localhost:{port}/api/")
    print("按 Ctrl+C 停止服务器")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n服务器已停止")
        httpd.shutdown()

if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 3001
    run_server(port)