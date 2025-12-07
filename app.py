"""
🎙️ 访谈总结器 - Interview Summarizer
将音频、视频、图片转换为结构化访谈记录
"""

import streamlit as st
import os
import tempfile
from src.processor import configure_gemini, analyze_interview, generate_report
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Page Configuration
st.set_page_config(
    page_title="访谈总结器 | Interview Summarizer",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for premium look
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.5rem;
        font-weight: 800;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 10px 20px;
    }
    .result-card {
        background: #f8f9fa;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<h1 class="main-header">🎙️ 访谈总结器</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Interview Summarizer - 将访谈录音转换为结构化记录</p>', unsafe_allow_html=True)

# Sidebar Configuration
with st.sidebar:
    st.header("⚙️ 设置 / Settings")
    
    # API Key
    api_key_env = os.getenv("GEMINI_API_KEY")
    api_key = st.text_input(
        "Gemini API Key", 
        value=api_key_env if api_key_env else "", 
        type="password",
        help="输入您的 Gemini API 密钥 / Enter your Gemini API Key"
    )
    
    if not api_key:
        st.warning("⚠️ 请输入 Gemini API Key")
        st.stop()
    
    try:
        configure_gemini(api_key)
        st.success("✅ API 已配置")
    except Exception as e:
        st.error(f"❌ 配置失败: {e}")
        st.stop()
    
    st.markdown("---")
    
    # Language Selection
    language = st.radio(
        "输出语言 / Output Language",
        options=["zh", "en"],
        format_func=lambda x: "中文" if x == "zh" else "English",
        horizontal=True
    )
    
    st.markdown("---")
    st.info("""
    **支持格式 / Supported Formats:**
    - 🎵 音频: MP3, WAV, M4A
    - 🎬 视频: MP4, MOV, WEBM
    - 🖼️ 图片: JPG, PNG, WEBP
    """)
    
    st.markdown("---")
    st.caption("Powered by **Gemini 1.5 Pro**")

# Main Content
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📤 上传文件 / Upload File")
    
    uploaded_file = st.file_uploader(
        "选择访谈文件",
        type=["mp3", "wav", "m4a", "mp4", "mov", "webm", "jpg", "jpeg", "png", "webp"],
        help="支持音频、视频和图片格式"
    )
    
    if uploaded_file:
        # Preview
        file_type = uploaded_file.type
        if file_type.startswith('audio'):
            st.audio(uploaded_file)
        elif file_type.startswith('video'):
            st.video(uploaded_file)
        elif file_type.startswith('image'):
            st.image(uploaded_file, use_container_width=True)
        
        st.info(f"📁 文件: {uploaded_file.name} ({uploaded_file.size / 1024:.1f} KB)")

with col2:
    st.subheader("🚀 分析 / Analyze")
    
    if uploaded_file:
        if st.button("🎯 开始分析 / Start Analysis", type="primary", use_container_width=True):
            # Save to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_file_path = tmp_file.name
            
            try:
                with st.spinner("⏳ 正在分析... 这可能需要1-2分钟 / Analyzing..."):
                    results = analyze_interview(tmp_file_path, language=language)
                
                st.success("✅ 分析完成! / Analysis Complete!")
                st.session_state['results'] = results
                st.session_state['filename'] = uploaded_file.name.rsplit('.', 1)[0]
                
            except Exception as e:
                st.error(f"❌ 分析失败: {e}")
            finally:
                # Cleanup
                if os.path.exists(tmp_file_path):
                    os.unlink(tmp_file_path)
    else:
        st.info("👆 请先上传文件 / Please upload a file first")

# Results Section
if 'results' in st.session_state:
    st.markdown("---")
    st.header("📊 分析结果 / Results")
    
    results = st.session_state['results']
    filename = st.session_state.get('filename', 'interview')
    
    # Tabs for different outputs
    tab_summary, tab_mindmap, tab_transcript, tab_report = st.tabs([
        "📝 纪要 / Summary", 
        "🗺️ 框图 / Mind Map", 
        "📜 正文 / Transcript",
        "📋 完整报告 / Full Report"
    ])
    
    with tab_summary:
        st.markdown("### 访谈纪要 / Interview Summary")
        st.markdown(results.get("summary", "暂无内容"))
        st.download_button(
            "⬇️ 下载纪要",
            results.get("summary", ""),
            file_name=f"{filename}_summary.md",
            mime="text/markdown"
        )
    
    with tab_mindmap:
        st.markdown("### 信息框图 / Mind Map")
        mermaid_code = results.get("mind_map", "")
        
        # Display Mermaid code
        st.code(mermaid_code, language="mermaid")
        
        st.caption("💡 复制上方代码到 [Mermaid Live Editor](https://mermaid.live) 查看可视化效果")
        
        st.download_button(
            "⬇️ 下载框图",
            mermaid_code,
            file_name=f"{filename}_mindmap.mmd",
            mime="text/plain"
        )
    
    with tab_transcript:
        st.markdown("### 访谈正文 / Transcript")
        st.text_area(
            "全文转录",
            results.get("transcript", ""),
            height=500,
            label_visibility="collapsed"
        )
        st.download_button(
            "⬇️ 下载正文",
            results.get("transcript", ""),
            file_name=f"{filename}_transcript.txt",
            mime="text/plain"
        )
    
    with tab_report:
        st.markdown("### 完整报告 / Full Report")
        report = generate_report(results, filename)
        
        st.markdown(report)
        
        st.download_button(
            "⬇️ 下载完整报告",
            report,
            file_name=f"{filename}_report.md",
            mime="text/markdown",
            type="primary"
        )

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #888;">
    <p>🎙️ 访谈总结器 | Interview Summarizer</p>
    <p>由 <strong>Gemini 1.5 Pro</strong> 驱动 | Powered by <strong>Gemini 1.5 Pro</strong></p>
</div>
""", unsafe_allow_html=True)
