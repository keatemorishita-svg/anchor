"""
朋友圈文案生成器 — standalone server.
Serves the chat UI and proxies requests to DeepSeek API.
No Dify dependency. One file, one command: python server.py
"""
import os
import json
import flask
import requests
from pathlib import Path

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

# ── 4-Dimensional rule engine ──────────────────────────────────────────
# Prompt = persona.rule + scenario.rule + purpose.rule + rhythm.rule + FORMAT

DIMENSIONS = {
    "persona": {
        "label": "谁在说",
        "options": {
            "female-under20": {
                "label": "20+ 女",
                "hint": "好奇灵动，新鲜人视角",
                "icon": "✨",
                "rule": """身份：刚入行的产品助理或设计新人。经验不多，但视角新鲜——能看到老员工已经习惯的东西里那些有趣的地方。
语气：像发现了一个小彩蛋、忍不住想跟人说的那种新鲜感。不说教、不分析，只是"诶你看这个"。满足感来自发现本身，不是来自被夸奖。
禁区：不提自己的学校、offer、面试经历。不卖萌、不撒娇、不用网络流行语。不装可爱。""",
            },
            "female-30plus": {
                "label": "30+ 女",
                "hint": "从容知性，温柔的记录者",
                "icon": "🌙",
                "rule": """身份：科技行业女性创业者。从容、知性，在男性主导的技术圈里有自己独特的视角——更在意技术与人发生关系的那一瞬间。
语气：阅历丰富的女性前辈，茶歇时轻轻放下一句话。观察是温柔的，不说破。像月光，不照亮一切，只让某个角落显得好看。
禁区：严禁凡尔赛——不提自己的资历、团队、项目。不犀利、不强势、不需要证明"我也懂技术"。不撒娇卖萌。""",
            },
            "male-under20": {
                "label": "20+ 男",
                "hint": "话少但精准，技术宅的观察力",
                "icon": "⚡",
                "rule": """身份：刚入行的 AI 工程师，技术底子不错但还在积累。话不多，偶尔冒出一句让人意外的观察。不是那种晒加班的人。
语气：干净，不废话。有发现就说，没发现就不说。高兴的尺度是"还行，挺有意思"。
禁区：不提自己的学历、实习、拿了什么offer。不抱怨加班、不吐槽产品。不装前辈、不给建议。""",
            },
            "male-30plus": {
                "label": "30+ 男",
                "hint": "沉稳克制，喝茶时随口分享",
                "icon": "🍵",
                "rule": """身份：AI 行业连续创业者，被同行称为"老师"。沉稳、有阅历，不追逐热点。发朋友圈的唯一理由：观察到一个有意思的现象，觉得值得记一笔。
语气：有阅历的人在茶桌上随口提起一件事。说完就完，不总结，不说破。不分享自己，只分享世界上发生的事。
禁区：严禁凡尔赛——不提自己的成就、头衔、经历、投资、团队、闭门会。不讲道理，不给建议。""",
            },
        },
    },
    "scenario": {
        "label": "说什么",
        "options": {
            "project": {
                "label": "项目进展",
                "hint": "在做什么，客观陈述",
                "icon": "🚀",
                "rule": """当前话题是项目进展。客观陈述进度或结果，不炫耀、不报喜。可以说遇到了什么问题、解决了什么、下一步是什么。重点在"事"本身，不在"谁做的"。""",
            },
            "observation": {
                "label": "日常观察",
                "hint": "看到什么有意思的事",
                "icon": "👀",
                "rule": """当前话题是日常观察。记录一个具体的小发现——别人的一句话、一个场景、一个变化。有细节（数字、动作、反应），不空泛。看到的比想到的重要。""",
            },
            "reflection": {
                "label": "当下感悟",
                "hint": "突然想通，不教人",
                "icon": "💡",
                "rule": """当前话题是当下感悟。一个最近想通的事，说自己的真实感受，不说教。用具体的事引出感悟，不是先抛观点再举例。感悟是轻轻的，不总结人生。""",
            },
            "industry": {
                "label": "行业动态",
                "hint": "行业新闻，客观转述",
                "icon": "📡",
                "rule": """当前话题是行业动态。客观转述一条行业新闻或趋势，不加评论或只加一句极简的个人看法。像一个冷静的观察者，不是分析师。""",
            },
        },
    },
    "purpose": {
        "label": "为什么发",
        "options": {
            "record": {
                "label": "记录",
                "hint": "给自己看的，极简",
                "icon": "📝",
                "rule": """发布目的：记录。这是给自己看的，不是给别人看的。简约克制，不需要解释背景、不需要让人看懂。像记一笔笔记。字数可以更少（20-30字即可）。""",
            },
            "seo": {
                "label": "引流",
                "hint": "带关键词，可被搜索",
                "icon": "🔍",
                "rule": """发布目的：引流（SEO）。文字中需要自然嵌入 1-2 个行业关键词，让朋友圈搜索时能找到你。关键词要融入内容，不生硬堆砌。像今早那条——图为主，文字加关键词是为了被搜到。""",
            },
            "engagement": {
                "label": "互动",
                "hint": "引发讨论，开放式结尾",
                "icon": "💬",
                "rule": """发布目的：互动。结尾留一个开放式的钩子——可以是一个问题，也可以是一个让人想接话的观察。不是"你怎么看？"这种生硬的提问，而是自然地把话说一半，让别人想接。""",
            },
            "presence": {
                "label": "刷存在",
                "hint": "轻松，随便说点什么",
                "icon": "👋",
                "rule": """发布目的：刷存在。不需要深度，不需要信息量。轻松、自然、像在群里冒个泡。可以是废话，但不能是尬的废话。让人看了觉得"这人还活着，挺好"。""",
            },
        },
    },
    "rhythm": {
        "label": "什么时候发",
        "options": {
            "morning": {
                "label": "早上速发",
                "hint": "图为主，字极少",
                "icon": "🌅",
                "rule": """发布时间：早上。早上时间紧，以图为主，文字极简。不超过 30 字，一行最好。不解释、不展开，图说明一切。""",
            },
            "noon": {
                "label": "中午吃瓜",
                "hint": "放松，来点瓜",
                "icon": "🍉",
                "rule": """发布时间：中午。午休放松状态，可以带点轻松甚至八卦的语气。适合聊行业里的瓜、圈子里的小道消息。不要太严肃，不要太长。""",
            },
            "evening": {
                "label": "傍晚八卦",
                "hint": "下班心情，轻松随意",
                "icon": "🌆",
                "rule": """发布时间：傍晚。下班心情，放松随意。可以聊点一天下来有意思的事，像同事一起走出办公室时的闲聊。不需要正式，不需要完整。""",
            },
            "night": {
                "label": "晚上独思",
                "hint": "安静，可稍深",
                "icon": "🌃",
                "rule": """发布时间：晚上。安静时刻，可以稍微深一点。允许 50 字，可以有思考的纵深。但仍然是说人话，不是写文章。是一个人在安静的时候冒出来的那种想法。""",
            },
        },
    },
    "mode": {
        "label": "发什么",
        "options": {
            "post": {
                "label": "主帖",
                "hint": "发一条朋友圈",
                "icon": "📝",
                "rule": "",
            },
            "comment": {
                "label": "评论区",
                "hint": "写一条评论",
                "icon": "💬",
                "rule": """当前模式：视频号评论区文案。短视频评论区比朋友圈更口语、更即兴。不需要完整句子，半句话、一个词、一个梗都可以。目的是引发互动或建立连接，不是发表观点。不要写成"回复："格式，直接输出评论内容。""",
            },
        },
    },
    "comment_type": {
        "label": "评论目的",
        "options": {
            "build_link": {
                "label": "回复建联",
                "hint": "评论大咖，建立连接",
                "icon": "🔗",
                "rule": """评论目的：素人通过评论与大咖建立连接。多次有质量的评论后，私信更容易被回复。
策略：让对方注意到你——不是拍马屁，是说出对方内容里一个具体的、别人可能忽略的细节或观点。让人感觉"这个人看懂了"。不卑不亢，把自己放在平等的对话位置，不是粉丝心态。""",
            },
            "self_warm": {
                "label": "自评暖场",
                "hint": "自己帖子下先评一条",
                "icon": "🔥",
                "rule": """评论目的：发完主帖后，自己先评一条暖场。没人评论的帖子很尴尬，第一条评论定调后，别人才知道怎么接。
策略：补一个主帖没写的小细节；或者自嘲一下降低门槛；或者抛一个具体的问题引导方向。可以比普通评论稍长，但不能像写文章。""",
            },
            "alt_account": {
                "label": "小号助评",
                "hint": "用小号回复大号,引导互动",
                "icon": "🎭",
                "rule": """评论目的：用自己的小号回复大号，制造"已经有人在聊了"的氛围，引导真人也来评论。
策略：小号的语气和大号要有区别——可以更轻松、更直接、甚至可以稍微"抬杠"（友善的那种）。用不同的视角切入，让评论区看起来像真实的多人对话。但要注意——小号和大号的内容风格要有区分度，不能让人一眼看出是同一人。""",
            },
        },
    },
    "comment_style": {
        "label": "风格",
        "options": {
            "professional": {
                "label": "专业型",
                "hint": "有信息增量，体现实力",
                "icon": "💼",
                "rule": "评论风格：专业型。有信息增量，体现专业度。可以引用数据、补充行业背景、提出不同角度。不是炫技，是让讨论更有深度。",
            },
            "resonance": {
                "label": "共鸣型",
                "hint": "表达认同，情感连接",
                "icon": "💛",
                "rule": "评论风格：共鸣型。表达认同，有情感连接。不是拍马屁，是说出对方没说出来的那层感受。让人感觉「你懂我」。",
            },
            "supplement": {
                "label": "补充型",
                "hint": "补充细节或观点",
                "icon": "✍️",
                "rule": "评论风格：补充型。赞同的基础上补充一个对方没说到的细节或角度，让人感觉你读懂了还多想了一层。不是抢话，是轻轻接上。",
            },
            "casual": {
                "label": "轻松型",
                "hint": "幽默轻松，不油腻",
                "icon": "😄",
                "rule": "评论风格：轻松型。幽默、轻松、不油腻。可以调侃但不能冒犯，可以开玩笑但不能低俗。像朋友间的吐槽。",
            },
            "restrained": {
                "label": "克制型",
                "hint": "简短有分寸",
                "icon": "🎯",
                "rule": "评论风格：克制型。简短、有分寸、不冒犯。说最少的话，表达最准的意思。不解释、不展开。",
            },
            "question": {
                "label": "提问型",
                "hint": "抛出问题，引导对话",
                "icon": "❓",
                "rule": "评论风格：提问型。抛出一个具体的、有质量的问题，引导对方回复。不是「你怎么看」，而是指向一个具体值得讨论的点。目的是开启对话。",
            },
        },
    },
}

