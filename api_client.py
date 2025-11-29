import requests
import json
import base64
from concurrent.futures import ThreadPoolExecutor

API_KEY = "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"
API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "google/gemini-2.5-flash"

# 95种情绪清单 (基于飞书文档整理)
EMOTION_LIST = """
1. 快乐类: 狂喜, 兴奋, 惊喜, 愉悦, 畅爽, 知足, 平静, 放松, 舒适, 逗趣, 治愈
2. 激励类: 成就感, 骄傲, 自信, 激励感, 振奋, 勇敢, 期待感, 希望, 憧憬
3. 欣赏类: 欣赏感, 钦佩感, 惊艳, 认同感, 赞同, 共情, 好奇, 探秘感
4. 松弛类: 松弛感, 自在, 慵懒, 随意, 淡定, 幽默
5. 安全类: 安全感, 信赖感, 踏实, 确定感, 归属感, 被保护, 熟悉
6. 爱与亲密类: 爱, 喜欢, 依恋, 亲密, 温暖, 陪伴, 甜蜜, 宠溺
7. 优越类: 优越感, 高级感, 尊贵, 独特, 领先, 奢华
8. 负面-失望类: 失望, 后悔, 无语, 心累, 疲惫, 困惑, 迷茫, 遗憾
9. 负面-愤怒类: 愤怒, 气愤, 吐槽, 抓狂, 烦躁, 不满, 抗议
10. 负面-轻蔑类: 轻蔑, 不屑, 鄙视, 嘲讽, 嫌弃
11. 负面-恐惧类: 恐惧, 害怕, 焦虑, 担忧, 惊慌
12. 负面-悲伤类: 悲伤, 难过, 委屈, 心碎, 孤独
13. 复杂情绪: 怀旧, 纠结, 矛盾, 尴尬, 社死, 真香, 意难平, 破防, 上头, 下头
"""

# 爆款标题八大词类定义
TITLE_KEYWORD_CATEGORIES = """
1. 痛点词: 直击用户问题，引发共鸣 (如: 近视、失眠、显胖)
2. 效果词: 承诺使用后的美好结果 (如: 显瘦、不卡粉、秒懂)
3. 承诺词: 提供保障，消除顾虑 (如: 医生推荐、包退、亲测)
4. 情绪词: 激发强烈情感 (如: 绝了、后悔、哭了、炸裂)
5. 语气词: 增加真实感 (如: 真的、居然、果然、说实话)
6. 人群词: 精准定位 (如: 宝妈、学生党、梨形身材)
7. 时效词: 制造紧迫感 (如: 2025、限时、今天)
8. 产品词: 明确品类 (如: 护眼灯、荞麦枕)
"""

# 爆款标题公式库
TITLE_FORMULAS = """
公式1: 人群词 + 痛点词 + 效果词/解决方案 (例: 程序员必看！颈椎痛有救了，一觉睡到天亮的秘密)
公式2: 情绪词 + 效果词 + 语气词 (例: 绝了！居然真的不卡粉，说实话后悔没早买)
公式3: 痛点场景 + 承诺词 + 产品词 (例: 孩子总揉眼？眼科医生推荐的护眼灯，亲测有效)
公式4: 数字/时效 + 强效果 + 悬念 (例: 坚持3天！法令纹消失术，2025年最强逆袭)
"""

def encode_image(image_file):
    """Encodes a file-like object (image) to base64 string."""
    return base64.b64encode(image_file.getvalue()).decode('utf-8')

def analyze_product(image_file, product_name, product_price):
    """Phase 1: Analyze Product Image + Basic Info."""
    base64_image = encode_image(image_file)
    
    prompt = f"""
    请仔细分析这张商品图片，结合提供的基础信息，提取关键信息：
    
    [基础信息]
    - 产品名称: {product_name}
    - 产品价格: {product_price}
    
    [分析要求]
    1. 精确的产品名称与细分品类（注意区分易混淆品类）。
    2. 核心功能/成分（3-5个主要功能）。
    3. 视觉风格。
    4. 适用人群（具体的年龄段、身份）。
    5. 核心卖点（差异化优势）。
    
    请以JSON格式输出，Keys为: name, category, features, visual_style, target_audience, selling_points.
    """
    
    return call_gemini([{"type": "text", "text": prompt}, {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}])

