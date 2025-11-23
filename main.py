import os
import datetime
import requests
import json
import pytz
import time

# ================= 配置区域 =================
# 使用目前免费且最强的实验模型 (Gemini 2.0 Flash Exp)
# 该模型在 API 中免费，且支持搜索
MODEL_NAME = "gemini-2.0-flash-exp"
API_KEY = os.environ.get("GEMINI_API_KEY")

def get_beijing_time():
    tz = pytz.timezone('Asia/Shanghai')
    return datetime.datetime.now(tz).strftime('%Y年%m月%d日 %H:%M')

def generate_report():
    current_time = get_beijing_time()
    print(f"Current Time: {current_time}")
    print(f"Connecting to Google API directly (Model: {MODEL_NAME})...")

    if not API_KEY:
        print("Error: API Key not found!")
        return "<html><body><h1>Error</h1><p>API Key is missing.</p></body></html>"

    # 1. 构造 REST API URL
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={API_KEY}"

    # 2. 构造请求体 (严格遵循 Google REST 标准)
    # 使用 camelCase (小驼峰) 命名，确保兼容性
    payload = {
        "contents": [{
            "parts": [{
                "text": f"""
                Current Time (Beijing): {current_time}
                Task: Search the web for AI news in the past 24 hours and generate a single-file HTML5 Dashboard.
                
                【核心要求】
                1. **必须联网**: 使用 Google Search 工具获取真实信息。
                2. **真实链接**: 必须保留原始 URL，不要编造。
                3. **监测名单**: 
                   - DeepMind (Demis Hassabis, Jeff Dean)
                   - OpenAI (Sam Altman, Greg Brockman, Noam Brown)
                   - Meta (Yann LeCun)
                   - Anthropic (Dario Amodei)
                4. **空状态**: 若无动态，显示“今日无动态”。
                
                【HTML 规范】
                1. 使用 Tailwind CSS (CDN)。
                2. 深色模式 (Dark Mode, bg-slate-900)。
                3. 包含 JavaScript 实现 Tab 切换。
                4. 所有文字为简体中文。
                
                Output ONLY raw HTML code starting with <!DOCTYPE html>.
                """
            }]
        }],
        "tools": [
            # 【关键】直接发送 REST API 标准的工具定义
            # 使用 "googleSearch": {} 而非 Python SDK 的写法
            {"googleSearch": {}}
        ],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 8192
        }
    }

    try:
        # 3. 发送 POST 请求
        response = requests.post(
            url, 
            headers={'Content-Type': 'application/json'},
            data=json.dumps(payload),
            timeout=120 # 设置较长超时防止中断
        )
        
        # 4. 错误处理
        if response.status_code != 200:
            print(f"API Error: {response.status_code}")
            print(f"Response: {response.text}")
            return f"<html><body><h1>API Error {response.status_code}</h1><p>{response.text}</p></body></html>"

        # 5. 解析响应
        result = response.json()
        
        try:
            # 提取生成的 HTML 文本
            # 路径：candidates[0] -> content -> parts[0] -> text
            html_content = result['candidates'][0]['content']['parts'][0]['text']
            
            # 清理 Markdown 标记 (```html ... ```)
            if "```" in html_content:
                html_content = html_content.replace("```html", "").replace("```", "")
            
            return html_content.strip()
            
        except (KeyError, IndexError) as e:
            print(f"Parsing Error. Structure might be unexpected: {result}")
            return f"<html><body><h1>Parsing Error</h1><p>{e}</p></body></html>"

    except Exception as e:
        print(f"Network Error: {e}")
        return f"<html><body><h1>Network Error</h1><p>{e}</p></body></html>"

if __name__ == "__main__":
    html = generate_report()
    
    # 写入文件
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)
    
    print("Job finished. Check index.html content.")
