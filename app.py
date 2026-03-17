"""
主程序 - 宠物疾病问答系统界面
"""
import streamlit as st
import pandas as pd
from datetime import datetime
from qa_engine import PetQAEngine

# ==================== 页面配置 ====================
st.set_page_config(
    page_title="宠医助手 - 宠物疾病问答系统",
    page_icon="🐾",
    layout="wide"
)

# ==================== 自定义CSS美化 ====================
st.markdown("""
<style>
    /* 全局样式 */
    .main-header {
        text-align: center;
        padding: 2rem 1rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 20px;
        margin-bottom: 2rem;
        box-shadow: 0 10px 20px rgba(0,0,0,0.1);
    }
    .main-header h1 {
        font-size: 3rem;
        margin-bottom: 0.5rem;
    }
    .main-header p {
        font-size: 1.2rem;
        opacity: 0.95;
    }

    /* 紧急提醒框 */
    .urgent-box {
        background: linear-gradient(135deg, #ff4757 0%, #ff6b81 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.02); }
        100% { transform: scale(1); }
    }

    /* 疾病卡片 */
    .disease-card {
        background: white;
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
        border-left: 5px solid #4CAF50;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .urgent-card {
        border-left: 5px solid #ff4757;
        background: #fff5f5;
    }

    /* 侧边栏 */
    .sidebar-info {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }

    /* 按钮样式 */
    .stButton button {
        border-radius: 20px;
        background: #4CAF50;
        color: white;
        font-weight: bold;
        border: none;
        padding: 0.5rem 1rem;
        transition: all 0.3s;
    }
    .stButton button:hover {
        background: #45a049;
        transform: translateY(-2px);
        box-shadow: 0 5px 10px rgba(0,0,0,0.1);
    }

    /* 页脚 */
    .footer {
        text-align: center;
        margin-top: 3rem;
        padding: 2rem;
        background: #f8f9fa;
        border-radius: 10px;
        color: #666;
    }
</style>
""", unsafe_allow_html=True)


# ==================== 初始化 ====================
@st.cache_resource
def init_engine():
    """初始化问答引擎"""
    return PetQAEngine()


engine = init_engine()

# 初始化session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'search_history' not in st.session_state:
    st.session_state.search_history = []

# ==================== 标题区 ====================
st.markdown("""
<div class="main-header">
    <h1>🐕 宠医助手 · 宠物疾病问答系统 🐈</h1>
    <p>描述症状，获取分析结果 · 紧急情况自动提醒 · 24小时在线</p >
</div>
""", unsafe_allow_html=True)

# ==================== 侧边栏 ====================
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/dog-health.png", width=80)
    st.markdown("## 📋 关于系统")

    with st.expander("项目介绍", expanded=True):
        st.markdown("""
        这是一个**宠物疾病问答系统**，可以帮助你：

        **核心功能：**
        - 🔍 症状匹配分析
        - 🚨 紧急情况识别
        - 📊 疾病知识查询
        - 🏥 就医建议指导

        **数据统计：**
        """)

    # 统计信息
    stats = engine.get_statistics()

    col1, col2 = st.columns(2)
    with col1:
        st.metric("📚 疾病总数", stats['total'])
    with col2:
        st.metric("🚨 紧急疾病", stats['urgent_count'])

    # 按物种统计
    if stats['by_species']:
        st.markdown("**📊 按物种分布：**")
        for species, count in stats['by_species'].items():
            st.markdown(f"- {species}：{count}种")

    # ==================== 历史记录（新加的）====================
    st.markdown("---")
    st.markdown("### 📜 最近查询")

    if 'search_history' not in st.session_state:
        st.session_state.search_history = []

    if st.session_state.search_history:
        # 显示最近5条记录
        for i, item in enumerate(st.session_state.search_history[-5:]):
            # 显示时间和问题
            time_str = item['time'][5:16]
            question_display = item['question'][:15] + "..." if len(item['question']) > 15 else item['question']

            # 添加点击重新查询的功能
            if st.button(f"🕒 {time_str} {question_display}", key=f"history_{i}"):
                st.session_state.quick_question = item['question']
    else:
        st.markdown("暂无查询记录")

    # 清空历史按钮
    if st.session_state.search_history:
        if st.button("🗑️ 清空记录"):
            st.session_state.search_history = []
            st.rerun()

    st.markdown("---")

    # 快速查询按钮
    st.markdown("### 🔍 快速查询")

    quick_questions = [
        "狗呕吐拉稀怎么办",
        "猫不吃东西没精神",
        "狗身上掉毛有皮屑",
        "猫尿不出来一直叫",
        "狗抽搐口吐白沫",
        "猫肚子变大不吃东西"
    ]

    for q in quick_questions:
        if st.button(q, key=f"btn_{q}", use_container_width=True):
            st.session_state.quick_question = q

    st.markdown("---")

    # 紧急就医
    st.markdown("### 🏥 紧急就医")
    city = st.text_input("输入城市名", placeholder="例如：北京")
    if city:
        map_url = f"https://map.baidu.com/search/宠物医院/{city}/"
        st.markdown(f"[📍 点击查看{city}宠物医院]({map_url})")

    # 免责声明
    st.markdown("---")
    st.markdown("""
    **⚠️ 免责声明：**
    本系统仅供科普参考，不能替代专业兽医诊断。如遇紧急情况，请立即就医。
    """)
