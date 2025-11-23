import os
import datetime
import requests
import json
import pytz

# ================= 配置区域 =================
# 使用 gemini-2.0-flash (免费且支持搜索)
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

    # 1. 构造 URL
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={API_KEY}"

    # 2. 构造超详细的 Prompt (融合了你的四个板块要求)
    system_prompt = f"""
    你是一个专业的 AI 行业首席分析师。当前北京时间是：{current_time}。
    请利用 Google Search 联网搜索过去 24 小时的信息，生成一份 HTML5 格式的《AI 硬科技日报》。

    【全局原则】
    1. **真实性**：必须使用 Google Search 找到的真实信息，严禁编造。
    2. **链接溯源**：每一个具体的新闻/观点/论文，都**必须**附带原始 URL 链接（如果是推特，尽量指向具体推文；如果找不到，链接到相关新闻报道）。
    3. **语言**：所有可见文字必须是**简体中文**。
    4. **深度**：不要罗列流水账，要进行技术和商业逻辑的分析。

    【板块 1：技术领袖与进展 (Tech Leaders)】
    * **核心任务**：追踪顶级科学家最新动态。
    * **重点关注对象**：
        - **DeepMind**: Demis Hassabis, Jeff Dean, Noam Brown (重点关注)。
        - **OpenAI/Meta**: 官方技术博客及核心研究员。
    * **搜索策略**：搜索 Twitter/X 上上述人员的最新推文，或 Reddit/Hacker News 上的讨论。
    * **内容要求**：
        - 提取核心观点（对 AGI、推理、Scaling Law 的看法）。
        - 判断态度（乐观/悲观/警告）。
        - **深度解读**：用 50 字分析其背后的技术含义。
    * **UI展示**：请在 HTML 中使用 Tab 切换（DeepMind | OpenAI | Meta）。
    * **板块总结**：在顶部用一段话总结今日领袖们的共识或分歧。

    【板块 2：媒体深度见解 (Media Insights)】
    * **核心任务**：梳理深度媒体见解，**过滤掉单纯的融资新闻或通稿**。
    * **目标源**：
        - 英文：The Information, SemiAnalysis (Dylan Patel), Stratechery, Sequoia Blog.
        - 中文：机器之心，量子位，知乎/公众号深度评论（如瓦砾村夫）。
    * **筛选标准**：重点关注“技术瓶颈”、“商业模式闭环”、“算力成本分析”。
    * **内容要求**：文章标题 + 核心洞察（反直觉观点/深度数据） + 来源链接。
    * **板块总结**：今日媒体关注焦点在哪个环节（训练/推理/应用）？

    【板块 3：当日重点事件 (Key Events)】
    * **核心任务**：行业重大事件回顾。
    * **关键词**：GPU, TPU, HBM, NVLink, AWS Trainium, Google Cloud, NVIDIA, AMD, 融资, 离职。
    * **内容要求**：
        - 事件分类：[硬件 | 模型 | 应用 | 人事]。
        - 事件描述：包含具体金额、参数量或性能数据。
    
    【板块 4：技术论文 (Trending Papers)】
    * **核心任务**：热门论文与路径分析。
    * **数据源**：Hugging Face Daily Papers, arXiv-sanity, Papers with Code.
    * **内容要求**：
        - 找出今日讨论度最高的 3-5 篇论文。
        - **重点分析**：解决了什么痛点（如 KV Cache, 长文本）？
        - **路径判断**：是否代表新趋势（如 SSM, 新 RLHF）？

    【HTML 输出规范】
    * 输出且**仅输出**一段完整的 HTML 代码，以 `<!DOCTYPE html>` 开头。
    * 使用 **Tailwind CSS** (通过 CDN) 进行美化。
    * **深色模式 (Dark Mode)**：背景色 `bg-slate-900`，文字 `text-slate-100`。
    * **卡片设计**：使用 `bg-slate-800` 和圆角设计。
    * 包含必要的 JavaScript 以实现板块 1 的 Tab 切换功能。
    """

    # 3. 构造请求体
    payload = {
        "contents": [{
            "parts": [{"text": system_prompt}]
        }],
        "tools": [
            # 强制开启 Google 搜索
            {"googleSearch": {}}
        ],
        "generationConfig": {
            "temperature": 0.7, 
            "maxOutputTokens": 8192
        }
    }

    try:
        # 4. 发送请求
        response = requests.post(
            url, 
            headers={'Content-Type': 'application/json'},
            data=json.dumps(payload),
            timeout=180 # 增加超时时间，因为搜索需要时间
        )
        
        if response.status_code != 200:
            print(f"API Error: {response.status_code}")
            return f"<html><body><h1>API Error</h1><p>{response.text}</p></body></html>"

        result = response.json()
        
        try:
            html_content = result['candidates'][0]['content']['parts'][0]['text']
            if "```" in html_content:
                html_content = html_content.replace("```html", "").replace("```", "")
            return html_content.strip()
        except (KeyError, IndexError):
            return f"<html><body><h1>Parsing Error</h1><p>API 返回数据无法解析</p></body></html>"

    except Exception as e:
        return f"<html><body><h1>Network Error</h1><p>{e}</p></body></html>"

if __name__ == "__main__":
    html = generate_report()
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("Job finished.")