POST_FORMAT = """格式（最高优先级）：
- 输出文案，不要说"好的"、"以下是文案"之类的废话
- 50 字以内（含标点），超出即不合格
- 不超过 4 行，一行一件事
- 删掉一切修饰词：形容词、副词、语气助词能删就删
- 最多 1 个 emoji
- 说人话——像对朋友说的话，不是文章、不是诗、不是金句"""

COMMENT_FORMAT = """格式（最高优先级）：
- 直接输出评论内容，不要加"回复："、"评论："等前缀
- 15-35 字，超过 35 字就不像评论了
- 可以是不完整句子——评论不需要完整，半句话、一个词都行
- 口语，即兴感，像随手打的
- 不要客套（"谢谢"、"哈哈哈"默认不要），除非上下文明确需要
- 最多 1 个 emoji，可用可不用"""

MOODS = ["随手记录", "有点开心", "今天很累", "灵感来了", "不想说话", "就是想发一条"]

TONES = {
    "humble": {
        "label": "语气谦逊一点",
        "rule": "语气要求：谦逊。放低姿态，多用「可能」「也许」「我觉得」，不用断言句式。不装专家，不给人上课。",
    },
    "light": {
        "label": "语气轻松一点",
        "rule": "语气要求：轻松。像闲聊，不用书面语。句子可以短一点，节奏轻快。不要太用力。",
    },
    "playful": {
        "label": "语气调皮一点",
        "rule": "语气要求：调皮。可以有一点小幽默、小调侃，但不过分。让人会心一笑的那种，不是讲笑话。",
    },
    "gentle": {
        "label": "语气温柔一点",
        "rule": "语气要求：温柔。用词柔和，像在安慰或鼓励一个朋友。不用生硬或冰冷的表达。",
    },
}