# ==================== 主界面 ====================

# 症状自查向导
with st.expander("🔍 症状快速自查向导（点击展开）", expanded=False):
    col1, col2, col3 = st.columns(3)

    with col1:
        pet_type = st.selectbox(
            "宠物种类",
            ["请选择", "狗", "猫", "其他"]
        )

    with col2:
        symptom = st.selectbox(
            "主要症状",
            ["请选择", "呕吐", "拉稀", "不吃东西", "没精神",
             "咳嗽", "掉毛", "尿异常", "抽搐"]
        )

    with col3:
        duration = st.selectbox(
            "持续时间",
            ["请选择", "1天内", "2-3天", "3天以上"]
        )

    if st.button("开始自查", use_container_width=True):
        if pet_type != "请选择" and symptom != "请选择":
            query = f"{pet_type}{symptom}"
            st.session_state.quick_question = query
            st.success(f"正在查询：{query}")
        else:
            st.warning("请选择宠物种类和主要症状")

# 处理快速查询
if 'quick_question' in st.session_state:
    question = st.session_state.quick_question
    del st.session_state.quick_question

    # 记录到历史
    st.session_state.search_history.append({
        'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'question': question
    })

    # 显示用户问题
    with st.chat_message("user"):
        st.markdown(f"**您**：{question}")

    # 获取答案
    with st.chat_message("assistant"):
        with st.spinner("正在分析症状..."):
            result = engine.get_answer(question)

            if result['success']:
                # 显示匹配结果
                for i, item in enumerate(result['results']):
                    # 判断卡片样式
                    card_class = "urgent-card" if item['urgent'] else "disease-card"
                    urgent_tag = "🚨 紧急" if item['urgent'] else "💚 普通"

                    # 显示疾病卡片
                    st.markdown(f"""
                    <div class="{card_class}">
                        <h4>{i + 1}. {item['disease']} 
                            <span style="color: {'#ff4757' if item['urgent'] else '#4CAF50'}; 
                                  font-size: 0.9rem; margin-left: 1rem;">
                                {urgent_tag}
                            </span>
                        </h4>
                        <p style="color: #666;">匹配度：{int(item['score'] * 100)}%</p >
                        <p style="white-space: pre-line;">{item['answer']}</p >
                    </div>
                    """, unsafe_allow_html=True)

                # 紧急提醒
                if result['urgent']:
                    st.markdown("""
                    <div class="urgent-box">
                        <h3>🚨 紧急情况提醒</h3>
                        <p>根据您描述的症状，这可能是紧急情况！请立即就医！</p >
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.warning(result['message'])

    st.session_state.messages.append({"role": "assistant", "content": "已回复"})

# 聊天输入框
if prompt := st.chat_input("描述一下宠物的症状，例如：狗呕吐拉稀没精神"):

    # 记录到历史
    st.session_state.search_history.append({
        'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'question': prompt
    })

    # 显示用户问题
    with st.chat_message("user"):
        st.markdown(f"**您**：{prompt}")

    # 获取答案
    with st.chat_message("assistant"):
        with st.spinner("正在分析症状..."):
            result = engine.get_answer(prompt)

            if result['success']:
                # 显示匹配结果
                for i, item in enumerate(result['results']):
                    card_class = "urgent-card" if item['urgent'] else "disease-card"
                    urgent_tag = "🚨 紧急" if item['urgent'] else "💚 普通"

                    st.markdown(f"""
                    <div class="{card_class}">
                        <h4>{i + 1}. {item['disease']} 
                            <span style="color: {'#ff4757' if item['urgent'] else '#4CAF50'}; 
                                  font-size: 0.9rem; margin-left: 1rem;">
                                {urgent_tag}
                            </span>
                        </h4>
                        <p style="color: #666;">匹配度：{int(item['score'] * 100)}%</p >
                        <p style="white-space: pre-line;">{item['answer']}</p >
                    </div>
                    """, unsafe_allow_html=True)

                if result['urgent']:
                    st.markdown("""
                    <div class="urgent-box">
                        <h3>🚨 紧急情况提醒</h3>
                        <p>请立即就医！</p >
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.warning(result['message'])

# ==================== 底部信息 ====================
st.markdown("---")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    ### 📝 使用说明
    - 直接输入症状描述
    - 点击快速查询按钮
    - 查看多个可能结果
    - 紧急情况立即就医
    """)

with col2:
    st.markdown("""
    ### 💡 输入技巧
    - 包含物种（狗/猫）
    - 多个症状一起描述
    - 描述越详细越好
    """)

with col3:
    st.markdown("""
    ### 📞 紧急电话
    - 全国动物救助：12395
    - 附近宠物医院
    - 24小时急诊
    """)

st.markdown("""
<div class="footer">
    <p>🐾 宠医助手 · 个人作品</p >
    <p style="font-size: 0.8rem; color: #999;">
        ⚠️ 本系统仅供科普参考，不能替代专业兽医诊断
    </p >
</div>
""", unsafe_allow_html=True)