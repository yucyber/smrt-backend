import os
from app import create_app
from app.auth.models import Users

# 强制设置生产模式
os.environ['DEVELOPMENT_MODE'] = 'False'

app = create_app()

# 简单的首页路由
@app.route('/')
def index():
    return '妙笔智能编辑器后端服务 - 生产模式'

# 配置信息路由
@app.route('/api/status')
def status():
    # 统计用户数量
    user_count = 0
    try:
        with app.app_context():
            user_count = Users.query.count()
    except Exception as e:
        print(f"获取用户数量失败: {str(e)}")
    
    return {
        'status': 'online',
        'version': '1.0.0',
        'mode': 'production',
        'message': '后端服务正常运行中',
        'users': user_count,
        'available_accounts': [
            {'email': 'admin@smarteditor.com', 'password': 'admin123', 'role': '管理员'},
            {'email': 'template@admin.com', 'password': 'template123', 'role': '模板管理员'},
            {'email': 'test@example.com', 'password': '123456', 'role': '测试用户'},
            {'email': 'user@test.com', 'password': '123456', 'role': '测试用户'},
            {'email': 'example@test.com', 'password': '123456', 'role': '示例用户'}
        ]
    }

# 提供可用账号信息的路由
@app.route('/api/accounts')
def accounts():
    return {
        'message': '可用的测试账号',
        'accounts': [
            {'email': 'admin@smarteditor.com', 'password': 'admin123', 'role': '管理员'},
            {'email': 'template@admin.com', 'password': 'template123', 'role': '模板管理员'},
            {'email': 'test@example.com', 'password': '123456', 'role': '测试用户'},
            {'email': 'user@test.com', 'password': '123456', 'role': '测试用户'},
            {'email': 'example@test.com', 'password': '123456', 'role': '示例用户'}
        ]
    }

if __name__ == '__main__':
    with app.app_context():
        user_count = Users.query.count()
        print(f"系统中共有 {user_count} 个用户账号")
        print("\n可用的测试账号:")
        print("1. 管理员: admin@smarteditor.com / admin123")
        print("2. 模板管理员: template@admin.com / template123")
        print("3. 测试用户: test@example.com / 123456")
        print("4. 测试用户: user@test.com / 123456")
        print("5. 示例用户: example@test.com / 123456")
        print("\n启动服务器...")
    
    app.run(host='0.0.0.0', port=5000, debug=False) 