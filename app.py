import streamlit as st
import pandas as pd
import os
from qa_engine import PetQA
import time

# 页面配置
st.set_page_config(
    page_title="AI宠物医生",
    page_icon="🐕",
    layout="wide"
)

# 初始化主题颜色
if 'theme' not in st.session_state:
    st.session_state['theme'] = {
        "primary": "#43e97b",
        "secondary": "#38f9d7",
        "gradient": "linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)"
    }

# 获取当前主题
theme = st.session_state['theme']

# 自定义CSS
st.markdown(f"""
<style>
    .main-header {{
        background: {theme['gradient']};
        padding: 2rem;
        border-radius: 10px;
        text-align: center;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px {theme['primary']}40;
    }}
    
    .main-header h1 {{
        color: white;
        margin: 0;
        font-size: 2.5rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }}
    
    .main-header p {{
        color: rgba(255,255,255,0.95);
        font-size: 1.2rem;
        margin: 0.5rem 0 0 0;
        font-weight: 300;
    }}
    
    /* 按钮样式 */
    .stButton button {{
        background: {theme['gradient']};
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.6rem 2rem;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s ease;
        border: 1px solid rgba(255,255,255,0.2);
    }}
    
    .stButton button:hover {{
        transform: translateY(-3px);
        box-shadow: 0 10px 20px {theme['primary']}80;
    }}
    
    /* 输入框样式 */
    .stTextInput input {{
        border: 2px solid #e8f5e9;
        border-radius: 12px;
        padding: 0.8rem;
        font-size: 1rem;
        transition: all 0.3s ease;
        background: white;
    }}
    
    .stTextInput input:focus {{
        border-color: {theme['primary']};
        box-shadow: 0 0 0 3px {theme['primary']}20;
        outline: none;
    }}
    
    /* 聊天消息样式 */
    .stChatMessage {{
        border-radius: 15px;
        padding: 1rem;
        margin: 0.5rem 0;
    }}
    
    /* 侧边栏样式 */
    .css-1d391kg {{
        background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%);
        padding: 2rem 1rem;
    }}
    
    /* 分割线 */
    hr {{
        border: none;
        height: 2px;
        background: linear-gradient(90deg, transparent, {theme['primary']}, transparent);
        margin: 2rem 0;
    }}
    
    /* 成功消息 */
    .stAlert {{
        border-radius: 12px;
        border-left: 4px solid {theme['primary']};
    }}
    
    /* 标题样式 */
    h1, h2, h3 {{
        color: #2c3e50;
    }}
    
    /* 动画效果 */
    @keyframes fadeIn {{
        from {{ opacity: 0; transform: translateY(10px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    
    .main {{
        animation: fadeIn 0.5s ease;
    }}
</style>
""", unsafe_allow_html=True)

# 初始化QA引擎
@st.cache_resource
def init_qa_engine():
    data_path = os.path.join("data", "diseases.csv")
    if os.path.exists(data_path):
        return PetQA(data_path)
    return None

