#!/usr/bin/env python3
"""
Y.js WebSocket服务器
用于处理Tiptap协同编辑的Y.js协议
"""

import asyncio
import websockets
import json
import logging
from typing import Dict, Set

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 存储文档和连接
documents: Dict[str, Dict] = {}
connections: Dict[str, Set] = {}

class YjsWebSocketServer:
    def __init__(self, host='localhost', port=1234):
        self.host = host
        self.port = port
        
    async def register_client(self, websocket, document_id):
        """注册客户端连接"""
        if document_id not in connections:
            connections[document_id] = set()
        connections[document_id].add(websocket)
        
        if document_id not in documents:
            documents[document_id] = {
                'state': b'',  # Y.js文档状态
                'updates': []  # 更新历史
            }
        
        logger.info(f"客户端连接到文档 {document_id}，当前连接数: {len(connections[document_id])}")
        
        # 发送当前文档状态给新连接的客户端
        if documents[document_id]['state']:
            await websocket.send(documents[document_id]['state'])
    
    async def unregister_client(self, websocket, document_id):
        """注销客户端连接"""
        if document_id in connections:
            connections[document_id].discard(websocket)
            if not connections[document_id]:
                # 如果没有连接了，可以选择清理文档状态
                pass
        logger.info(f"客户端断开文档 {document_id}，当前连接数: {len(connections.get(document_id, set()))}")
    
    async def broadcast_update(self, websocket, document_id, update):
        """广播更新给其他客户端"""
        if document_id in connections:
            # 保存更新到文档历史
            documents[document_id]['updates'].append(update)
            
            # 广播给除发送者外的所有客户端
            disconnected = set()
            for client in connections[document_id]:
                if client != websocket:
                    try:
                        await client.send(update)
                    except websockets.exceptions.ConnectionClosed:
                        disconnected.add(client)
            
            # 清理断开的连接
            for client in disconnected:
                connections[document_id].discard(client)
    
    async def handle_client(self, websocket, path):
        """处理客户端连接"""
        # 从路径中提取文档ID
        document_id = path.strip('/')
        if not document_id:
            document_id = 'default'
        
        try:
            await self.register_client(websocket, document_id)
            
            async for message in websocket:
                # Y.js发送的是二进制数据
                if isinstance(message, bytes):
                    await self.broadcast_update(websocket, document_id, message)
                else:
                    # 处理文本消息（如果有的话）
                    logger.info(f"收到文本消息: {message}")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"客户端连接关闭: {document_id}")
        except Exception as e:
            logger.error(f"处理客户端连接时出错: {e}")
        finally:
            await self.unregister_client(websocket, document_id)
    
    async def start_server(self):
        """启动WebSocket服务器"""
        logger.info(f"启动Y.js WebSocket服务器: {self.host}:{self.port}")
        
        server = await websockets.serve(
            self.handle_client,
            self.host,
            self.port,
            ping_interval=20,
            ping_timeout=10
        )
        
        logger.info(f"Y.js WebSocket服务器已启动: ws://{self.host}:{self.port}")
        return server

def main():
    """主函数"""
    server = YjsWebSocketServer()
    
    async def run_server():
        websocket_server = await server.start_server()
        await websocket_server.wait_closed()
    
    try:
        asyncio.run(run_server())
    except KeyboardInterrupt:
        logger.info("服务器已停止")

if __name__ == '__main__':
    main()