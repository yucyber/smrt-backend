from app import create_app

app = create_app()
socketio = app.socketio


# 为了方便测试，添加一个简单的路由
@app.route('/')
def index():
    return 'Hello, World! WebSocket Server is running.'


if __name__ == '__main__':
    # 使用SocketIO运行应用，支持WebSocket
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)