# 侧边栏
with st.sidebar:
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 15px;
        color: white;
        margin: 1rem 0;
        text-align: center;
    ">
        <h2 style="color: white; margin: 0;">🐕 AI宠物医生</h2>
        <p style="color: rgba(255,255,255,0.9); margin: 0;">24小时在线问诊</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 📋 宠物档案")

    with st.container():
        st.markdown("""
        <div style="
            background: white;
            padding: 1rem;
            border-radius: 15px;
            border: 1px solid #e9ecef;
            margin-bottom: 1rem;
        ">
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            pet_species = st.selectbox("物种", ["🐕 狗", "🐈 猫", "🐇 兔子", "🦜 鸟"], key="species")
        with col2:
            pet_age = st.number_input("年龄(岁)", min_value=0.0, max_value=30.0, value=1.0, key="age")

        pet_weight = st.number_input("体重(kg)", min_value=0.1, max_value=100.0, value=5.0, key="weight")
        pet_name = st.text_input("宠物名字", placeholder="如：旺财", key="pet_name")
        pet_breed = st.text_input("品种", placeholder="如：金毛", key="breed")

        if st.button("📝 保存档案", use_container_width=True):
            st.session_state.pet_info = {
                "name": pet_name if pet_name else "未命名",
                "species": pet_species,
                "age": pet_age,
                "weight": pet_weight,
                "breed": pet_breed if pet_breed else "未填写"
            }
            st.success("✅ 宠物档案已保存！")

        st.markdown("</div>", unsafe_allow_html=True)

    # 显示已保存的档案
    if 'pet_info' in st.session_state:
        with st.expander("📌 当前档案", expanded=True):
            info = st.session_state.pet_info
            st.markdown(f"""
            **名字：** {info['name']}  
            **物种：** {info['species']}  
            **年龄：** {info['age']}岁  
            **体重：** {info['weight']}kg  
            **品种：** {info['breed']}
            """)

    st.markdown("---")

    # ===== 7色主题选择器 =====
    st.markdown("### 🎨 主题颜色")

    # 定义7种颜色方案
    color_themes = {
        "清新绿": {
            "primary": "#43e97b",
            "secondary": "#38f9d7",
            "gradient": "linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)",
        },
        "温暖橙": {
            "primary": "#fa709a",
            "secondary": "#fee140",
            "gradient": "linear-gradient(135deg, #fa709a 0%, #fee140 100%)",
        },
        "专业蓝": {
            "primary": "#66a6ff",
            "secondary": "#89f7fe",
            "gradient": "linear-gradient(135deg, #89f7fe 0%, #66a6ff 100%)",
        },
        "浪漫紫": {
            "primary": "#9d50bb",
            "secondary": "#6e48aa",
            "gradient": "linear-gradient(135deg, #9d50bb 0%, #6e48aa 100%)",
        },
        "热情红": {
            "primary": "#ff6b6b",
            "secondary": "#ff8e8e",
            "gradient": "linear-gradient(135deg, #ff6b6b 0%, #ff8e8e 100%)",
        },
        "阳光黄": {
            "primary": "#f9d423",
            "secondary": "#fdaa8b",
            "gradient": "linear-gradient(135deg, #f9d423 0%, #fdaa8b 100%)",
        },
        "深邃黑": {
            "primary": "#2c3e50",
            "secondary": "#3498db",
            "gradient": "linear-gradient(135deg, #2c3e50 0%, #3498db 100%)",
        }
    }

    # 用单选按钮选择颜色
    selected_color = st.radio(
        "选择主题颜色",
        options=list(color_themes.keys()),
        index=0,
        key="color_theme_selector"
    )

    # 获取选中的颜色配置
    new_theme = color_themes[selected_color]

    # 如果主题改变了，更新session_state
    if st.session_state['theme'] != new_theme:
        st.session_state['theme'] = new_theme
        st.rerun()  # 重新运行以应用新主题

    # 显示当前颜色预览
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"<div style='background: {new_theme['primary']}; width: 30px; height: 30px; border-radius: 50%; margin: 0 auto;'></div>", unsafe_allow_html=True)
        st.caption("主色")
    with col2:
        st.markdown(f"<div style='background: {new_theme['secondary']}; width: 30px; height: 30px; border-radius: 50%; margin: 0 auto;'></div>", unsafe_allow_html=True)
        st.caption("辅色")
    with col3:
        st.markdown(f"<div style='background: {new_theme['primary']}; width: 30px; height: 30px; border-radius: 50%; opacity: 0.5; margin: 0 auto;'></div>", unsafe_allow_html=True)
        st.caption("浅色")

    st.markdown("---")
    st.markdown("### 🔍 快速查询")
    quick_questions = [
        "🐕 狗狗感冒了怎么办？",
        "🐈 猫咪不吃东西",
        "🦷 怎么给宠物刷牙",
        "💉 疫苗接种时间",
        "🍖 宠物饮食建议"
    ]

    for q in quick_questions:
        if st.button(q, use_container_width=True):
            st.session_state.question = q

# 主界面
st.markdown("""
<div class="main-header">
    <h1>🐕 AI宠物医生</h1>
    <p>专业的宠物健康顾问，24小时在线解答</p>
</div>
""", unsafe_allow_html=True)

# 初始化QA引擎
qa_engine = init_qa_engine()

if qa_engine is None:
    st.error("❌ 无法加载疾病数据，请检查 data/diseases.csv 文件是否存在")
    st.stop()

# 初始化会话状态
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "你好！我是AI宠物医生。请告诉我你的宠物有什么症状或问题？"}
    ]

if "question" not in st.session_state:
    st.session_state.question = None

# 显示聊天历史
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 处理快速查询
if st.session_state.question:
    question = st.session_state.question
    st.session_state.question = None

    # 显示用户问题
    with st.chat_message("user"):
        st.markdown(question)
    st.session_state.messages.append({"role": "user", "content": question})

    # 获取并显示AI回答
    with st.chat_message("assistant"):
        with st.spinner("AI正在思考..."):
            # 获取宠物信息
            pet_context = ""
            if 'pet_info' in st.session_state:
                info = st.session_state.pet_info
                pet_context = f"（宠物信息：{info['name']}，{info['species']}，{info['age']}岁，{info['weight']}kg）"

            full_question = f"{pet_context} {question}" if pet_context else question
            result = qa_engine.get_answer(full_question)

            if result["found"]:
                answer = f"**诊断建议：**\n\n{result['answer']}"
                if result.get("source"):
                    answer += f"\n\n*参考：{result['source']}*"
            else:
                answer = result["answer"]

            st.markdown(answer)
    st.session_state.messages.append({"role": "assistant", "content": answer})

# 聊天输入框
if prompt := st.chat_input("请输入你的问题..."):
    # 显示用户问题
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 获取并显示AI回答
    with st.chat_message("assistant"):
        with st.spinner("AI正在思考..."):
            # 获取宠物信息
            pet_context = ""
            if 'pet_info' in st.session_state:
                info = st.session_state.pet_info
                pet_context = f"（宠物信息：{info['name']}，{info['species']}，{info['age']}岁，{info['weight']}kg）"

            full_question = f"{pet_context} {prompt}" if pet_context else prompt
            result = qa_engine.get_answer(full_question)

            if result["found"]:
                answer = f"**诊断建议：**\n\n{result['answer']}"
                if result.get("source"):
                    answer += f"\n\n*参考：{result['source']}*"
            else:
                answer = result["answer"]

            st.markdown(answer)
    st.session_state.messages.append({"role": "assistant", "content": answer})

# 侧边栏底部
with st.sidebar:
    st.markdown("---")
    st.markdown("### 📞 紧急联系")
    st.warning("""
    **24小时宠物医院**
    📱 电话：xxx-xxxx-xxxx
    🚑 急诊：xxx-xxxx-xxxx
    """)

    if st.button("🗑️ 清空对话", use_container_width=True):
        st.session_state.messages = [
            {"role": "assistant", "content": "你好！我是AI宠物医生。请告诉我你的宠物有什么症状或问题？"}
        ]
        st.rerun()