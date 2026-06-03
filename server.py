"""
Anchor — AI-powered comment generator for creator networking.
Serves the comment UI and proxies requests to DeepSeek API.
One file, one command: python server.py
"""
import os
import re
import json
import flask
import requests
from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urlparse

app = flask.Flask(__name__, template_folder="templates")

# Load .env file
_ENV_PATH = Path(__file__).parent / ".env"
if _ENV_PATH.exists():
    with open(_ENV_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

DEEPSEEK_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"

# ── Comment-only dimensions ───────────────────────────────────────────

DIMENSIONS = {
    "comment_type": {
        "label": "目的",
        "options": {
            "build_link": {
                "label": "建联",
                "hint": "评论大咖，建立连接",
                "icon": "🔗",
                "rule": """评论目的：素人通过评论与大咖建立连接。多次有质量的评论后，私信更容易被回复。
策略：让对方注意到你——不是拍马屁，是说出对方内容里一个具体的、别人可能忽略的细节或观点。让人感觉"这个人看懂了"。不卑不亢，把自己放在平等的对话位置，不是粉丝心态。""",
            },
            "self_warm": {
                "label": "暖场",
                "hint": "自己帖子下先评一条",
                "icon": "🔥",
                "rule": """评论目的：发完主帖后，自己先评一条暖场。没人评论的帖子很尴尬，第一条评论定调后，别人才知道怎么接。
策略：补一个主帖没写的小细节；或者自嘲一下降低门槛；或者抛一个具体的问题引导方向。可以比普通评论稍长，但不能像写文章。""",
            },
            "alt_account": {
                "label": "小号",
                "hint": "用小号回复大号，引导互动",
                "icon": "🎭",
                "rule": """评论目的：用自己的小号回复大号，制造"已经有人在聊了"的氛围，引导真人也来评论。
策略：小号的语气和大号要有区别——可以更轻松、更直接、甚至可以稍微"抬杠"（友善的那种）。用不同的视角切入，让评论区看起来像真实的多人对话。但要注意——小号和大号的内容风格要有区分度，不能让人一眼看出是同一人。""",
            },
        },
    },
    "comment_style": {
        "label": "风格",
        "options": {
            "resonance": {
                "label": "共鸣",
                "hint": "表达认同，情感连接",
                "icon": "💛",
                "rule": "评论风格：共鸣型。表达认同，有情感连接。不是拍马屁，是说出对方没说出来的那层感受。让人感觉「你懂我」。",
            },
            "supplement": {
                "label": "补充",
                "hint": "补充细节或观点",
                "icon": "✍️",
                "rule": "评论风格：补充型。赞同的基础上补充一个对方没说到的细节或角度，让人感觉你读懂了还多想了一层。不是抢话，是轻轻接上。",
            },
            "question": {
                "label": "提问",
                "hint": "抛出问题，引导对话",
                "icon": "❓",
                "rule": "评论风格：提问型。抛出一个具体的、有质量的问题，引导对方回复。不是「你怎么看」，而是指向一个具体值得讨论的点。目的是开启对话。",
            },
            "casual": {
                "label": "轻松",
                "hint": "幽默轻松，不油腻",
                "icon": "😄",
                "rule": "评论风格：轻松型。幽默、轻松、不油腻。可以调侃但不能冒犯，可以开玩笑但不能低俗。像朋友间的吐槽。",
            },
            "professional": {
                "label": "专业",
                "hint": "有信息增量，体现实力",
                "icon": "💼",
                "rule": "评论风格：专业型。有信息增量，体现专业度。可以引用数据、补充行业背景、提出不同角度。不是炫技，是让讨论更有深度。",
            },
            "restrained": {
                "label": "克制",
                "hint": "简短有分寸",
                "icon": "🎯",
                "rule": "评论风格：克制型。简短、有分寸、不冒犯。说最少的话，表达最准的意思。不解释、不展开。",
            },
        },
    },
}

COMMENT_FORMAT = """格式（最高优先级）：
- 直接输出评论内容，不要加"回复："、"评论："等前缀
- 15-35 字，超过 35 字就不像评论了
- 可以是不完整句子——评论不需要完整，半句话、一个词都行
- 口语，即兴感，像随手打的
- 不要客套（"谢谢"、"哈哈哈"默认不要），除非上下文明确需要
- 最多 1 个 emoji，可用可不用"""

TONES = {
    "humble": {
        "label": "谦逊",
        "rule": "语气要求：谦逊。放低姿态，多用「可能」「也许」「我觉得」，不用断言句式。不装专家，不给人上课。",
    },
    "light": {
        "label": "轻松",
        "rule": "语气要求：轻松。像闲聊，不用书面语。句子可以短一点，节奏轻快。不要太用力。",
    },
    "playful": {
        "label": "调皮",
        "rule": "语气要求：调皮。可以有一点小幽默、小调侃，但不过分。让人会心一笑的那种，不是讲笑话。",
    },
    "gentle": {
        "label": "温柔",
        "rule": "语气要求：温柔。用词柔和，像在安慰或鼓励一个朋友。不用生硬或冰冷的表达。",
    },
}


def assemble_prompt(comment_type_id, comment_style_id, tone_id, target_content, direction="", content_summary=""):
    """Assemble system prompt from comment dimensions + tone."""
    parts = []

    ct_opt = DIMENSIONS["comment_type"]["options"].get(comment_type_id, {})
    if ct_opt.get("rule"):
        parts.append(ct_opt["rule"])

    cs_opt = DIMENSIONS["comment_style"]["options"].get(comment_style_id, {})
    if cs_opt.get("rule"):
        parts.append(cs_opt["rule"])

    if target_content:
        parts.append(f"对方发的内容：\n{target_content}")
    if content_summary:
        parts.append(f"内容分析供参考：\n{content_summary}")
    if direction:
        parts.append(f"回复方向和态度：{direction}")

    parts.append(COMMENT_FORMAT)

    if tone_id and tone_id in TONES:
        parts.append(TONES[tone_id]["rule"])

    return "\n\n".join(parts)


# ── Routes ────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return flask.render_template("index.html", dimensions=DIMENSIONS, tones=TONES)


@app.route("/api/chat", methods=["POST"])
def chat():
    if not DEEPSEEK_KEY:
        return flask.jsonify({"error": "服务器未配置 DeepSeek API Key"}), 500

    data = flask.request.get_json()
    comment_type_id = data.get("comment_type", "build_link")
    comment_style_id = data.get("comment_style", "resonance")
    tone_id = data.get("tone", "humble")
    target_content = data.get("target_content", "").strip()
    direction = data.get("direction", "").strip()
    content_summary = data.get("content_summary", "").strip()

    if not target_content:
        return flask.jsonify({"error": "请粘贴博主内容"}), 400

    system_prompt = assemble_prompt(
        comment_type_id, comment_style_id, tone_id,
        target_content, direction, content_summary
    )

    try:
        resp = requests.post(
            DEEPSEEK_URL,
            headers={
                "Authorization": f"Bearer {DEEPSEEK_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": "请根据以上内容生成一条评论"},
                ],
                "temperature": 0.85,
                "max_tokens": 200,
            },
            timeout=30,
            proxies={"http": None, "https": None},
        )
        resp.raise_for_status()
        body = resp.json()
        reply = body["choices"][0]["message"]["content"]
        return flask.jsonify({"reply": reply})

    except requests.exceptions.Timeout:
        return flask.jsonify({"error": "DeepSeek API 超时，请重试"}), 504
    except requests.exceptions.RequestException as e:
        return flask.jsonify({"error": f"API 请求失败: {str(e)}"}), 502


