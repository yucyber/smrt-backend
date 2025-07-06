import os
import sys
import logging
import pymysql
from dotenv import load_dotenv

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def apply_migration():
    # 加载环境变量
    load_dotenv()
    
    # 获取数据库连接信息
    db_uri = os.getenv('SQLALCHEMY_DATABASE_URI')
    if not db_uri:
        db_uri = 'mysql+pymysql://root:root@localhost/smart_editor'
        logging.warning(f"数据库URI未设置，使用默认MySQL数据库: {db_uri}")
    
    # 解析数据库连接信息
    # 格式: mysql+pymysql://username:password@host:port/database
    try:
        # 移除协议部分
        db_info = db_uri.split('://', 1)[1]
        # 分离用户名密码和主机信息
        auth, rest = db_info.split('@', 1)
        username, password = auth.split(':', 1)
        # 分离主机和数据库名
        if '/' in rest:
            host_port, database = rest.split('/', 1)
        else:
            host_port, database = rest, 'smart_editor'
        
        # 分离主机和端口
        if ':' in host_port:
            host, port = host_port.split(':', 1)
            port = int(port)
        else:
            host, port = host_port, 3306
    except Exception as e:
        logging.error(f"解析数据库连接字符串失败: {str(e)}")
        sys.exit(1)
    
    # 连接数据库
    try:
        conn = pymysql.connect(
            host=host,
            port=port,
            user=username,
            password=password,
            database=database,
            charset='utf8mb4'
        )
        logging.info(f"成功连接到数据库: {host}:{port}/{database}")
    except Exception as e:
        logging.error(f"连接数据库失败: {str(e)}")
        sys.exit(1)
    
    # 读取SQL文件
    try:
        with open('add_share_token.sql', 'r') as f:
            sql_script = f.read()
        logging.info("成功读取SQL迁移脚本")
    except Exception as e:
        logging.error(f"读取SQL文件失败: {str(e)}")
        conn.close()
        sys.exit(1)
    
    # 执行SQL脚本
    try:
        cursor = conn.cursor()
        # 按语句分割并执行
        for statement in sql_script.split(';'):
            if statement.strip():
                cursor.execute(statement)
                logging.info(f"执行SQL语句: {statement.strip()}")
        conn.commit()
        logging.info("成功应用数据库迁移")
    except Exception as e:
        logging.error(f"执行SQL脚本失败: {str(e)}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    logging.info("开始应用数据库迁移...")
    apply_migration()
    logging.info("数据库迁移完成")