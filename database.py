# database.py
import logging
from flask_redis import FlaskRedis
from flask_sqlalchemy import SQLAlchemy
import os

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 创建数据库连接实例
db = SQLAlchemy()

# 创建Redis连接实例，当连接失败时不要抛出异常
try:
    redis_client = FlaskRedis(decode_responses=True)
except Exception as e:
    logging.error(f"Redis初始化错误（非关键）: {str(e)}")
    # 创建一个模拟的Redis客户端
    class MockRedis:
        def __init__(self):
            self.store = {}
            logging.warning("使用内存模拟Redis存储")
            
        def init_app(self, app):
            logging.info("初始化模拟Redis客户端")
            
        def get(self, key):
            logging.debug(f"模拟Redis GET: {key}")
            return self.store.get(key)
            
        def set(self, key, value, **kwargs):
            logging.debug(f"模拟Redis SET: {key}")
            self.store[key] = value
            
        def delete(self, key):
            logging.debug(f"模拟Redis DEL: {key}")
            if key in self.store:
                del self.store[key]
    
    redis_client = MockRedis()
    logging.warning("使用模拟Redis客户端替代")