@app.route("/api/analyze", methods=["POST"])
def analyze():
    """Extract structured summary from target content."""
    if not DEEPSEEK_KEY:
        return flask.jsonify({"error": "服务器未配置 DeepSeek API Key"}), 500

    data = flask.request.get_json()
    target_content = data.get("target_content", "").strip()
    if not target_content:
        return flask.jsonify({"error": "内容不能为空"}), 400

    analyze_prompt = """分析以下内容，提取关键信息。严格按JSON格式返回，不要加任何其他文字：

{
  "topic": "内容主题（10字以内）",
  "viewpoint": "作者核心观点（20字以内）",
  "emotion": "情绪基调（理性/兴奋/克制/幽默/焦虑/愤怒 中选一个）",
  "key_points": ["关键信息1", "关键信息2", "关键信息3"],
  "summary": "30-60字简短摘要"
}"""

    try:
        resp = requests.post(
            DEEPSEEK_URL,
            headers={
                "Authorization": f"Bearer {DEEPSEEK_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": analyze_prompt},
                    {"role": "user", "content": target_content},
                ],
                "temperature": 0.3,
                "max_tokens": 400,
            },
            timeout=30,
            proxies={"http": None, "https": None},
        )
        resp.raise_for_status()
        body = resp.json()
        raw = body["choices"][0]["message"]["content"]
        try:
            analysis = json.loads(raw)
        except json.JSONDecodeError:
            analysis = {
                "topic": "",
                "viewpoint": "",
                "emotion": "",
                "key_points": [],
                "summary": raw,
            }
        return flask.jsonify({"analysis": analysis})

    except requests.exceptions.Timeout:
        return flask.jsonify({"error": "DeepSeek API 超时，请重试"}), 504
    except requests.exceptions.RequestException as e:
        return flask.jsonify({"error": f"API 请求失败: {str(e)}"}), 502


