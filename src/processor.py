"""
访谈处理模块 - Interview Processor Module
使用 Gemini 1.5 Pro API 进行多模态分析
"""

import os
import time
import logging
import google.generativeai as genai
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def configure_gemini(api_key=None):
    """配置 Gemini API / Configure Gemini API."""
    key = api_key or os.getenv("GEMINI_API_KEY")
    if not key:
        logger.error("No API key provided.")
        raise ValueError("Gemini API Key is required. / 需要提供 Gemini API 密钥。")
    genai.configure(api_key=key)

def upload_file_to_gemini(file_path):
    """上传文件到 Gemini File API / Upload file to Gemini File API."""
    try:
        logger.info(f"Uploading file: {file_path}")
        file_upload = genai.upload_file(file_path)
        logger.info(f"File uploaded. URI: {file_upload.uri}")
        
        # Poll for processing completion
        while file_upload.state.name == "PROCESSING":
            logger.info("File is processing...")
            time.sleep(2)
            file_upload = genai.get_file(file_upload.name)
            
        if file_upload.state.name == "FAILED":
            logger.error("File processing failed.")
            raise RuntimeError("Gemini File API processing failed. / 文件处理失败。")
            
        logger.info(f"File ready. State: {file_upload.state.name}")
        return file_upload
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise

def analyze_interview(file_path, language="zh"):
    """
    分析访谈内容 / Analyze interview content using Gemini 1.5 Pro.
    
    Args:
        file_path (str): 本地文件路径 / Path to the local file
        language (str): 输出语言 "zh" 或 "en" / Output language
        
    Returns:
        dict: 包含 'transcript', 'summary', 'mind_map' 的字典
    """
    # 1. Upload File
    uploaded_file = upload_file_to_gemini(file_path)
    
    # 2. Select Model (Gemini 2.5 Flash)
    model = genai.GenerativeModel(model_name="gemini-2.5-flash")
    
    # 3. Construct Prompts
    results = {}
    
    # Language-specific instructions
    if language == "zh":
        base_instruction = """
        你是一位专业的访谈分析专家，同时也是一位秘书。
        你的任务是分析提供的访谈录音/视频/图片。
        请用中文回复。
        """
        transcript_prompt = "生成访谈的逐字稿。区分不同发言人很重要。格式为 '发言人: 内容'。"
        summary_prompt = """
        提供访谈的全面总结。包括：
        1. **执行摘要**：高层次概述（约100字）
        2. **关键要点**：讨论的主要议题（要点列表）
        3. **行动事项/结论**：提到的任何决定或后续步骤
        4. **详细笔记**：内容的结构化分解
        """
        mind_map_prompt = """
        使用 Mermaid.js 语法创建访谈内容的思维导图。
        注重主题和子主题的层级结构。
        
        只输出 Mermaid 代码，不要包含其他说明文字。
        使用中文节点标签。
        
        示例格式：
        mindmap
          root((访谈主题))
            话题1
              要点A
              要点B
            话题2
              要点C
        """
    else:
        base_instruction = """
        You are an expert Interview Analyst acting as a professional secretary.
        Your task is to analyze the provided interview recording/image.
        """
        transcript_prompt = "Generate a verbatim transcript of this interview. Speaker distinction is important. Format as 'Speaker: Text'."
        summary_prompt = """
        Provide a comprehensive summary of the interview.
        Include:
        1. **Executive Summary**: A high-level overview (100 words).
        2. **Key Topics**: Bullet points of main subjects discussed.
        3. **Action Items/Conclusions**: Any decisions or next steps mentioned.
        4. **Detailed Notes**: A structured breakdown of the content.
        """
        mind_map_prompt = """
        Create a Mind Map of the interview content using Mermaid.js syntax.
        Focus on the hierarchy of topics and subtopics.
        
        Output ONLY the Mermaid code, no other text.
        
        Example format:
        mindmap
          root((Interview Topic))
            Topic 1
              Subpoint A
              Subpoint B
            Topic 2
              Subpoint C
        """
    
    # -- Transcript --
    logger.info("Generating transcript...")
    response = model.generate_content([uploaded_file, base_instruction, transcript_prompt])
    results["transcript"] = response.text
        
    # -- Summary --
    logger.info("Generating summary...")
    response = model.generate_content([uploaded_file, base_instruction, summary_prompt])
    results["summary"] = response.text
        
    # -- Mind Map --
    logger.info("Generating mind map...")
    response = model.generate_content([uploaded_file, base_instruction, mind_map_prompt])
    # Clean up code blocks
    text = response.text
    if "```mermaid" in text:
        text = text.split("```mermaid")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].strip()
    results["mind_map"] = text
    
    return results

def generate_report(results, filename="interview_report"):
    """
    生成 Markdown 格式的完整报告 / Generate full Markdown report.
    
    Args:
        results (dict): analyze_interview 的返回结果
        filename (str): 报告文件名（不含扩展名）
        
    Returns:
        str: Markdown 格式的报告内容
    """
    report = f"""# 📋 访谈分析报告 / Interview Analysis Report

## 📝 访谈纪要 / Summary

{results.get("summary", "无摘要 / No summary")}

---

## 🗺️ 信息框图 / Mind Map

```mermaid
{results.get("mind_map", "mindmap\\n  root((No Data))")}
```

---

## 📜 访谈正文 / Transcript

{results.get("transcript", "无转录 / No transcript")}

---

*由访谈总结器自动生成 / Generated by Interview Summarizer*
"""
    return report
