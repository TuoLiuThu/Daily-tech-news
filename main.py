import os
import datetime
import requests
import json
import pytz
import re

# ================= 配置区域 =================
# 听您的：1.5 已死，2.0 没额度。
# 我们锁定 gemini-2.5-flash，修复 URL 格式错误后它应该能跑。
MODEL_NAME = "gemini-2.5-flash"
API_KEY = os.environ.get("GEMINI_API_KEY")

def get_beijing_time():
    tz = pytz.timezone('Asia/Shanghai')
    return datetime.datetime.now(tz).strftime('%Y年%m月%d日 %H:%M')

def clean_html_content(text):
    """清洗函数：只保留 HTML 代码"""
    if "```" in text:
        text = text.replace("```html", "").replace("```", "")
    
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

    # 【关键修复】这里是纯净的字符串，绝对没有 markdown 符号
    url = f"[https://generativelanguage.googleapis.com/v1beta/models/](https://generativelanguage.googleapis.com/v1beta/models/){MODEL_NAME}:generateContent?key={API_KEY}"

    # ================= 您的四大板块核心 Prompt =================
    system_prompt = f"""
    Time: {current_time}.
    Role: You are an elite AI Industry Analyst.
    Task: Search web for AI news (Past 24h) and generate a single-file HTML5 Dashboard.

    【CRITICAL EXECUTION RULES】
    1. **NO CONVERSATIONAL TEXT**: Output ONLY raw HTML code. Start directly with `<!DOCTYPE html>`.
    2. **Real Links**: Must use Google Search tool to find real URLs.
    3. **Language**: Simplified Chinese.
    4. **Design**: Tailwind CSS, Dark Mode (bg-slate-900).

    【SECTION 1: Tech Leaders (技术进展)】
    * **Target**: DeepMind (Demis Hassabis, Jeff Dean, Noam Brown), OpenAI (Sam Altman, Greg Brockman), Meta (Yann LeCun), Anthropic (Dario Amodei).
    * **Execution**:
        1. Search their Twitter/X, Reddit, or Blogs.
        2. **Requirements**:
           - Core View: What is their latest take on AGI/Reasoning/Scaling?
           - Attitude: Label as [Optimistic / Pessimistic / Warning].
           - **Deep Analysis**: Add a 50-word analysis of the technical implication.
    * **UI**: Use Tabs to switch between companies.

    【SECTION 2: Media Insights (媒体进展)】
    * **Filter**: **NO** funding news/PR releases. Deep analysis ONLY.
    * **Sources**: The Information, SemiAnalysis, Stratechery, 机器之心.
    * **Requirements**:
        - Title & Link.
        - **Core Insight**: Extract counter-intuitive views or deep data.
    * **Summary**: Focus area (Training/Inference/App).

    【SECTION 3: Key Events (重点事件)】
    * **Keywords**: GPU, TPU, HBM, NVLink, AWS Trainium, NVIDIA.
    * **Requirements**: Include specific numbers (money, parameter count, performance gain).

    【SECTION 4: Trending Papers (技术论文)】
    * **Sources**: Hugging Face Daily Papers, arXiv-sanity.
    * **Requirements**:
        - **Pain Point**: What problem does it solve?
        - **Path Judgment**: Does it represent a new trend?

    Output ONLY the HTML string.
    """

    payload = {
        "contents": [{"parts": [{"text": system_prompt}]}],
        "tools": [{"googleSearch": {}}],
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
            timeout=180
        )
        
        # 错误处理
        if response.status_code != 200:
            print(f"API Error Code: {response.status_code}")
            return f"<html><body><h1>API Error {response.status_code}</h1><p>{response.text}</p></body></html>"

        result = response.json()
        
        try:
            raw_text = result['candidates'][0]['content']['parts'][0]['text']
            final_html = clean_html_content(raw_text)
            return final_html
        except (KeyError, IndexError):
            return "<html><body><h1>Parsing Error</h1><p>API structure mismatch.</p></body></html>"

    except Exception as e:
        print(f"Network Exception: {e}")
        return f"<html><body><h1>Network Error</h1><p>{e}</p></body></html>"

if __name__ == "__main__":
    html = generate_report()
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("Job finished.")
