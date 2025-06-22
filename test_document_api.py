import json
import requests
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# 测试配置
BASE_URL = 'http://127.0.0.1:5000'
TEST_USER = {
    'email': 'test@example.com',
    'password': '123456'
}

def test_document_api():
    """测试文档API的各项功能"""
    # 1. 登录获取JWT令牌
    token = login_and_get_token()
    if not token:
        logging.error("登录失败，无法继续测试")
        return False
    
    # 2. 创建新文档
    document_id = create_document(token)
    if not document_id:
        logging.error("创建文档失败，无法继续测试")
        return False
    
    # 3. 获取文档详情
    if not get_document(token, document_id):
        logging.error("获取文档失败")
        return False
    
    # 4. 获取用户所有文档
    if not get_user_documents(token):
        logging.error("获取用户文档列表失败")
        return False
    
    # 5. 更新文档
    if not update_document(token, document_id):
        logging.error("更新文档失败")
        return False
    
    # 6. 将文档加入收藏
    if not favorite_document(token, document_id):
        logging.error("收藏文档失败")
        return False
    
    # 7. 获取收藏文档列表
    if not get_favorite_documents(token):
        logging.error("获取收藏文档列表失败")
        return False
    
    # 8. 将文档移至回收站
    if not delete_document_logic(token, document_id):
        logging.error("移动文档到回收站失败")
        return False
    
    # 9. 获取回收站文档列表
    if not get_deleted_documents(token):
        logging.error("获取回收站文档列表失败")
        return False
    
    # 10. 测试完成
    logging.info("文档API测试完成，所有功能正常！")
    return True

def login_and_get_token():
    """登录并获取JWT令牌"""
    try:
        logging.info("尝试登录获取令牌...")
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json=TEST_USER
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == 200:
                token = data.get('data', {}).get('access_token')
                logging.info(f"登录成功，获取到令牌: {token[:20]}...")
                return token
            else:
                logging.error(f"登录失败: {data.get('message')}")
                return None
        else:
            logging.error(f"登录请求失败: {response.status_code}")
            return None
    except Exception as e:
        logging.error(f"登录过程中发生错误: {str(e)}")
        return None

