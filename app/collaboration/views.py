import logging
from flask import request
from flask_socketio import emit, join_room, leave_room, rooms
from flask_jwt_extended import decode_token, get_jwt_identity
from . import collaboration

# 存储文档的协同编辑状态
document_states = {}
# 存储房间中的用户
room_users = {}

logger = logging.getLogger(__name__)

def init_socketio_events(socketio):
    """初始化SocketIO事件处理器"""
    
    @socketio.on('connect')
    def on_connect(auth):
        """客户端连接事件"""
        try:
            logger.info(f"客户端连接: {request.sid}")
            emit('connected', {'status': 'success', 'message': '连接成功'})
        except Exception as e:
            logger.error(f"连接处理错误: {str(e)}")
            emit('error', {'message': '连接失败'})
    
    @socketio.on('disconnect')
    def on_disconnect():
        """客户端断开连接事件"""
        try:
            logger.info(f"客户端断开连接: {request.sid}")
            # 从所有房间中移除用户
            user_rooms = rooms(request.sid)
            for room in user_rooms:
                if room != request.sid:  # 排除默认房间
                    leave_room(room)
                    if room in room_users:
                        room_users[room].discard(request.sid)
                        # 通知房间内其他用户
                        emit('user_left', {
                            'user_id': request.sid,
                            'room': room
                        }, room=room)
        except Exception as e:
            logger.error(f"断开连接处理错误: {str(e)}")
    
    @socketio.on('join_document')
    def on_join_document(data):
        """加入文档协同编辑"""
        try:
            document_id = data.get('document_id')
            user_info = data.get('user_info', {})
            
            if not document_id:
                emit('error', {'message': '文档ID不能为空'})
                return
            
            room = f"doc_{document_id}"
            join_room(room)
            
            # 初始化房间用户列表
            if room not in room_users:
                room_users[room] = set()
            room_users[room].add(request.sid)
            
            # 初始化文档状态
            if document_id not in document_states:
                document_states[document_id] = {
                    'content': '',
                    'version': 0,
                    'operations': []
                }
            
            logger.info(f"用户 {request.sid} 加入文档 {document_id}")
            
            # 发送当前文档状态给新加入的用户
            emit('document_state', {
                'document_id': document_id,
                'state': document_states[document_id],
                'users': list(room_users[room])
            })
            
            # 通知房间内其他用户有新用户加入
            emit('user_joined', {
                'user_id': request.sid,
                'user_info': user_info,
                'room': room
            }, room=room, include_self=False)
            
        except Exception as e:
            logger.error(f"加入文档错误: {str(e)}")
            emit('error', {'message': '加入文档失败'})
    
    @socketio.on('leave_document')
    def on_leave_document(data):
        """离开文档协同编辑"""
        try:
            document_id = data.get('document_id')
            if not document_id:
                return
            
            room = f"doc_{document_id}"
            leave_room(room)
            
            if room in room_users:
                room_users[room].discard(request.sid)
            
            logger.info(f"用户 {request.sid} 离开文档 {document_id}")
            
            # 通知房间内其他用户
            emit('user_left', {
                'user_id': request.sid,
                'room': room
            }, room=room)
            
        except Exception as e:
            logger.error(f"离开文档错误: {str(e)}")
    
    @socketio.on('document_operation')
    def on_document_operation(data):
        """处理文档操作（Y.js更新）"""
        try:
            document_id = data.get('document_id')
            operation = data.get('operation')
            
            if not document_id or not operation:
                emit('error', {'message': '文档ID和操作不能为空'})
                return
            
            room = f"doc_{document_id}"
            
            # 更新文档状态
            if document_id in document_states:
                document_states[document_id]['version'] += 1
                document_states[document_id]['operations'].append(operation)
            
            logger.info(f"文档 {document_id} 收到操作，版本: {document_states[document_id]['version']}")
            
            # 广播操作给房间内其他用户
            emit('document_operation', {
                'document_id': document_id,
                'operation': operation,
                'from_user': request.sid,
                'version': document_states[document_id]['version']
            }, room=room, include_self=False)
            
        except Exception as e:
            logger.error(f"文档操作错误: {str(e)}")
            emit('error', {'message': '操作处理失败'})
    
    @socketio.on('cursor_position')
    def on_cursor_position(data):
        """处理光标位置更新"""
        try:
            document_id = data.get('document_id')
            position = data.get('position')
            user_info = data.get('user_info', {})
            
            if not document_id:
                return
            
            room = f"doc_{document_id}"
            
            # 广播光标位置给房间内其他用户
            emit('cursor_position', {
                'document_id': document_id,
                'position': position,
                'user_id': request.sid,
                'user_info': user_info
            }, room=room, include_self=False)
            
        except Exception as e:
            logger.error(f"光标位置更新错误: {str(e)}")
    
    @socketio.on('awareness_update')
    def on_awareness_update(data):
        """处理用户感知信息更新（选择、光标等）"""
        try:
            document_id = data.get('document_id')
            awareness_data = data.get('awareness')
            
            if not document_id:
                return
            
            room = f"doc_{document_id}"
            
            # 广播感知信息给房间内其他用户
            emit('awareness_update', {
                'document_id': document_id,
                'awareness': awareness_data,
                'user_id': request.sid
            }, room=room, include_self=False)
            
        except Exception as e:
            logger.error(f"感知信息更新错误: {str(e)}")

    return socketio