from flask import Blueprint, render_template_string
from flask_socketio import emit

websocket_test = Blueprint('websocket_test', __name__)

# 简单的测试页面HTML
TEST_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>WebSocket Test</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
</head>
<body>
    <h1>WebSocket Connection Test</h1>
    <div id="status">Connecting...</div>
    <div id="messages"></div>
    
    <script>
        const socket = io('http://localhost:5000');
        const status = document.getElementById('status');
        const messages = document.getElementById('messages');
        
        socket.on('connect', function() {
            status.innerHTML = 'Connected!';
            status.style.color = 'green';
            
            // 测试加入文档
            socket.emit('join_document', {
                document_id: 'example-document',
                user_info: { name: 'Test User' }
            });
        });
        
        socket.on('disconnect', function() {
            status.innerHTML = 'Disconnected!';
            status.style.color = 'red';
        });
        
        socket.on('connected', function(data) {
            messages.innerHTML += '<p>Server says: ' + data.message + '</p>';
        });
        
        socket.on('document_state', function(data) {
            messages.innerHTML += '<p>Document state received: ' + JSON.stringify(data) + '</p>';
        });
        
        socket.on('error', function(data) {
            messages.innerHTML += '<p style="color: red;">Error: ' + data.message + '</p>';
        });
    </script>
</body>
</html>
'''

@websocket_test.route('/test')
def test_websocket():
    """WebSocket测试页面"""
    return render_template_string(TEST_HTML)