def create_document(token):
    """创建新文档"""
    try:
        logging.info("尝试创建新文档...")
        headers = {'Authorization': f'Bearer {token}'}
        document_data = {
            'title': '测试文档',
            'content': '<h1>测试文档</h1><p>这是一个由API测试脚本创建的测试文档。</p>'
        }
        
        response = requests.post(
            f"{BASE_URL}/document",
            json=document_data,
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == '200':
                document_id = data.get('id')
                logging.info(f"文档创建成功，ID: {document_id}")
                return document_id
            else:
                logging.error(f"创建文档失败: {data.get('message')}")
                return None
        else:
            logging.error(f"创建文档请求失败: {response.status_code}")
            return None
    except Exception as e:
        logging.error(f"创建文档过程中发生错误: {str(e)}")
        return None

def get_document(token, document_id):
    """获取文档详情"""
    try:
        logging.info(f"尝试获取文档详情，ID: {document_id}...")
        headers = {'Authorization': f'Bearer {token}'}
        
        response = requests.get(
            f"{BASE_URL}/document/{document_id}",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == '200':
                document = data.get('document')
                logging.info(f"获取文档成功: {document.get('title')}")
                return True
            else:
                logging.error(f"获取文档失败: {data.get('message')}")
                return False
        else:
            logging.error(f"获取文档请求失败: {response.status_code}")
            return False
    except Exception as e:
        logging.error(f"获取文档过程中发生错误: {str(e)}")
        return False

def get_user_documents(token):
    """获取用户所有文档"""
    try:
        logging.info("尝试获取用户所有文档...")
        headers = {'Authorization': f'Bearer {token}'}
        
        response = requests.get(
            f"{BASE_URL}/document/user",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == '200':
                documents = data.get('documents', [])
                logging.info(f"获取用户文档成功，共 {len(documents)} 个文档")
                return True
            else:
                logging.warning(f"获取用户文档返回: {data.get('message')}")
                return True  # 用户可能没有文档，也是合法的情况
        else:
            logging.error(f"获取用户文档请求失败: {response.status_code}")
            return False
    except Exception as e:
        logging.error(f"获取用户文档过程中发生错误: {str(e)}")
        return False

def update_document(token, document_id):
    """更新文档内容"""
    try:
        logging.info(f"尝试更新文档，ID: {document_id}...")
        headers = {'Authorization': f'Bearer {token}'}
        update_data = {
            'title': '更新后的测试文档',
            'content': '<h1>更新后的测试文档</h1><p>这个文档已经被API测试脚本更新。</p>'
        }
        
        response = requests.put(
            f"{BASE_URL}/document/{document_id}",
            json=update_data,
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == '200':
                logging.info("文档更新成功")
                return True
            else:
                logging.error(f"更新文档失败: {data.get('message')}")
                return False
        else:
            logging.error(f"更新文档请求失败: {response.status_code}")
            return False
    except Exception as e:
        logging.error(f"更新文档过程中发生错误: {str(e)}")
        return False

def favorite_document(token, document_id):
    """将文档加入收藏"""
    try:
        logging.info(f"尝试收藏文档，ID: {document_id}...")
        headers = {'Authorization': f'Bearer {token}'}
        
        response = requests.put(
            f"{BASE_URL}/document/favorite/{document_id}",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == '200':
                logging.info("文档收藏成功")
                return True
            else:
                logging.error(f"收藏文档失败: {data.get('message')}")
                return False
        else:
            logging.error(f"收藏文档请求失败: {response.status_code}")
            return False
    except Exception as e:
        logging.error(f"收藏文档过程中发生错误: {str(e)}")
        return False

def get_favorite_documents(token):
    """获取收藏文档列表"""
    try:
        logging.info("尝试获取收藏文档列表...")
        headers = {'Authorization': f'Bearer {token}'}
        
        response = requests.get(
            f"{BASE_URL}/document/favorites/user",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == '200':
                documents = data.get('documents', [])
                logging.info(f"获取收藏文档成功，共 {len(documents)} 个文档")
                return True
            else:
                logging.warning(f"获取收藏文档返回: {data.get('message')}")
                return True  # 用户可能没有收藏文档，也是合法的情况
        else:
            logging.error(f"获取收藏文档请求失败: {response.status_code}")
            return False
    except Exception as e:
        logging.error(f"获取收藏文档过程中发生错误: {str(e)}")
        return False

def delete_document_logic(token, document_id):
    """将文档移至回收站（逻辑删除）"""
    try:
        logging.info(f"尝试将文档移至回收站，ID: {document_id}...")
        headers = {'Authorization': f'Bearer {token}'}
        
        response = requests.put(
            f"{BASE_URL}/document/delete/{document_id}",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == '200':
                logging.info("文档已移至回收站")
                return True
            else:
                logging.error(f"移动文档到回收站失败: {data.get('message')}")
                return False
        else:
            logging.error(f"移动文档到回收站请求失败: {response.status_code}")
            return False
    except Exception as e:
        logging.error(f"移动文档到回收站过程中发生错误: {str(e)}")
        return False

def get_deleted_documents(token):
    """获取回收站文档列表"""
    try:
        logging.info("尝试获取回收站文档列表...")
        headers = {'Authorization': f'Bearer {token}'}
        
        response = requests.get(
            f"{BASE_URL}/document/deleted/user",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == '200':
                documents = data.get('documents', [])
                logging.info(f"获取回收站文档成功，共 {len(documents)} 个文档")
                return True
            else:
                logging.warning(f"获取回收站文档返回: {data.get('message')}")
                return True  # 回收站可能是空的，也是合法的情况
        else:
            logging.error(f"获取回收站文档请求失败: {response.status_code}")
            return False
    except Exception as e:
        logging.error(f"获取回收站文档过程中发生错误: {str(e)}")
        return False

if __name__ == '__main__':
    print("开始测试文档API...")
    test_document_api() 