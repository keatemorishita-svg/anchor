# Anchor · 评论区神器

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

An AI-powered comment generator for Chinese short-video platforms. Paste a creator's content, get a comment that builds genuine connection.

AI 驱动的短视频评论区建联工具。粘贴博主内容，一键生成高质量评论。**每一句评论，都是一颗抛出去的锚。**

---

## What It Does · 核心功能

- Paste content → generate a comment that gets noticed
- 3 intents: 建联 (Networking) / 暖场 (Self-Warming) / 小号 (Alt-Account)
- 6 styles: 共鸣 / 补充 / 提问 / 轻松 / 专业 / 克制
- 4 tones: 谦逊 / 轻松 / 调皮 / 温柔
- One flow, zero distractions

---

## Quick Start · 快速开始

```bash
pip install -r requirements.txt
echo "DEEPSEEK_API_KEY=your-key-here" > .env
python server.py
```

Open `http://127.0.0.1:5001`.

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