# ── URL Fetch ─────────────────────────────────────────────────────────

URL_PATTERN = re.compile(r'https?://\S+', re.IGNORECASE)


def detect_url_type(url):
    domain = urlparse(url).netloc.lower()
    if 'bilibili.com' in domain:
        return 'bilibili'
    if 'youtube.com' in domain or 'youtu.be' in domain:
        return 'youtube'
    return 'article'


def fetch_article(url):
    """Fetch and extract text from a blog/article URL."""
    resp = requests.get(url, timeout=15, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }, proxies={"http": None, "https": None})
    resp.raise_for_status()
    resp.encoding = resp.apparent_encoding or 'utf-8'

    soup = BeautifulSoup(resp.text, 'lxml')
    # Remove noise
    for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
        tag.decompose()

    title = soup.title.string.strip() if soup.title else ''
    # Try to find main content
    body = soup.find('article') or soup.find(class_=re.compile('content|article|post|entry')) or soup.body
    text = body.get_text(separator='\n', strip=True) if body else soup.get_text(separator='\n', strip=True)

    # Clean up: remove excessive blank lines, limit length
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    text = '\n'.join(lines)
    if len(text) > 8000:
        text = text[:8000] + '\n...(内容已截断)'

    return {'type': 'article', 'title': title, 'content': text, 'source': url}


def fetch_bilibili(url):
    """Fetch B站 video title, description, and subtitles."""
    # Extract bvid from URL
    m = re.search(r'/video/(BV[\w]+)', url)
    if not m:
        return {'error': '无法识别 B站视频链接'}
    bvid = m.group(1)

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://www.bilibili.com/',
    }
    proxies = {"http": None, "https": None}

    # Get video info
    info_resp = requests.get(
        f'https://api.bilibili.com/x/web-interface/view?bvid={bvid}',
        headers=headers, timeout=15, proxies=proxies
    )
    info = info_resp.json().get('data', {})

    title = info.get('title', '')
    desc = info.get('desc', '')
    cid = info.get('cid', 0)

    parts = []
    if title:
        parts.append(f"标题：{title}")
    if desc:
        parts.append(f"简介：{desc}")

    # Try to get subtitles
    if cid:
        try:
            sub_resp = requests.get(
                f'https://api.bilibili.com/x/player/v2?bvid={bvid}&cid={cid}',
                headers=headers, timeout=10, proxies=proxies
            )
            sub_data = sub_resp.json().get('data', {})
            subtitle = sub_data.get('subtitle', {}).get('subtitles', [])
            if subtitle:
                sub_url = subtitle[0].get('subtitle_url', '')
                if sub_url and sub_url.startswith('//'):
                    sub_url = 'https:' + sub_url
                if sub_url:
                    sub_resp = requests.get(sub_url, headers=headers, timeout=10, proxies=proxies)
                    sub_json = sub_resp.json()
                    sub_lines = [item.get('content', '') for item in sub_json.get('body', [])]
                    sub_text = '\n'.join(sub_lines)
                    if len(sub_text) > 6000:
                        sub_text = sub_text[:6000] + '\n...(字幕已截断)'
                    parts.append(f"字幕：\n{sub_text}")
        except Exception:
            pass

    content = '\n\n'.join(parts)
    if not content.strip():
        # Fallback: fetch page and extract text
        try:
            page_resp = requests.get(url, headers=headers, timeout=15, proxies=proxies)
            soup = BeautifulSoup(page_resp.text, 'lxml')
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc:
                content = f"标题：{title}\n描述：{meta_desc.get('content', '')}"
        except Exception:
            content = f"标题：{title}"

    has_subtitle = any('字幕' in p for p in parts)
    return {'type': 'bilibili', 'title': title, 'content': content, 'source': url, 'has_subtitle': has_subtitle}


