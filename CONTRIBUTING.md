# Contributing to Comment Connect

## Ways to Contribute

- **Report bugs** — open an Issue describing the problem and steps to reproduce
- **Suggest features** — open an Issue describing your idea
- **Improve prompts** — the quality of generated comments depends heavily on prompt engineering
- **Add model support** — currently DeepSeek only; contributions for OpenAI / Claude API support welcome

## Development Setup

```bash
git clone https://github.com/keatemorishita-svg/comment-connect.git
cd comment-connect
pip install -r requirements.txt
echo "DEEPSEEK_API_KEY=your-key" > .env
python server.py
```

Open `http://127.0.0.1:5000`.

## Code Conventions

- Python: keep it simple, single-file server
- Frontend: vanilla JS, inline CSS — no build step, no framework
- Comments may be in Chinese or English

## Pull Request Process

1. Fork and create a feature branch
2. Test by running `python server.py` and verifying the UI
3. Open a PR with a clear description

---

# 参与贡献（中文）

欢迎提交 Bug 报告、功能建议或 PR。

开发环境：
```bash
pip install -r requirements.txt
echo "DEEPSEEK_API_KEY=你的key" > .env
python server.py
```
