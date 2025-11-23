import os
import datetime
import requests
import json
import pytz
import re
import sys

# ================= 配置区域 =================
# 必须从环境变量获取 KEY，Github Actions 中需在 Secrets 设置 GEMINI_API_KEY
API_KEY = os.environ.get("GEMINI_API_KEY")
MODEL_NAME = "gemini-2.5-flash" 

def get_beijing_time():
    tz = pytz.timezone('Asia/Shanghai')
    return datetime.datetime.now(tz).strftime('%Y年%m月%d日 %H:%M')

def clean_html_content(text):
    """
    清洗函数：强制移除 AI 的 Markdown 标记，只提取 HTML 代码
    增强容错：即使没有闭合的 </html>，也尝试提取主要内容
    """
    # 移除可能存在的 markdown 代码块标记
    text = re.sub(r"```html", "", text, flags=re.IGNORECASE)
    text = re.sub(r"```", "", text)
    
    # 优先：尝试提取完整的 <!DOCTYPE html>...</html>
    pattern = r"<!DOCTYPE html>.*</html>"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(0)
    
    # 备选1：尝试提取 <html...</html>
    pattern_tag = r"<html.*</html>"
    match_tag = re.search(pattern_tag, text, re.DOTALL)
    if match_tag:
        return match_tag.group(0)
        
    # 备选2（容错）：如果模型截断了，找到 <!DOCTYPE html> 开始的地方，返回之后所有内容
    start_pattern = r"<!DOCTYPE html>"
    start_match = re.search(start_pattern, text)
    if start_match:
        print("Warning: HTML might be truncated, returning partial content.")
        return text[start_match.start():]

    return text.strip()

def generate_report():
    current_time = get_beijing_time()
    print(f"[{current_time}] Starting Job...")
    
    if not API_KEY:
        print("Error: GEMINI_API_KEY not found in environment variables.")
        return "<html><body><h1>Configuration Error</h1><p>API Key is missing.</p></body></html>"

    base_url = "https://generativelanguage.googleapis.com/v1beta/models/"
    url = f"{base_url}{MODEL_NAME}:generateContent?key={API_KEY}"

    print(f"Target URL: {base_url}{MODEL_NAME}...")

    # ================= 核心 Prompt (强结构化版本) =================
    system_prompt = f"""
    Current Time (Beijing): {current_time}.
    Role: You are an elite AI Industry Analyst and Frontend Developer.
    Task: Search web for AI news (Past 24h-48h) and generate a **COMPLETE** HTML5 Dashboard with exactly 4 distinct sections.

    【CRITICAL EXECUTION PROTOCOL】
    1. **COMPLETENESS IS MANDATORY**: You MUST output ALL 4 SECTIONS defined below. Do not stop after the first section.
    2. **Grounding**: Use Google Search to find real URLs.
    3. **Citations**: Every news item must have a `<a href="...">[Source]</a>` link.
    4. **Language**: Content in Simplified Chinese (简体中文).

    【HTML OUTPUT FORMAT】
    - Start with `<!DOCTYPE html>`.
    - Use Tailwind CSS (Dark Mode: bg-slate-900 text-slate-50).
    - Use distinct styling (colors/borders) to separate the 4 sections visually.

    【REQUIRED SECTIONS - DO NOT SKIP ANY】

    --- SECTION 1: Tech Leaders (领军人物) ---
    - **Limit**: Max 4-5 key figures (e.g., Altman, Hassabis, LeCun, Amodei).
    - **Content**: Latest tweet/quote. 
    - **Analyst Take**: Concise (max 30 words) technical implication.
    - **Layout**: Grid of Cards.

    --- SECTION 2: Media Insights (深度媒体) ---
    - **Sources**: The Information, SemiAnalysis, Stratechery, 机器之心.
    - **Content**: 3-4 deep dive articles. Title + "Counter-Intuitive Insight" + Link.
    - **Layout**: Vertical List with highlight borders.

    --- SECTION 3: Key Events (行业大事件) ---
    - **Focus**: Infrastructure (GPUs, Clusters), Industry shifts.
    - **Content**: 3-4 major events with specific numbers (e.g., "$50M", "100k H100").
    - **Layout**: Timeline or distinct alert boxes.

    --- SECTION 4: Trending Papers & Blogs (技术风向) ---
    - **Sources**: Hugging Face, arXiv.
    - **Content**: Top 3 papers/blogs.
    - **Fields**: Title + Pain Point Solved + Link.
    - **Layout**: Simple clean list.

    Generating incomplete HTML is a failure. Start generating now.
    """

    payload = {
        "contents": [{"parts": [{"text": system_prompt}]}],
        "tools": [{"googleSearch": {}}],
        "generationConfig": {
            "temperature": 0.4,
            "maxOutputTokens": 8192
        }
    }

    try:
        print("Sending request to Gemini API (with Search Tool)...")
        response = requests.post(
            url, 
            headers={'Content-Type': 'application/json'},
            data=json.dumps(payload),
            timeout=180 
        )
        
        if response.status_code != 200:
            print(f"API Error Code: {response.status_code}")
            return f"<html><body><h1>API Error {response.status_code}</h1><p>{response.text}</p></body></html>"

        result = response.json()
        
        try:
            candidates = result.get('candidates', [])
            if not candidates:
                return "<html><body><h1>Error</h1><p>No content generated.</p></body></html>"
                
            raw_text = candidates[0]['content']['parts'][0].get('text', '')
            
            if not raw_text:
                return "<html><body><h1>Empty Response</h1><p>Model returned no text.</p></body></html>"

            # 打印生成文本长度，用于调试
            print(f"Generated text length: {len(raw_text)} chars")
            
            final_html = clean_html_content(raw_text)
            
            # 简单检查是否包含关键板块标题，如果没有则发出警告
            if "SECTION 4" not in system_prompt and "Trending Papers" not in final_html:
                 print("Warning: Section 4 might be missing.")

            print("Report generated successfully.")
            return final_html
            
        except (KeyError, IndexError) as e:
            print(f"Parsing Exception: {e}")
            return f"<html><body><h1>Parsing Error</h1><p>{str(e)}</p></body></html>"

    except Exception as e:
        print(f"Network Exception: {e}")
        return f"<html><body><h1>Network Error</h1><p>{e}</p></body></html>"

if __name__ == "__main__":
    html_content = generate_report()
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    print("Done. Output saved to index.html")
