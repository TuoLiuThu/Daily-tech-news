import os
import datetime
import requests
import json
import pytz

# ================= 配置区域 =================
# 经过核实，gemini-2.0-flash 是目前的稳定版
# 并且支持 Google Search 工具
MODEL_NAME = "gemini-2.0-flash"
API_KEY = os.environ.get("GEMINI_API_KEY")

def get_beijing_time():
    tz = pytz.timezone('Asia/Shanghai')
    return datetime.datetime.now(tz).strftime('%Y年%m月%d日 %H:%M')

def generate_report():
    current_time = get_beijing_time()
    print(f"Current Time: {current_time}")
    print(f"Connecting to Google API directly (Model: {MODEL_NAME})...")

    if not API_KEY:
        return "<html><body><h1>Error</h1><p>API Key is missing.</p></body></html>"

    # 1. 构造 REST API URL (使用 v1beta 接口)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={API_KEY}"

    # 2. 构造请求体 (严格遵循 Google REST JSON 标准)
    # 注意：REST API 中工具名必须是 camelCase (googleSearch)
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
                   - OpenAI (Sam Altman, Greg Brockman)
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
            # 【关键】直接发送 API 协议要求的原生对象
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
            timeout=120
        )
        
        # 4. 错误处理
        if response.status_code != 200:
            print(f"API Error: {response.status_code}")
            # 如果 2.0 偶尔繁忙，尝试降级到 2.5-flash (备选)
            print(f"Response: {response.text}")
            return f"<html><body><h1>API Error {response.status_code}</h1><p>{response.text}</p></body></html>"

        # 5. 解析响应
        result = response.json()
        
        try:
            # 提取生成的 HTML 文本
            # 路径：candidates[0] -> content -> parts[0] -> text
            html_content = result['candidates'][0]['content']['parts'][0]['text']
            
            # 清理 Markdown
            if "```" in html_content:
                html_content = html_content.replace("```html", "").replace("```", "")
            
            return html_content.strip()
            
        except (KeyError, IndexError) as e:
            print(f"Parsing Error: {result}")
            return f"<html><body><h1>Parsing Error</h1><p>API返回结构异常</p></body></html>"

    except Exception as e:
        print(f"Network Error: {e}")
        return f"<html><body><h1>Network Error</h1><p>{e}</p></body></html>"

if __name__ == "__main__":
    html = generate_report()
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("Job finished.")
