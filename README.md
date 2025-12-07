# 🎙️ 访谈总结器 | Interview Summarizer

将音频、视频、图片转换为结构化访谈记录的工具。

Convert audio, video, and image files into structured interview records.

---

## ✨ Features / 功能

| 输出 / Output | 描述 / Description |
|---------------|---------------------|
| 📝 **访谈纪要** | 执行摘要、关键要点、行动事项 |
| 📜 **访谈正文** | 逐字转录，区分发言人 |
| 🗺️ **信息框图** | Mermaid.js 思维导图 |

**支持格式 / Supported Formats:**
- 🎵 音频: MP3, WAV, M4A
- 🎬 视频: MP4, MOV, WEBM
- 🖼️ 图片: JPG, PNG, WEBP

---

## 🚀 Quick Start / 快速开始

### 1. 安装依赖 / Install Dependencies

```bash
cd interview-summarizer
pip install -r requirements.txt
```

### 2. 配置 API Key / Configure API Key

```bash
# Windows
set GEMINI_API_KEY=your_api_key_here

# Linux/Mac
export GEMINI_API_KEY=your_api_key_here
```

或在应用侧边栏中直接输入 API Key。

### 3. 运行应用 / Run the App

```bash
streamlit run app.py
```

打开浏览器访问 `http://localhost:8501`

---

## 📖 Usage / 使用说明

1. 在侧边栏输入 **Gemini API Key**
2. 选择**输出语言**（中文/English）
3. 上传访谈文件（音频/视频/图片）
4. 点击 **开始分析**
5. 查看并下载分析结果

---

## 🌐 Deploy to Streamlit Cloud

1. Fork this repository
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub account
4. Select this repository and `app.py`
5. Add `GEMINI_API_KEY` in Secrets management

---

## 📁 Project Structure

```
interview-summarizer/
├── app.py                 # Streamlit main app
├── src/
│   ├── __init__.py
│   └── processor.py       # Gemini API processing
├── requirements.txt       # Python dependencies
├── .streamlit/
│   └── config.toml        # Streamlit config
└── README.md
```

---

## ⚠️ Notes / 注意事项

- 使用 **Gemini 1.5 Pro** 模型
- 文件临时上传到 Google 服务器进行处理
- 大文件处理可能需要 1-2 分钟

---

## 📜 License

MIT License

---

*Powered by Google Gemini 1.5 Pro* 🚀
