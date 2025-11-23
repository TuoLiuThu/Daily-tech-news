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
    """清洗函数：强制移除 AI 的 Markdown 标记，只提取 HTML 代码"""
    # 移除可能存在的 markdown 代码块标记
    text = re.sub(r"```html", "", text, flags=re.IGNORECASE)
    text = re.sub(r"```", "", text)
    
    # 尝试提取 <html>...</html> 之间的内容
    pattern = r"<!DOCTYPE html>.*</html>"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(0)
    
    # 如果没有标准头，尝试提取 html 标签内的内容
    pattern_tag = r"<html.*</html>"
    match_tag = re.search(pattern_tag, text, re.DOTALL)
    if match_tag:
        return match_tag.group(0)
        
    return text.strip()

def generate_report():
    current_time = get_beijing_time()
    print(f"[{current_time}] Starting Job...")
    
    if not API_KEY:
        print("Error: GEMINI_API_KEY not found in environment variables.")
        return "<html><body><h1>Configuration Error</h1><p>API Key is missing.</p></body></html>"

    # 【修复重点】这里必须是纯 URL 字符串，不能包含 Markdown 格式
    base_url = "https://generativelanguage.googleapis.com/v1beta/models/"
    url = f"{base_url}{MODEL_NAME}:generateContent?key={API_KEY}"

    print(f"Target URL: {base_url}{MODEL_NAME}...")

    # ================= 核心 Prompt (增强了来源要求) =================
    # 我们明确要求模型使用 search result 中的 link
    system_prompt = f"""
    Current Time (Beijing): {current_time}.
    Role: You are an elite AI Industry Analyst and Frontend Developer.
    Task: Search the web for AI news (Past 24h-48h) and generate a single-file HTML5 Dashboard.

    【CRITICAL DATA SOURCE RULES】
    1. **GROUNDING**: You MUST use the Google Search tool to find real information.
    2. **CITATIONS**: For EVERY specific claim or news item, you MUST provide a clickable `<a href="...">[Source]</a>` link based on the search results.
    3. **No Hallucinations**: If there is no news for a specific person (e.g., Yann LeCun) in the last 48h, explicitly state "No public updates in the last 48h" instead of inventing content.

    【HTML OUTPUT RULES】
    1. Output ONLY raw HTML code. Start directly with `<!DOCTYPE html>`.
    2. Use Tailwind CSS via CDN for styling. Theme: Dark Mode (bg-gray-900, text-gray-100).
    3. Design: distinct cards, clear typography, responsive layout.

    【CONTENT SECTIONS】

    1. **Tech Leaders (领军人物动态)**
       - Targets: Demis Hassabis, Sam Altman, Greg Brockman, Yann LeCun, Dario Amodei, Ilya Sutskever.
       - Action: Search for their latest Tweets/X posts, Blog updates, or Interviews.
       - Display: A set of cards. Each card MUST have:
         - Person Name & Photo (use a generic placeholder or verify url).
         - **Latest Statement**: A direct quote or summary.
         - **Sentiment**: Label as [Optimistic / Pessimistic / Neutral].
         - **Analyst Take**: Your 50-word deep technical analysis of what this means for AGI/Scaling.
         - **Source Link**: Clickable link to the tweet/post.

    2. **Media Insights (深度媒体扫描)**
       - Sources: The Information, SemiAnalysis, Stratechery, Machine Heart (机器之心).
       - Filter: Exclude funding news. Focus on architecture, infrastructure, and strategic shifts.
       - Display: List format. Title + One sentence "Counter-Intuitive Insight" + Link.

    3. **Key Events (行业大事件)**
       - Keywords: NVIDIA H100/Blackwell, TPU v5/v6, HBM3e, AWS Trainium, Azure Maia.
       - Content: Industry shifts, massive cluster deployments, key personnel moves (e.g., Researchers leaving OAI).
       - Requirement: Include specific numbers (e.g., "100k GPU cluster", "$50M training cost").

    4. **Trending Research (论文与博客)**
       - Sources: Hugging Face Daily Papers, arXiv-sanity, leading tech blogs.
       - Display: Top 3-5 items.
       - Fields:
         - Title.
         - **Pain Point**: What specific problem does this solve? (e.g., "KV Cache memory usage").
         - **Judgment**: Is this SOTA? Is it a new path?

    Generate the HTML now.
    """

    payload = {
        "contents": [{"parts": [{"text": system_prompt}]}],
        # 工具定义：使用 Google Search
        "tools": [
            {"googleSearch": {}} 
        ],
        "generationConfig": {
            "temperature": 0.4, # 降低温度以减少幻觉
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
            print(f"API Error Body: {response.text}")
            return f"<html><body><h1>API Error {response.status_code}</h1><p>{response.text}</p></body></html>"

        result = response.json()
        
        # 解析返回结果
        try:
            # 尝试获取文本部分
            candidates = result.get('candidates', [])
            if not candidates:
                print("No candidates returned.")
                return "<html><body><h1>Error</h1><p>No content generated.</p></body></html>"
                
            part = candidates[0]['content']['parts'][0]
            raw_text = part.get('text', '')
            
            # 这是一个保险措施：有时候模型会把搜索结果放在 groundingMetadata 里，
            # 但 gemini-2.5-flash 通常会直接融合在文本里。
            # 如果 raw_text 为空，检查是不是因为只有函数调用（不太可能，因为我们没定义Function Calling）
            if not raw_text:
                print("Empty text received.")
                return "<html><body><h1>Empty Response</h1><p>Model returned no text.</p></body></html>"

            final_html = clean_html_content(raw_text)
            print("Report generated successfully.")
            return final_html
            
        except (KeyError, IndexError) as e:
            print(f"Parsing Exception: {e}")
            return f"<html><body><h1>Parsing Error</h1><p>{str(e)}</p><pre>{json.dumps(result, indent=2)}</pre></body></html>"

    except Exception as e:
        print(f"Network Exception: {e}")
        return f"<html><body><h1>Network Error</h1><p>{e}</p></body></html>"

if __name__ == "__main__":
    # 执行生成并写入 index.html
    html_content = generate_report()
    
    # 写入文件，方便 Github Pages 或本地查看
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print("Done. Output saved to index.html")