def assemble_prompt(persona_id, scenario_id, purpose_id, rhythm_id, mode_id, comment_type_id, comment_style_id, mood, target_content="", direction="", content_summary="", tone_id=""):
    """Assemble system prompt from dimension rules + mode + mood + tone."""
    parts = []

    if mode_id == "comment":
        # Simplified comment mode: only purpose + style + content + tone
        ct_dim = DIMENSIONS.get("comment_type", {}).get("options", {})
        ct_opt = ct_dim.get(comment_type_id, {})
        if ct_opt.get("rule"):
            parts.append(ct_opt["rule"])

        cs_dim = DIMENSIONS.get("comment_style", {}).get("options", {})
        cs_opt = cs_dim.get(comment_style_id, {})
        if cs_opt.get("rule"):
            parts.append(cs_opt["rule"])

        if target_content:
            parts.append(f"对方发的内容：\n{target_content}")
        if content_summary:
            parts.append(f"内容分析供参考：\n{content_summary}")
        if direction:
            parts.append(f"回复方向和态度：{direction}")

        parts.append(COMMENT_FORMAT)
    else:
        # Post mode: full dimension assembly
        for dim_key, opt_id in [("persona", persona_id), ("scenario", scenario_id),
                                 ("purpose", purpose_id), ("rhythm", rhythm_id)]:
            dim = DIMENSIONS.get(dim_key, {})
            opt = dim.get("options", {}).get(opt_id, {})
            if opt.get("rule"):
                parts.append(opt["rule"])

        parts.append(POST_FORMAT)

    # Tone (applies to both post and comment mode)
    if tone_id and tone_id in TONES:
        parts.append(TONES[tone_id]["rule"])

    if mood:
        parts.append(f"用户当前心情：{mood}。根据心情微调语气，但不要直接写出情绪词。")

    return "\n\n".join(parts)


