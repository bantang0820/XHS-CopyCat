import streamlit as st
from PIL import Image
import io
import json
import concurrent.futures
from api_client import (
    analyze_product, analyze_text_data, analyze_reviews, analyze_posts,
    generate_strategy_report, generate_title_titles, generate_copy
)

# 设置页面配置
st.set_page_config(
    page_title="XHS-CopyCat | 小红书爆款文案工作台",
    page_icon="🐱",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 自定义CSS
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stButton>button {
        width: 100%;
        background-color: #FF2442;
        color: white;
        border: none;
        height: 3rem;
        font-size: 1.2rem;
        border-radius: 8px;
    }
    .stButton>button:hover {
        background-color: #E01030;
        color: white;
    }
    h1, h2, h3 {
        color: #333;
        font-family: 'PingFang SC', sans-serif;
    }
    .section-header {
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 1rem;
        color: #111;
        display: flex;
        align-items: center;
    }
    /* 高亮输入框: 文本输入 */
    .stTextInput input {
        border: 2px solid #FF2442 !important;
        background-color: #FFF0F5 !important;
    }
    /* 高亮输入框: 文本区域 */
    .stTextArea textarea {
        border: 2px solid #FF2442 !important;
        background-color: #FFF0F5 !important;
    }
    /* 汉化上传按钮 (CSS Hack) */
    [data-testid="stFileUploader"] button {
        position: relative;
        color: transparent !important;
        border: 1px solid #FF2442 !important;
    }
    [data-testid="stFileUploader"] button::after {
        content: "选择图片";
        position: absolute;
        left: 0;
        right: 0;
        top: 0;
        bottom: 0;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #FF2442 !important;
        font-weight: bold;
    }
    [data-testid="stFileUploader"] section {
        border: 2px dashed #FF2442 !important;
        background-color: #FFF0F5 !important;
    }
    
    .keyword-tag {
        display: inline-block;
        padding: 4px 8px;
        margin: 2px;
        background-color: #ffebee;
        color: #c62828;
        border-radius: 12px;
        font-size: 0.85rem;
        border: 1px solid #ef9a9a;
    }
    </style>
""", unsafe_allow_html=True)

# 标题
st.title("🐱 XHS-CopyCat | 小红书爆款文案工作台 (Pro版)")
st.markdown("通过 **大数据文本 + 视觉分析 + 竞品拆解**，生成高转化爆款文案。")

# 布局容器：上半部分（输入区）
col1, col2 = st.columns([1, 1])

# 区域 A：本品输入 (Product Zone)
with col1:
    st.markdown('<div class="section-header">📦 区域 A: 本品信息</div>', unsafe_allow_html=True)
    with st.container():
        # 1. 基础信息
        product_name = st.text_input("产品名称", placeholder="例如：xx品牌一段一段奶粉")
        product_price = st.text_input("产品价格/价格带", placeholder="例如：299元 / 3k-5k")
        
        # 2. 产品图片
        product_image = st.file_uploader("上传本期商品图 (1张)", type=['png', 'jpg', 'jpeg'], key="product")
        if product_image:
            st.image(product_image, caption="本期商品", use_column_width=True)

# 区域 B：数据与竞品 (Data & Benchmark Zone)
with col2:
    st.markdown('<div class="section-header">📊 区域 B: 数据 & 竞品</div>', unsafe_allow_html=True)
    
    # Tab 1: 文本数据
    with st.expander("📄 文本数据 (标题/搜索词)", expanded=True):
        titles_text = st.text_area("100个爆款标题 (粘贴文本)", height=100, placeholder="一行一个标题...")
        keywords_text = st.text_area("搜索词数据 (粘贴文本)", height=100, placeholder="粘贴爬取的搜索关键词...")

    # Tab 2: 图片数据
    with st.expander("🖼️ 图片数据 (笔记/评论)", expanded=True):
        post_images = st.file_uploader("对标爆款笔记正文 (5-10张)", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True, key="posts")
        review_images = st.file_uploader("对标商品评论区 (多张)", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True, key="reviews")
        if review_images:
             st.caption(f"已上传 {len(review_images)} 张评论截图")

# 布局容器：下半部分（控制与输出）
st.markdown("---")
st.markdown('<div class="section-header">🚀 区域 C & D: 生成与结果</div>', unsafe_allow_html=True)

# 区域 C：生成控制区
if st.button("开始全维度分析并生成"):
    # 校验输入
    if not product_name:
        st.error("请输入产品名称！")
    elif not product_image:
        st.error("请上传商品图片！")
    elif not post_images:
        st.error("请上传对标笔记图片！")
    elif not titles_text and not keywords_text:
        st.warning("建议提供标题或搜索词数据以获得更精准的结果，继续生成中...")
        
    if product_name and product_image and post_images:
        status_container = st.status("正在进行全维度分析...", expanded=True)
        
        try:
            # 阶段一：多模态并行解析
            status_container.write("🔍 正在并行处理：视觉分析、文本挖掘、评论洞察...")
            
            with concurrent.futures.ThreadPoolExecutor() as executor:
                # 任务1：产品视觉 + 基础信息
                future_product = executor.submit(analyze_product, product_image, product_name, product_price)
                
                # 任务2：文本数据挖掘
                future_text = executor.submit(analyze_text_data, titles_text, keywords_text)
                
                # 任务3：评论区痛点提取
                future_reviews = executor.submit(analyze_reviews, review_images)
                
                # 任务4：对标笔记结构拆解
                future_posts = executor.submit(analyze_posts, post_images)
                
                # 获取结果
                product_res = future_product.result()
                text_res = future_text.result()
                reviews_res = future_reviews.result()
                posts_res = future_posts.result()
            
            # 错误检查
            errors = []
            for name, res in [("产品分析", product_res), ("文本挖掘", text_res), ("竞品拆解", posts_res)]:
                try:
                    res_json = json.loads(res)
                    if "error" in res_json:
                        errors.append(f"{name}: {res_json['error']}")
                except:
                    pass
            if errors:
                status_container.write(f"⚠️ 部分分析遇到问题: {'; '.join(errors)}，正在尝试修复...")

            # 阶段二：生成深度策略报告 (包含词库)
            status_container.write("🧠 正在生成全维度策略报告与爆款词库...")
            strategy_res = generate_strategy_report(product_res, text_res, reviews_res, posts_res)
            
            # 阶段三：生成标题策略 (包含10个标题)
            status_container.write("✍️ 正在生成10个爆款标题...")
            title_res = generate_title_titles(strategy_res)
            
            # 阶段四：预生成一篇文案 (基于第一个推荐标题)
            try:
                titles_data = json.loads(title_res)
                first_title = titles_data.get("generated_titles", [{}])[0].get("title", "未命名标题")
                copy_res = generate_copy(strategy_res, first_title)
            except:
                copy_res = json.dumps({"content": "生成失败", "tags": ""})
            
            status_container.update(label="生成完成！", state="complete", expanded=False)
            
            # 解析所有结果
            try:
                strategy_data = json.loads(strategy_res)
                titles_data = json.loads(title_res)
                copy_data = json.loads(copy_res)
                
                st.success("分析完成！")
                
                # 区域 C (新)：全维度分析与策略报告
                st.subheader("📈 区域 C: 深度策略报告")
                
                tab_strategy, tab_keywords = st.tabs(["🎯 核心策略", "📚 爆款词库 (八大类)"])
                
                with tab_strategy:
                    c1, c2 = st.columns(2)
                    with c1:
                        st.info(f"**👤 目标人群:** {strategy_data.get('target_audience', '未识别')}")
                        st.info(f"**❤️ 核心痛点:** {strategy_data.get('core_pain_point', '未识别')}")
                        st.info(f"**🎭 情绪策略:** {strategy_data.get('emotion_strategy', '未识别')}")
                    with c2:
                        st.success(f"**💎 差异化卖点:** {strategy_data.get('core_selling_point', '未识别')}")
                        st.success(f"**🧘 深层需求:** {strategy_data.get('deep_need', '未识别')}")
                        st.success(f"**🎡 使用场景:** {strategy_data.get('usage_scenario', '未识别')}")
                
                with tab_keywords:
                    st.markdown("基于您的数据，AI 为您提取了专属爆款词库：")
                    library = strategy_data.get("keyword_library", {})
                    
                    cols = st.columns(4)
                    categories = [
                        ("痛点词", "pain_points"), ("效果词", "effects"), 
                        ("承诺词", "promises"), ("情绪词", "emotions"),
                        ("语气词", "tones"), ("人群词", "audiences"),
                        ("时效词", "timings"), ("产品词", "products")
                    ]
                    
                    for idx, (label, key) in enumerate(categories):
                        with cols[idx % 4]:
                            st.markdown(f"**{label}**")
                            words = library.get(key, [])
                            for w in words:
                                st.markdown(f'<span class="keyword-tag">{w}</span>', unsafe_allow_html=True)
                            st.markdown("<br>", unsafe_allow_html=True)

                # 区域 D (新)：标题生成与最终文案
                st.subheader("🔥 区域 D: 爆款标题 & 文案")
                
                tab_titles, tab_copy = st.tabs(["🏆 爆款标题 (含Prompt)", "📝 正文文案 (含Prompt)"])
                
                with tab_titles:
                    st.markdown("### 🚀 推荐标题 (经4项标准审核)")
                    titles = titles_data.get("generated_titles", [])
                    for i, t_obj in enumerate(titles):
                        t_text = t_obj.get('title', '')
                        t_reason = t_obj.get('reason', '')
                        st.markdown(f"**{i+1}. {t_text}**")
                        st.caption(f"💡 {t_reason}")
                    
                    st.markdown("---")
                    st.markdown("### 🤖 标题生成提示词 (Title Prompt)")
                    st.caption("💡 点击下方文本框右上角的复制按钮，或直接编辑内容。")
                    title_prompt_text = titles_data.get("title_prompt", "")
                    st.text_area("标题Prompt (可编辑)", value=title_prompt_text, height=200, key="title_prompt_area")

                with tab_copy:
                    st.markdown("### 📝 正文文案预览")
                    st.markdown(f"**选定标题:** {first_title}")
                    st.text_area("正文内容", value=copy_data.get("content", ""), height=400)
                    st.markdown(f"**标签:** {copy_data.get('tags', '')}")
                    
                    st.markdown("---")
                    st.markdown("### 🤖 正文生成提示词 (Body Prompt)")
                    st.caption("💡 点击下方文本框右上角的复制按钮，或直接编辑内容。")
                    body_prompt_text = copy_data.get("body_prompt", "生成失败或未返回 Prompt")
                    st.text_area("正文Prompt (可编辑)", value=body_prompt_text, height=300, key="body_prompt_area")

            except json.JSONDecodeError:
                st.error("JSON 解析失败，请查看原始输出。")
                
        except Exception as e:
            st.error(f"发生错误: {str(e)}")