def analyze_text_data(titles_text, keywords_text):
    """Phase 1: Analyze Text Data (Titles & Keywords)."""
    prompt = f"""
    请分析以下两组文本数据：
    
    [数据1：100个爆款标题]
    {titles_text[:10000]}
    
    [数据2：搜索词数据]
    {keywords_text[:5000]}
    
    [分析任务]
    1. **建立爆款标题词库**: 请从上述数据中提取高频词，并严格按照以下八大类进行归类（每类至少提取5-10个词）：
       - 痛点词, 效果词, 承诺词, 情绪词, 语气词, 人群词, 时效词, 产品词
    2. **搜索意图分析**: 判断主要搜索意图（信息类/交易类）。
    3. **核心痛点提取**: 找出用户最关心的问题。
    
    请以JSON格式输出，Keys为: 
    title_keyword_library (包含8个子key: pain_points, effects, promises, emotions, tones, audiences, timings, products),
    search_intent, 
    core_pain_points.
    """
    return call_gemini([{"type": "text", "text": prompt}])

def analyze_reviews(image_files):
    """Phase 1: Analyze Review Screenshots."""
    if not image_files:
        return json.dumps({"error": "No review images provided", "review_pain_points": "无评论数据"})

    content = [{"type": "text", "text": """
    提取评论区关键信息：
    1. 用户痛点/槽点
    2. 用户夸赞点
    3. 真实使用场景
    请以JSON格式输出，Keys为: review_pain_points, review_praises, usage_scenarios.
    """}]
    
    for img in image_files:
        b64 = encode_image(img)
        content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}})
        
    return call_gemini(content)

def analyze_posts(image_files):
    """Phase 1: Analyze Viral Post Content."""
    content = [{"type": "text", "text": """
    拆解爆款笔记：
    1. 内容结构 (行文逻辑)
    2. 语气风格
    3. 转化设计
    4. 字数与排版
    请以JSON格式输出，Keys为: body_structure, tone_style, conversion_tactics, format_specs.
    """}]
    
    for img in image_files:
        b64 = encode_image(img)
        content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}})
        
    return call_gemini(content)

def generate_strategy_report(product_data, text_data, review_data, post_data):
    """Phase 2: Generate Comprehensive Strategy Report."""
    
    prompt = f"""
    # Role
    你是一个小红书爆款策略专家。

    # Context
    [产品数据] {product_data}
    [文本数据] {text_data}
    [评论数据] {review_data}
    [竞品数据] {post_data}
    [情绪库] {EMOTION_LIST}

    # Task
    生成一份深度策略报告：
    1. **目标人群画像**: 具体到年龄、身份、痛点。
    2. **核心痛点**: 最紧迫需要解决的问题。
    3. **差异化卖点**: 为什么选这个产品。
    4. **情绪策略**: 选定2-3种核心情绪。
    5. **深层需求**: 精神层面满足。
    6. **使用场景**: 具体画面。
    7. **词库构建**: 基于[文本数据]的分析，输出针对该产品的【八大类爆款词库】（痛点/效果/承诺/情绪/语气/人群/时效/产品）。

    # Output Format
    JSON: {{
        "target_audience": "...",
        "core_pain_point": "...",
        "core_selling_point": "...",
        "emotion_strategy": "...",
        "deep_need": "...",
        "usage_scenario": "...",
        "keyword_library": {{
            "pain_points": ["...", "..."],
            "effects": ["...", "..."],
            "promises": ["...", "..."],
            "emotions": ["...", "..."],
            "tones": ["...", "..."],
            "audiences": ["...", "..."],
            "timings": ["...", "..."],
            "products": ["...", "..."]
        }}
    }}
    """
    return call_gemini([{"type": "text", "text": prompt}])

