# Anchor · 评论区神器

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

An AI-powered comment generator for Chinese short-video platforms. Helps content creators craft authentic, high-quality comments to build genuine connections — one comment at a time.

AI 驱动的短视频评论区文案工具。粘贴博主内容，一键生成高质量评论，用于创作者之间的主动建联。**每一句评论，都是一颗抛出去的锚。**

---

## What It Does · 核心功能

**Comment Mode · 评论区模式**（核心）
- Paste a creator's short-video content → generate a comment that gets noticed
- 3 comment intents: Networking (建联), Self-Warming (暖场), Alt-Account (小号助评)
- 6 tone styles: Professional, Resonance, Supplement, Casual, Restrained, Question
- Perfect for building connections with KOLs in your niche

**Post Mode · 主帖模式**
- Generate WeChat Moments (朋友圈) posts
- 4 personas, 4 scenarios, 4 purposes, 4 time-of-day rhythms

---

## Quick Start · 快速开始

```bash
# Install dependencies
pip install -r requirements.txt

# Set your API key
echo "DEEPSEEK_API_KEY=your-key-here" > .env

# Start server
python server.py
```

Open `http://127.0.0.1:5000`.

---

## Tech Stack · 技术栈

| Layer | Choice |
|-------|--------|
| Backend | Flask (Python) |
| AI Model | DeepSeek Chat API |
| Frontend | Vanilla JS + CSS (inline, zero build step) |

---

## How It Works · 工作原理

```
Paste target content → Select intent & style → AI generates comment → Copy & post
粘贴博主内容 → 选择目的和风格 → AI 生成评论 → 复制粘贴到评论区
```

The system prompt assembles rules from multiple dimensions (persona, intent, style, tone) and sends them to DeepSeek to generate contextually appropriate comments in colloquial Chinese.

---

## Privacy · 隐私

Your DeepSeek API key stays in your local `.env` file (gitignored). All content is sent directly from your server to DeepSeek — no third-party data collection.

---

## Project Structure · 项目结构

```
anchor/
├── server.py          # Flask backend, prompt assembly, API proxy
├── templates/
│   └── index.html     # Single-page UI (inline CSS + JS)
├── requirements.txt
├── .gitignore
├── LICENSE
└── README.md
```

---

## Contributing · 参与贡献

Bug reports and feature requests welcome. See [CONTRIBUTING.md](CONTRIBUTING.md).

---

## Disclaimer · 免责声明

This tool generates comment suggestions for reference. Use responsibly — authentic human connection cannot be fully automated.

---

## License · 许可证

[MIT](LICENSE)
