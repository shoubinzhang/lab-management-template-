import requests
import json
import time

# 基础URL
BASE_URL = "http://localhost:8000"

# 测试账号信息
TEST_USER = {
    "username": "test_user",
    "password": "password123"
}

# 测试数据
TEST_CONSUMABLE_REQUEST = {
    "quantity": 2,
    "purpose": "项目开发测试",
    "notes": "测试申请备注"
}

# 超时设置
TIMEOUT = 10  # 秒

class ConsumableRequestTester:
    def __init__(self):
        self.token = None
        self.session = requests.Session()
    
    def register_test_user(self):
        """注册测试用户"""
        print("=== 尝试注册测试用户 ===")
        try:
            # 准备注册数据
            register_data = {
                "username": TEST_USER["username"],
                "email": f"{TEST_USER['username']}@example.com",
                "password": TEST_USER["password"],
                "role": "user"
            }
            
            response = self.session.post(
                f"{BASE_URL}/api/auth/register",
                json=register_data,
                timeout=TIMEOUT
            )
            
            if response.status_code == 200:
                print(f"✅ 测试用户注册成功")
                return True
            elif response.status_code == 400 and "已存在" in response.text:
                print(f"✅ 测试用户已存在")
                return True
            else:
                print(f"❌ 用户注册失败: 状态码 {response.status_code}")
                print(f"响应内容: {response.text}")
                return False
        except Exception as e:
            print(f"❌ 用户注册请求异常: {str(e)}")
            return False
    
    def login(self):
        """登录获取令牌"""
        print("=== 测试登录功能 ===")
        try:
            response = self.session.post(
                f"{BASE_URL}/api/auth/login",
                json=TEST_USER,
                timeout=TIMEOUT
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                print(f"✅ 登录成功，获取到令牌: {self.token[:20]}...")
                return True
            else:
                print(f"❌ 登录失败: 状态码 {response.status_code}")
                print(f"响应内容: {response.text}")
                return False
        except Exception as e:
            print(f"❌ 登录请求异常: {str(e)}")
            return False
    
    def get_consumables(self):
        """获取耗材列表"""
        print("\n=== 测试获取耗材列表 ===")
        if not self.token:
            print("❌ 未登录，无法获取耗材列表")
            return None
        
        headers = {"Authorization": f"Bearer {self.token}"}
        try:
            response = self.session.get(
                f"{BASE_URL}/cached_consumables",
                headers=headers,
                timeout=TIMEOUT
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 获取耗材列表成功，共 {len(data)} 条数据")
                if data:
                    print(f"首个耗材信息: {data[0]['name']} (库存: {data[0]['stock']})")
                return data
            else:
                print(f"❌ 获取耗材列表失败: 状态码 {response.status_code}")
                print(f"响应内容: {response.text}")
                return None
        except Exception as e:
            print(f"❌ 获取耗材列表请求异常: {str(e)}")
            return None
    
    def submit_consumable_request(self, consumable_id):
        """提交耗材申请"""
        print(f"\n=== 测试提交耗材申请 (耗材ID: {consumable_id}) ===")
        if not self.token:
            print("❌ 未登录，无法提交申请")
            return False
        
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        # 准备申请数据
        request_data = TEST_CONSUMABLE_REQUEST.copy()
        request_data["consumable_id"] = consumable_id
        
        try:
            response = self.session.post(
                f"{BASE_URL}/consumables/request",
                headers=headers,
                data=json.dumps(request_data),
                timeout=TIMEOUT
            )
            
            if response.status_code == 201:
                data = response.json()
                print(f"✅ 耗材申请提交成功")
                print(f"申请ID: {data.get('id')}")
                print(f"申请状态: {data.get('status')}")
                return True
            else:
                print(f"❌ 耗材申请提交失败: 状态码 {response.status_code}")
                print(f"响应内容: {response.text}")
                return False
        except Exception as e:
            print(f"❌ 耗材申请请求异常: {str(e)}")
            return False
    
    def get_my_requests(self):
        """获取我的申请列表"""
        print("\n=== 测试获取我的申请列表 ===")
        if not self.token:
            print("❌ 未登录，无法获取申请列表")
            return None
        
        headers = {"Authorization": f"Bearer {self.token}"}
        try:
            response = self.session.get(
                f"{BASE_URL}/approvals/my-requests",
                headers=headers,
                timeout=TIMEOUT
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 获取我的申请列表成功，共 {len(data)} 条申请")
                if data:
                    print(f"最新申请: {data[0]['purpose']} (状态: {data[0]['status']})")
                return data
            else:
                print(f"❌ 获取我的申请列表失败: 状态码 {response.status_code}")
                print(f"响应内容: {response.text}")
                return None
        except Exception as e:
            print(f"❌ 获取我的申请列表请求异常: {str(e)}")
            return None
    
    def run_full_test(self):
        """运行完整测试流程"""
        print("🚀 开始测试耗材申请功能")
        print("="*50)
        
        # 1. 尝试注册测试用户
        if not self.register_test_user():
            print("❌ 用户注册失败，测试终止")
            return False
        
        # 2. 登录
        if not self.login():
            print("❌ 登录失败，测试终止")
            return False
        
        # 2. 获取耗材列表
        consumables = self.get_consumables()
        if not consumables or len(consumables) == 0:
            print("❌ 没有找到耗材数据，测试终止")
            return False
        
        # 3. 选择第一个可用的耗材提交申请
        valid_consumable = None
        for consumable in consumables:
            if consumable.get("stock", 0) > 0:
                valid_consumable = consumable
                break
        
        if not valid_consumable:
            print("❌ 没有找到有库存的耗材，测试终止")
            return False
        
        # 4. 提交申请
        if not self.submit_consumable_request(valid_consumable["id"]):
            print("❌ 耗材申请提交失败，测试终止")
            return False
        
        # 5. 查询我的申请列表
        self.get_my_requests()
        
        print("="*50)
        print("✅ 耗材申请功能测试完成")
        return True

if __name__ == "__main__":
    tester = ConsumableRequestTester()
    tester.run_full_test()