import redis

# 尝试连接Redis
try:
    r = redis.Redis(host='localhost', port=6379, db=0)
    r.ping()  # 测试连接
    print("Redis连接成功!")
    
    # 尝试设置和获取一个值
    r.set('test_key', 'Hello Redis')
    value = r.get('test_key')
    print(f"从Redis获取的值: {value.decode('utf-8')}")
    
except Exception as e:
    print(f"Redis连接失败: {e}") 