def fetch_youtube(url):
    """Fetch YouTube video title, description, and captions."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    proxies = {"http": None, "https": None}

    parts = []

    # Get page info
    try:
        resp = requests.get(url, headers=headers, timeout=15, proxies=proxies)
        soup = BeautifulSoup(resp.text, 'lxml')

        title_tag = soup.find('title')
        title = title_tag.string.strip().replace(' - YouTube', '') if title_tag else ''
        if title:
            parts.append(f"标题：{title}")

        # Extract description from meta
        desc_tag = soup.find('meta', attrs={'name': 'description'})
        if desc_tag:
            desc = desc_tag.get('content', '')
            if desc:
                parts.append(f"简介：{desc}")
    except Exception:
        pass

    # Get captions via youtube-transcript-api
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        video_id = None
        if 'v=' in url:
            video_id = url.split('v=')[1].split('&')[0]
        elif 'youtu.be/' in url:
            video_id = url.split('youtu.be/')[1].split('?')[0]

        if video_id:
            transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['zh-Hans', 'zh', 'en'])
            lines = [item.get('text', '') for item in transcript]
            sub_text = '\n'.join(lines)
            if len(sub_text) > 6000:
                sub_text = sub_text[:6000] + '\n...(字幕已截断)'
            parts.append(f"字幕：\n{sub_text}")
    except Exception:
        pass

    content = '\n\n'.join(parts)
    if not content.strip():
        return {'error': '无法获取 YouTube 视频内容'}

    has_subtitle = any('字幕' in p for p in parts)
    return {'type': 'youtube', 'title': title if 'title' in dir() else '', 'content': content, 'source': url, 'has_subtitle': has_subtitle}


@app.route("/api/fetch", methods=["POST"])
def fetch_url():
    """Fetch content from a URL — article, B站 video, or YouTube video."""
    data = flask.request.get_json()
    url = data.get("url", "").strip()
    if not url:
        return flask.jsonify({"error": "请提供链接"}), 400

    try:
        url_type = detect_url_type(url)
        if url_type == 'bilibili':
            result = fetch_bilibili(url)
        elif url_type == 'youtube':
            result = fetch_youtube(url)
        else:
            result = fetch_article(url)

        if 'error' in result:
            return flask.jsonify({"error": result['error']}), 400

        return flask.jsonify({
            "type": result['type'],
            "title": result.get('title', ''),
            "content": result['content'],
            "source": result['source'],
        })

    except requests.exceptions.Timeout:
        return flask.jsonify({"error": "抓取超时，请直接粘贴正文"}), 504
    except Exception as e:
        return flask.jsonify({"error": f"抓取失败: {str(e)}"}), 502


if __name__ == "__main__":
    print("\n  Anchor — 评论区建联工具")
    print("  http://127.0.0.1:5001")
    if DEEPSEEK_KEY:
        print(f"  DeepSeek Key 已加载: {DEEPSEEK_KEY[:10]}...")
    else:
        print("  ⚠ 未加载 DeepSeek Key，请检查 .env 文件")
    print()
    app.run(host="0.0.0.0", port=5001, debug=True)
