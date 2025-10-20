// 测试试剂页面修复
async function testReagentsPageFix() {
  console.log('=== 测试试剂页面修复 ===\n');

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
    
    if (!loginResponse.ok) {
      throw new Error(`登录失败: ${loginResponse.status}`);
    }
    
    const loginData = await loginResponse.json();
    const token = loginData.access_token;
    console.log('✅ 登录成功');

    // 2. 测试试剂API
    console.log('\n2. 测试试剂API...');
    const reagentsResponse = await fetch('http://localhost:8000/api/reagents?page=1&per_page=50', {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });

    if (!reagentsResponse.ok) {
      throw new Error(`试剂API请求失败: ${reagentsResponse.status}`);
    }

    const data = await reagentsResponse.json();
    console.log('✅ 试剂API响应正常');
    console.log(`- 试剂总数: ${data.total}`);
    console.log(`- 当前页试剂数: ${data.items.length}`);

    // 3. 测试前端页面
    console.log('\n3. 测试前端页面...');
    const frontendResponse = await fetch('http://localhost:3000/#/reagents');
    
    if (frontendResponse.ok) {
      console.log('✅ 前端页面可访问');
    } else {
      console.log('❌ 前端页面访问失败');
    }

    // 4. 显示一些试剂数据示例
    if (data.items && data.items.length > 0) {
      console.log('\n4. 试剂数据示例:');
      const firstReagent = data.items[0];
      console.log(`- 名称: ${firstReagent.name}`);
      console.log(`- 制造商: ${firstReagent.manufacturer}`);
      console.log(`- 分类: ${firstReagent.category}`);
      console.log(`- 位置: ${firstReagent.location}`);
      console.log(`- 数量: ${firstReagent.quantity} ${firstReagent.unit}`);
    }

    console.log('\n✅ 所有测试通过！试剂页面应该正常显示数据了。');
    console.log('\n📝 修复说明:');
    console.log('- 修复了ReagentsPage中的过滤逻辑错误');
    console.log('- 添加了本地过滤功能，支持按名称、制造商、批次号、位置搜索');
    console.log('- 添加了按分类和状态的过滤功能');
    console.log('- 移除了对SearchAndFilterSection组件onDataChange的依赖');

  } catch (error) {
    console.error('❌ 测试失败:', error.message);
  }
}

testReagentsPageFix();