def generate_title_titles(strategy_report):
    """Phase 3: Generate Viral Titles AND the Prompt used to create them."""
    
    prompt = f"""
    # Role
    你是一位资深小红书标题优化师，擅长结合关键词库和爆款公式创作高点击率标题。

    # Context
    [策略报告] {strategy_report}
    [内置公式库] {TITLE_FORMULAS}
    
    # Task 1: 智能选择与填充
    1. 从策略报告中提取产品信息（名称、卖点、人群、痛点）。
    2. 提取策略报告中的【八大类词库】具体词汇。
    3. 选择最适合该产品的1-2个爆款公式。

    # Task 2: 编写标题生成提示词 (Title Prompt)
    请严格按照以下模板，将 Task 1 提取的内容填充进去，生成一个完整的 Prompt：

    [Prompt模板]
    #角色
    你是一位资深小红书标题优化师，擅长结合关键词库和爆款公式创作高点击率标题。

    #任务
    基于我提供的“产品信息”和“标题词库”，使用指定的“爆款公式”生成10个标题。

    #产品信息
    - **产品名称**：[从策略报告提取]
    - **核心卖点**：[从策略报告提取]
    - **目标人群**：[从策略报告提取]
    - **要解决的痛点**：[从策略报告提取]

    #标题词库（请按类别填充你收集好的词）
    - **痛点词**：[从策略报告提取]
    - **效果词**：[从策略报告提取]
    - **人群词**：[从策略报告提取]
    - **情绪词**：[从策略报告提取]
    - ...（其他你有的词类）

    #爆款公式（请选择1-2个）
    [填入选定的1-2个具体公式内容，例如：]
    - **公式1（人群痛点型）**：`[人群词]必看！[痛点词]有救了，[效果词]的秘密！`
    - **公式2（数字揭秘型）**：`[数字]个[时效词][效果词]的[产品词]，第[数字]个绝了！`

    #生成要求
    1.  每个标题必须至少包含3类不同的关键词。字数控制在20字以内
    2.  优先使用我提供的词库中的词汇。
    3.  标题要口语化，有冲击力，避免生硬广告感。
    4.  输出格式：直接列出标题，每个标题一行。 最后需要确认标题符合以下几个要求：是否一眼看懂？（5秒内懂）
    是否圈定了精准人群？（让对的人点进来）
    是否激发了好奇或共鸣？（有点击冲动）
    是否包含了搜索关键词？（能被搜到）

    # Task 3: 执行生成
    使用你编写的 [Title Prompt] 生成 10 个爆款标题。

    # Output Format
    JSON: {{
        "title_prompt": "...",
        "generated_titles": [
            {{"title": "...", "reason": "..."}},
            ... (10个)
        ],
        "selected_formulas": ["公式名称..."]
    }}
    """
    return call_gemini([{"type": "text", "text": prompt}])

def generate_copy(strategy_report, selected_title):
    """Phase 4: Generate Body Prompt AND Final Copy."""
    
    prompt = f"""
    # Role
    你是一个小红书爆款文案专家。

    # Context
    [策略报告] {strategy_report}
    [选定标题] {selected_title}
    
    # Task 1: 编写正文提示词 (Body Prompt)
    请严格按照以下结构，基于策略报告编写一个**生成正文的指令**（Prompt）：
    
    [Prompt模板]
    【角色定位】作为[行业]领域的爆款文案专家
    【用户画像】针对[分析得出的用户特征]人群
    【核心痛点】解决[分析出的核心痛点]问题
    【情绪基调】采用[情绪词1]+[情绪词2]组合
    【内容风格】[分析出的风格偏好]+[卖点突出方式]
    【深层需求】满足用户[精神层面的需求]
    【结构要求】包含价值主张+案例佐证+行动召唤
    【字数限制】300字左右
    【避坑指南】避免[竞品常见问题]

    # Task 2: 撰写文案 (Sample Copy)
    执行你刚才编写的 [Body Prompt]，为 [选定标题] 撰写一篇爆款笔记正文。

    # Output Format
    JSON: {{
        "body_prompt": "...", 
        "content": "...",
        "tags": "#..."
    }}
    """
    return call_gemini([{"type": "text", "text": prompt}])

def call_gemini(content):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://cursor.sh", 
        "X-Title": "XHS-CopyCat"
    }
    
    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "user",
                "content": content
            }
        ],
        "response_format": {"type": "json_object"}
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        
        if 'choices' in result and len(result['choices']) > 0:
            content_str = result['choices'][0]['message']['content']
            if content_str.startswith("```json"):
                content_str = content_str.replace("```json", "").replace("```", "")
            elif content_str.startswith("```"):
                content_str = content_str.replace("```", "")
            return content_str
        else:
            return json.dumps({"error": "No response from API"})
            
    except Exception as e:
        return json.dumps({"error": str(e)})
