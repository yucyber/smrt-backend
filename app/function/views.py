import os
import json  # 添加这一行
from time import sleep
import base64
import requests
from dotenv import load_dotenv
from flask import jsonify, request, Response
from flask_jwt_extended import jwt_required
import erniebot

from . import function

load_dotenv()

# SiliconFlow API配置
SILICONFLOW_API_KEY = os.getenv('SILICONFLOW_API_KEY')
SILICONFLOW_BASE_URL = "https://api.siliconflow.cn/v1/chat/completions"

# ChatGLM API配置
CHATGLM_API_URL = os.getenv('CHATGLM_API_URL', 'https://open.bigmodel.cn/api/paas/v4/chat/completions')
CHATGLM_API_KEY = os.getenv('CHATGLM_API_KEY', '填写key')


@function.route('/ocr', methods=['POST'])
def ocr():
    # 检查是否有文件被上传
    if 'file' not in request.files:
        return jsonify({'message': '无文件上传!', 'code': 400})
    file = request.files['file']
    if file.filename == '':
        return jsonify({'message': '无文件上传!', 'code': 400})
    image_bytes = file.read()
    image_base64 = base64.b64encode(image_bytes).decode('ascii')
    headers = {
        "Authorization": f"token {os.getenv('ACCESS_TOKEN')}",
        "Content-Type": "application/json"
    }
    payload = {"image": image_base64}
    try:
        resp = requests.post(url=os.getenv('OCR_API_URL'), json=payload, headers=headers)
        resp.raise_for_status()
        ocr_result = resp.json()["result"]
        result = ''
        for text in ocr_result["texts"]:
            result += text["text"] + '\n'
        return jsonify({'message': result, 'code': 200})
    except Exception as e:
        print(f"处理响应时发生错误: {e}")
        return jsonify({'message': '后端小模型OCR服务未启动！', 'code': 400})


@function.route('/asr', methods=['POST'])
def asr():
    if 'file' not in request.files:
        return jsonify({'message': '无文件上传!', 'code': 400})
    file = request.files['file']
    if file.filename == '':
        return jsonify({'message': '无文件上传!', 'code': 400})
    sleep(1.33)
    return jsonify({'message': '后端小模型ASR服务未启动！', 'code': 400})


@function.route('/AIFunc', methods=['POST'])
def AIFunc():
    data = request.get_json()
    command = data['command']
    text = data['text']
    # 根据 command 构建 prompt（省略相同逻辑）
    prompt = build_prompt(command, text, data)

    def generate_siliconflow():
        headers = {
            "Authorization": f"Bearer {SILICONFLOW_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "Qwen/Qwen2.5-7B-Instruct",
            "messages": [{"role": "user", "content": prompt}],
            "stream": True,
            "max_tokens": 2048,
            "temperature": 0.7
        }
        try:
            response = requests.post(
                SILICONFLOW_BASE_URL,
                headers=headers,
                json=payload,
                stream=True,
                timeout=30
            )
            response.raise_for_status()
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        if line.strip() == 'data: [DONE]':
                            break
                        data_json = json.loads(line[6:])
                        choices = data_json.get('choices', [])
                        if choices:
                            content = choices[0].get('delta', {}).get('content', '')
                            if content:
                                yield content
        except Exception as e:
            yield f"处理请求时发生错误: {str(e)}"

    return Response(generate_siliconflow(), content_type='text/event-stream')


@function.route('/chatglm', methods=['POST'])
def chatglm():
    """
    调用 ChatGLM API 的接口
    请求格式：{...}
    响应格式：{'message': 'AI 回复', 'code': 200}
    """
    if not CHATGLM_API_KEY:
        return jsonify({'message': 'ChatGLM API 密钥未配置', 'code': 400})
    data = request.get_json()
    messages = data.get('messages', [])
    model = data.get('model', 'glm-4-flash')
    temperature = data.get('temperature', 0.7)
    top_p = data.get('top_p', 0.9)
    max_tokens = data.get('max_tokens', 1024)
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "top_p": top_p,
        "max_tokens": max_tokens
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {CHATGLM_API_KEY}"
    }
    try:
        resp = requests.post(CHATGLM_API_URL, json=payload, headers=headers)
        resp.raise_for_status()
        result = resp.json()
        ai_msg = result.get('choices', [{}])[0].get('message', {}).get('content', '')
        return jsonify({'message': ai_msg, 'code': 200})
    except Exception as e:
        print(f"调用 ChatGLM API 时发生错误: {e}")
        return jsonify({'message': f'调用 ChatGLM API 失败: {e}', 'code': 500})


@function.route('/chatglm/stream', methods=['POST'])
def chatglm_stream():
    """
    调用 ChatGLM API 的流式响应接口
    """
    if not CHATGLM_API_KEY:
        return jsonify({'message': 'ChatGLM API 密钥未配置', 'code': 400})
    data = request.get_json()
    messages = data.get('messages', [])
    model = data.get('model', 'glm-4-flash')
    temperature = data.get('temperature', 0.7)
    top_p = data.get('top_p', 0.9)
    max_tokens = data.get('max_tokens', 1024)
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "top_p": top_p,
        "max_tokens": max_tokens,
        "stream": True
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {CHATGLM_API_KEY}"
    }
    def generate():
        resp = requests.post(CHATGLM_API_URL, json=payload, headers=headers, stream=True)
        resp.raise_for_status()
        for line in resp.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    data = line[6:]
                    if data == '[DONE]':
                        break
                    try:
                        data_json = json.loads(data)
                        content = data_json.get('choices', [{}])[0].get('delta', {}).get('content', '')
                        if content:
                            yield content
                    except:
                        continue
    return Response(generate(), content_type='text/event-stream')
