// 测试前端网络请求
async function testFrontendNetwork() {
  console.log('=== 测试前端网络请求 ===\n');

  try {
    // 1. 测试登录
    console.log('1. 测试登录...');
    const loginResponse = await fetch('http://localhost:8000/api/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        username: 'admin',
        password: 'admin123'
      })
    });
    
    console.log('登录状态:', loginResponse.status);
    const loginData = await loginResponse.json();
    const token = loginData.access_token;
    console.log('获取到token:', token ? '是' : '否');

    // 2. 测试试剂API（模拟前端请求）
    console.log('\n2. 测试试剂API...');
    
    // 模拟前端的请求参数
    const params = new URLSearchParams({
      page: '1',
      per_page: '50',
      search: '',
      category: '',
      status: ''
    });

    const reagentsResponse = await fetch(`http://localhost:8000/api/reagents?${params}`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });

    console.log('试剂API状态:', reagentsResponse.status);
    console.log('响应头Content-Type:', reagentsResponse.headers.get('content-type'));
    
    const data = await reagentsResponse.json();
    console.log('\n3. 数据结构分析:');
    console.log('- 响应类型:', typeof data);
    console.log('- 是否有items字段:', 'items' in data);
    console.log('- items类型:', typeof data.items);
    console.log('- items是否为数组:', Array.isArray(data.items));
    console.log('- items长度:', data.items ? data.items.length : 'N/A');
    console.log('- total字段:', data.total);
    console.log('- page字段:', data.page);
    console.log('- per_page字段:', data.per_page);

    if (data.items && data.items.length > 0) {
      console.log('\n4. 第一个试剂数据:');
      const firstReagent = data.items[0];
      console.log('- ID:', firstReagent.id);
      console.log('- 名称:', firstReagent.name);
      console.log('- 制造商:', firstReagent.manufacturer);
      console.log('- 数量:', firstReagent.quantity);
      console.log('- 单位:', firstReagent.unit);
      console.log('- 位置:', firstReagent.location);
      console.log('- 分类:', firstReagent.category);
    } else {
      console.log('\n4. 没有试剂数据或数据为空');
    }

    console.log('\n✅ 网络请求测试完成');

  } catch (error) {
    console.error('\n❌ 网络请求测试失败:');
    console.error('错误信息:', error.message);
    if (error.response) {
      console.error('响应状态:', error.response.status);
      console.error('响应数据:', error.response.data);
    }
  }
}

testFrontendNetwork();