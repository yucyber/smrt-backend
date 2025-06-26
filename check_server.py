import json
import requests

def check_server():
    """检查后端服务是否正常运行"""
    try:
        # 尝试连接后端服务
        response = requests.get('http://127.0.0.1:5000/')
        print(f"服务器根URL响应状态码: {response.status_code}")
        print(f"服务器根URL响应内容: {response.text}")
        
        # 尝试进行登录请求
        login_data = {
            'email': 'test@example.com',
            'password': '123456'
        }
        
        print("\n尝试登录请求...")
        print(f"请求数据: {json.dumps(login_data)}")
        
        login_response = requests.post('http://127.0.0.1:5000/auth/login', json=login_data)
        print(f"登录响应状态码: {login_response.status_code}")
        
        try:
            response_json = login_response.json()
            print(f"登录响应内容: {json.dumps(response_json, ensure_ascii=False, indent=2)}")
            
            if response_json.get('code') == 200:
                print("\n✅ 登录成功! 服务器工作正常。")
                return True
            else:
                print(f"\n❌ 登录失败: {response_json.get('message')}")
                return False
        except ValueError:
            print(f"\n❌ 响应不是有效的JSON: {login_response.text}")
            return False
    except requests.exceptions.ConnectionError:
        print("\n❌ 无法连接到服务器! 请确保后端服务正在运行。")
        return False
    except Exception as e:
        print(f"\n❌ 检查服务器时出错: {str(e)}")
        return False

if __name__ == '__main__':
    print("正在检查后端服务器状态...")
    check_server() 