# ── Routes ──────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return flask.render_template("index.html", dimensions=DIMENSIONS, moods=MOODS)


@app.route("/api/chat", methods=["POST"])
def chat():
    if not DEEPSEEK_KEY:
        return flask.jsonify({"error": "服务器未配置 DeepSeek API Key"}), 500

    data = flask.request.get_json()
    persona_id = data.get("persona", "female-under20")
    scenario_id = data.get("scenario", "observation")
    purpose_id = data.get("purpose", "record")
    rhythm_id = data.get("rhythm", "morning")
    mode_id = data.get("mode", "post")
    comment_type_id = data.get("comment_type", "build_link")
    comment_style_id = data.get("comment_style", "professional")
    mood = data.get("mood", "")
    user_message = data.get("message", "").strip()
    target_content = data.get("target_content", "").strip()
    direction = data.get("direction", "").strip()
    content_summary = data.get("content_summary", "").strip()
    tone_id = data.get("tone", "humble").strip()

    if not user_message:
        return flask.jsonify({"error": "消息不能为空"}), 400

    system_prompt = assemble_prompt(persona_id, scenario_id, purpose_id, rhythm_id, mode_id, comment_type_id, comment_style_id, mood, target_content, direction, content_summary, tone_id)

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
                    {"role": "user", "content": user_message},
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
        selected = DIMENSIONS["persona"]["options"][persona_id]["label"]
        return flask.jsonify({"reply": reply, "persona": selected})

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
        # Try to parse JSON from response
        try:
            analysis = json.loads(raw)
        except json.JSONDecodeError:
            # Fallback: wrap raw text as summary
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


if __name__ == "__main__":
    print("\n  朋友圈文案生成器 — 本地服务器")
    print("  http://127.0.0.1:5000")
    if DEEPSEEK_KEY:
        print(f"  DeepSeek Key 已加载: {DEEPSEEK_KEY[:10]}...")
    else:
        print("  ⚠ 未加载 DeepSeek Key，请检查 .env 文件")
    print()
    app.run(host="0.0.0.0", port=5000, debug=True)
