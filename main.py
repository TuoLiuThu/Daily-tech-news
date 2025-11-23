import os
import datetime
import requests
import json
import pytz
import re

# ================= 配置区域 =================
# 依据 2025 年 11 月官方文档：
# 1.5-flash 已弃用
# 3-pro 是付费模型
# 2.5-flash 是当前的免费主力模型
MODEL_NAME = "gemini-2.5-flash"
API_KEY = os.environ.get("GEMINI_API_KEY")

def get_beijing_time():
    tz = pytz.timezone('Asia/Shanghai')
    return datetime.datetime.now(tz).strftime('%Y年%m月%d日 %H:%M')

def clean_html_content(text):
    """
    清洗函数：强制移除 AI 的废话，只提取 HTML 代码
    """
    # 1. 移除 Markdown 代码块标记
    if "```" in text:
        text = text.replace("```html", "").replace("```", "")
    
    # 2. 正则提取 <!DOCTYPE html> ... </html>
    pattern = r"<!DOCTYPE html>.*</html>"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(0)
    
    return text.strip()

def generate_report():
    current_time = get_beijing_time()
    print(f"Current Time: {current_time}")
    print(f"Connecting to Google API directly (Model: {MODEL_NAME})...")

    if not API_KEY:
        return "<html><body><h1>Error</h1><p>API Key is missing.</p></body></html>"

    # 构造 REST API URL
    url = f"[https://generativelanguage.googleapis.com/v1beta/models/](https://generativelanguage.googleapis.com/v1beta/models/){MODEL_NAME}:generateContent?key={API_KEY}"

    # ================= 核心 Prompt (您的四大板块要求) =================
    system_prompt = f"""
    Time: {current_time}.
    Role: You are an elite AI Industry Analyst.
    Task: Search web for AI news (Past 24h) and generate a single-file HTML5 Dashboard.

    【CRITICAL EXECUTION RULES】
    1. **NO CONVERSATIONAL TEXT**: Output ONLY raw HTML code. Start directly with `<!DOCTYPE html>`.
    2. **Real Links**: Must use Google Search tool to find real URLs.
    3. **Language**: Simplified Chinese.
    4. **Design**: Tailwind CSS, Dark Mode (bg-slate-900), Modern UI.

    【SECTION 1: Tech Leaders (技术进展)】
    * **Goal**: Track top scientists' latest moves.
    * **Target List**: 
        - DeepMind (Demis Hassabis, Jeff Dean, Noam Brown)
        - OpenAI (Sam Altman, Greg Brockman, Jason Wei)
        - Meta (Yann LeCun, Thomas Scialom)
        - Anthropic (Dario Amodei)
    * **Execution**:
        1. Search their Twitter/X, Reddit, or Blogs.
        2. **Requirements**:
           - Core View: What is their latest take on AGI/Reasoning/Scaling?
           - Attitude: Label as [Optimistic / Pessimistic / Warning].
           - **Deep Analysis**: Add a 50-word analysis of the technical implication.
    * **UI**: Use Tabs to switch between companies.
    * **Summary**: A one-sentence summary of today's consensus at the top.

    【SECTION 2: Media Insights (媒体进展)】
    * **Goal**: Deep analysis ONLY. **FILTER OUT** funding news or PR releases.
    * **Target Sources**: 
        - EN: The Information, SemiAnalysis, Stratechery.
        - CN: 机器之心, 量子位, Deep Tech Bloggers.
    * **Execution**:
        1. Filter for articles discussing "Tech Bottlenecks", "Business Models", or "Cost Analysis".
        2. **Requirements**:
           - Title & Link.
           - **Core Insight**: Extract counter-intuitive views or deep data (e.g., HBM3e yield impact).
    * **Summary**: Where is the media focus today? (Training/Inference/App).

    【SECTION 3: Key Events (重点事件)】
    * **Keywords**: GPU, TPU, HBM, NVLink, AWS Trainium, Google Cloud, NVIDIA, AMD.
    * **Execution**:
        1. Classify into: [Hardware | Model | App | Personnel].
        2. **Requirements**: Include specific numbers (money, parameter count, performance gain).

    【SECTION 4: Trending Papers (技术论文)】
    * **Sources**: Hugging Face Daily Papers, arXiv-sanity.
    * **Execution**:
        1. Find 3-5 papers with high social discussion.
        2. **Requirements**:
           - **Pain Point**: What problem does it solve? (e.g., KV Cache optimization).
           - **Path Judgment**: Does it represent a new trend? (e.g., Transformer -> SSM).

    Output ONLY the HTML string.
    """

    # 构造请求体 (REST API 标准)
    payload = {
        "contents": [{"parts": [{"text": system_prompt}]}],
        "tools": [
            # 【关键修复】使用 REST API 标准的工具名 googleSearch (小驼峰)
            {"googleSearch": {}} 
        ],
        "generationConfig": {
            "temperature": 0.5,
            "maxOutputTokens": 8192
        }
    }

    try:
        response = requests.post(
            url, 
            headers={'Content-Type': 'application/json'},
            data=json.dumps(payload),
            timeout=180 # 增加超时，搜索需要时间
        )
        
        if response.status_code != 200:
            print(f"API Error Code: {response.status_code}")
            print(f"API Error Body: {response.text}")
            return f"<html><body><h1>API Error {response.status_code}</h1><p>{response.text}</p></body></html>"

        result = response.json()
        
        try:
            raw_text = result['candidates'][0]['content']['parts'][0]['text']
            # 清洗数据，确保只返回 HTML
            final_html = clean_html_content(raw_text)
            return final_html
        except (KeyError, IndexError):
            return "<html><body><h1>Parsing Error</h1><p>API valid but no content returned (Safe or Filtered).</p></body></html>"

    except Exception as e:
        print(f"Network Exception: {e}")
        return f"<html><body><h1>Network Error</h1><p>{e}</p></body></html>"

if __name__ == "__main__":
    html = generate_report()
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("Job finished.")
