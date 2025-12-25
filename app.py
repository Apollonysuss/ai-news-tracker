import streamlit as st
import arxiv
import feedparser
from openai import OpenAI
import datetime

# --- 1. 网页设置 ---
st.set_page_config(page_title="具身智能 & 自动驾驶日报", page_icon="🤖", layout="wide")
st.title("🤖 具身智能 & 自动驾驶情报站")

# --- 2. 侧边栏：设置与控制 ---
with st.sidebar:
    st.header("⚙️ 设置面板")
    
    # 获取 API Key (优先从系统读取，读不到就让用户填)
    api_key = st.secrets.get("DEEPSEEK_API_KEY", None)
    if not api_key:
        api_key = st.text_input("请输入 DeepSeek/OpenAI API Key:", type="password")
        if not api_key:
            st.warning("⚠️ 未检测到 API Key，AI 总结功能将不可用")
    
    base_url = st.text_input("API 地址", value="https://api.deepseek.com")
    model_name = st.text_input("模型名称", value="deepseek-chat")
    
    st.divider()
    st.subheader("关键词设置")
    # 默认搜索关键词
    default_keywords = "Embodied AI\nAutonomous Driving\nHumanoid Robot\nEnd-to-end Driving"
    keywords_input = st.text_area("输入关键词 (每行一个)", value=default_keywords, height=150)
    keywords = [k.strip() for k in keywords_input.split('\n') if k.strip()]

# --- 3. 功能函数：AI 总结 ---
def get_ai_summary(text):
    if not api_key:
        return None
    
    client = OpenAI(api_key=api_key, base_url=base_url)
    try:
        prompt = f"请用中文一句话总结这篇关于{keywords[0]}的文章核心，并列出3个关键点。\n\n原文：{text[:1000]}"
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"AI 总结出错: {e}"

# --- 4. 功能函数：获取数据 ---
def get_arxiv_papers():
    search_query = " OR ".join([f'ti:"{k}"' for k in keywords])
    # 搜索最近提交的
    search = arxiv.Search(query=search_query, max_results=5, sort_by=arxiv.SortCriterion.SubmittedDate)
    
    results = []
    client = arxiv.Client()
    for r in client.results(search):
        results.append({
            "title": r.title,
            "link": r.pdf_url,
            "summary": r.summary,
            "date": r.published.date()
        })
    return results

# --- 5. 页面展示逻辑 ---
tab1, tab2 = st.tabs(["📄 最新论文 (Arxiv)", "🌍 产业新闻 (RSS)"])

with tab1:
    if st.button("🔍 扫描最新论文"):
        with st.spinner("正在连接 Arxiv 数据库..."):
            papers = get_arxiv_papers()
            st.success(f"找到 {len(papers)} 篇最新论文")
            
            for p in papers:
                with st.expander(f"[{p['date']}] {p['title']}"):
                    st.write(f"**原文链接**: {p['link']}")
                    if st.button("✨ AI 解读", key=p['link']):
                        summary = get_ai_summary(p['summary'])
                        if summary:
                            st.info(summary)
                    else:
                        st.caption("点击上方按钮查看 AI 中文总结")
                        st.text(p['summary'])

with tab2:
    st.info("💡 提示：这里演示从 TechCrunch 获取 AI 新闻")
    # 这里用一个稳定的国外科技源做演示
    rss_url = "https://techcrunch.com/category/artificial-intelligence/feed/"
    
    if st.button("🔍 扫描最新新闻"):
        feed = feedparser.parse(rss_url)
        for entry in feed.entries[:5]:
            st.markdown(f"**[{entry.published[:16]}] {entry.title}**")
            st.markdown(f"[阅读原文]({entry.link})")
            if st.button("✨ AI 摘要", key=entry.link):
                # 组合标题和摘要发给 AI
                content = entry.title + "\n" + (entry.get('summary', '') or entry.get('description', ''))
                summary = get_ai_summary(content)
                if summary:
                    st.success(summary)
            st.divider()
