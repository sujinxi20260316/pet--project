import streamlit as st
import pandas as pd
import os
import time
from PIL import Image
import base64
from io import BytesIO
import datetime
import requests
import json
import numpy as np
import cv2
import hashlib

# 页面配置
st.set_page_config(
    page_title="AI宠物医生",
    page_icon="🐕",
    layout="wide"
)

# ===== 从环境变量读取密钥 =====
AMAP_KEY = os.getenv("AMAP_KEY", "")
BAIDU_API_KEY = os.getenv("BAIDU_API_KEY", "")
BAIDU_SECRET_KEY = os.getenv("BAIDU_SECRET_KEY", "")

# ===== 初始化主题颜色 =====
color_themes = {
    "清新绿": {"primary": "#43e97b", "secondary": "#38f9d7",
               "gradient": "linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)"},
    "温暖橙": {"primary": "#fa709a", "secondary": "#fee140",
               "gradient": "linear-gradient(135deg, #fa709a 0%, #fee140 100%)"},
    "专业蓝": {"primary": "#66a6ff", "secondary": "#89f7fe",
               "gradient": "linear-gradient(135deg, #89f7fe 0%, #66a6ff 100%)"},
    "浪漫紫": {"primary": "#9d50bb", "secondary": "#6e48aa",
               "gradient": "linear-gradient(135deg, #9d50bb 0%, #6e48aa 100%)"},
    "热情红": {"primary": "#ff6b6b", "secondary": "#ff8e8e",
               "gradient": "linear-gradient(135deg, #ff6b6b 0%, #ff8e8e 100%)"},
    "阳光黄": {"primary": "#f9d423", "secondary": "#fdaa8b",
               "gradient": "linear-gradient(135deg, #f9d423 0%, #fdaa8b 100%)"},
    "深邃黑": {"primary": "#2c3e50", "secondary": "#3498db",
               "gradient": "linear-gradient(135deg, #2c3e50 0%, #3498db 100%)"}
}

if 'selected_theme_name' not in st.session_state:
    st.session_state.selected_theme_name = "清新绿"
    st.session_state['theme'] = color_themes["清新绿"]

# 获取当前主题
theme = st.session_state['theme']

# ===== 初始化缓存 =====
if 'hospital_cache' not in st.session_state:
    st.session_state.hospital_cache = {}
if 'last_search_time' not in st.session_state:
    st.session_state.last_search_time = 0
if 'selected_city' not in st.session_state:
    st.session_state.selected_city = None
if 'city_hospitals' not in st.session_state:
    st.session_state.city_hospitals = {}
if 'analysis_result' not in st.session_state:
    st.session_state.analysis_result = None
if 'analysis_image' not in st.session_state:
    st.session_state.analysis_image = None
if 'analysis_source' not in st.session_state:
    st.session_state.analysis_source = None
if 'show_camera' not in st.session_state:
    st.session_state.show_camera = False
if 'friends_list' not in st.session_state:
    st.session_state.friends_list = []  # 朋友列表
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = ""

# ===== 自定义CSS =====
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

    .hospital-card {{
        background: white;
        padding: 1rem;
        border-radius: 10px;
        border: 1px solid #e9ecef;
        margin: 0.5rem 0;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        transition: all 0.3s ease;
    }}

    .hospital-card:hover {{
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        transform: translateY(-2px);
    }}

    .symptom-tag {{
        display: inline-block;
        padding: 5px 10px;
        margin: 3px;
        border-radius: 15px;
        font-size: 0.9rem;
        font-weight: 500;
    }}

    .symptom-high {{
        background: #ff6b6b;
        color: white;
    }}

    .symptom-medium {{
        background: #ffd93d;
        color: #333;
    }}

    .symptom-low {{
        background: #6bcf7f;
        color: white;
    }}

    .emergency-badge {{
        background: #ff0000;
        color: white;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.8rem;
        margin-left: 10px;
        animation: pulse 1.5s infinite;
    }}

    @keyframes pulse {{
        0% {{ opacity: 1; }}
        50% {{ opacity: 0.7; }}
        100% {{ opacity: 1; }}
    }}

    .severe-badge {{
        background: #ff9900;
        color: white;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.8rem;
        margin-left: 10px;
    }}

    .city-info {{
        background: linear-gradient(135deg, #667eea20 0%, #764ba220 100%);
        padding: 0.5rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        text-align: center;
        font-size: 0.9rem;
        color: #666;
    }}

    .color-preview {{
        display: flex;
        justify-content: center;
        align-items: center;
        flex-direction: column;
        padding: 10px;
        border-radius: 10px;
        background: white;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }}

    .section-divider {{
        margin: 2rem 0;
        border-top: 2px solid #e9ecef;
    }}

    .friend-chat {{
        background: #f8f9fa;
        padding: 0.5rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }}
</style>
""", unsafe_allow_html=True)

# ===== 初始化会话状态 =====
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "你好！我是AI宠物医生。请告诉我你的宠物有什么症状或问题？"}
    ]

if "question" not in st.session_state:
    st.session_state.question = None

# ===== 城市医院数据库（包含都匀市）=====
CITY_HOSPITALS = {
    "贵阳市": [
        {
            "name": "贵阳瑞鹏宠物医院（南明店）",
            "address": "贵阳市南明区新华路58号",
            "phone": "0851-85511234",
            "emergency": "13985011234",
            "hours": "24小时",
            "lat": 26.56,
            "lon": 106.71
        },
        {
            "name": "贵阳康诺宠物医院（云岩店）",
            "address": "贵阳市云岩区北京路128号",
            "phone": "0851-86881234",
            "emergency": "13985021234",
            "hours": "24小时",
            "lat": 26.60,
            "lon": 106.72
        },
        {
            "name": "贵阳宠颐生动物医院（观山湖店）",
            "address": "贵阳市观山湖区金阳南路298号",
            "phone": "0851-84841234",
            "emergency": "13985031234",
            "hours": "24小时",
            "lat": 26.65,
            "lon": 106.62
        }
    ],
    "遵义市": [
        {
            "name": "遵义瑞鹏宠物医院",
            "address": "遵义市红花岗区中华路168号",
            "phone": "0851-28621234",
            "emergency": "13985671234",
            "hours": "24小时",
            "lat": 27.72,
            "lon": 106.93
        }
    ],
    "六盘水市": [
        {
            "name": "六盘水宠医堂动物医院",
            "address": "六盘水市钟山区人民中路89号",
            "phone": "0858-8261234",
            "emergency": "13985881234",
            "hours": "9:00-21:00",
            "lat": 26.59,
            "lon": 104.83
        }
    ],
    "安顺市": [
        {
            "name": "安顺康诺宠物医院",
            "address": "安顺市西秀区黄果树大街276号",
            "phone": "0851-33521234",
            "emergency": "13985331234",
            "hours": "9:00-20:00",
            "lat": 26.25,
            "lon": 105.95
        }
    ],
    "毕节市": [
        {
            "name": "毕节瑞鹏宠物医院",
            "address": "毕节市七星关区开行路188号",
            "phone": "0857-8231234",
            "emergency": "13985771234",
            "hours": "9:00-21:00",
            "lat": 27.30,
            "lon": 105.29
        }
    ],
    "铜仁市": [
        {
            "name": "铜仁宠颐生动物医院",
            "address": "铜仁市碧江区东太大道456号",
            "phone": "0856-5221234",
            "emergency": "13985661234",
            "hours": "9:00-20:00",
            "lat": 27.73,
            "lon": 109.19
        }
    ],
    "黔南州（含都匀）": [
        {
            "name": "都匀康贝宠物医院",
            "address": "黔南州都匀市剑江中路234号",
            "phone": "0854-8221234",
            "emergency": "13985441234",
            "hours": "9:00-21:00",
            "lat": 26.26,
            "lon": 107.52
        },
        {
            "name": "都匀爱宠动物医院",
            "address": "黔南州都匀市民族路78号",
            "phone": "0854-8234567",
            "emergency": "13985451234",
            "hours": "9:00-20:00",
            "lat": 26.27,
            "lon": 107.53
        }
    ],
    "黔东南州": [
        {
            "name": "凯里爱宠动物医院",
            "address": "黔东南州凯里市宁波路167号",
            "phone": "0855-8231234",
            "emergency": "13985551234",
            "hours": "9:00-21:00",
            "lat": 26.58,
            "lon": 107.98
        }
    ],
    "黔西南州": [
        {
            "name": "兴义康诺宠物医院",
            "address": "黔西南州兴义市桔山大道345号",
            "phone": "0859-3211234",
            "emergency": "13985991234",
            "hours": "9:00-20:00",
            "lat": 25.09,
            "lon": 104.89
        }
    ]
}


# ===== 获取当前位置 =====
def get_current_location():
    """获取当前IP所在位置"""
    try:
        response = requests.get("http://ip-api.com/json/?lang=zh-CN", timeout=3)
        data = response.json()
        if data["status"] == "success":
            city = data.get("city", "贵阳市")
            # 标准化城市名称
            for standard_city in CITY_HOSPITALS.keys():
                if standard_city in city or city in standard_city:
                    return {
                        "city": standard_city,
                        "lat": data.get("lat", 26.65),
                        "lon": data.get("lon", 106.63)
                    }
    except:
        pass

    return {
        "city": "贵阳市",
        "lat": 26.65,
        "lon": 106.63
    }


# ===== 增强的图像预处理函数 =====
def enhance_image_for_analysis(image):
    """使用CLAHE和锐化增强图像细节"""
    try:
        img = np.array(image)
        if len(img.shape) == 3:
            # 转为灰度
            gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
            # CLAHE 增强
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
            enhanced_gray = clahe.apply(gray)
            # 锐化
            kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
            sharpened = cv2.filter2D(enhanced_gray, -1, kernel)
            # 转回三通道（保持颜色）
            enhanced = cv2.cvtColor(sharpened, cv2.COLOR_GRAY2RGB)
            # 轻微降噪
            enhanced = cv2.fastNlMeansDenoising(enhanced, None, 5, 7, 21)
            return Image.fromarray(enhanced)
        else:
            return image
    except Exception as e:
        print(f"图像增强失败: {e}")
        return image


# ===== 六部位专业检测函数（每个返回列表，改进版）=====
def analyze_eyes(img_rgb, hsv, gray, height, width, kernel, kernel_large):
    """检测眼睛部位的健康状况（改进版）"""
    try:
        # 假设眼睛位于图像上半部分中间区域
        eye_y_start = int(height * 0.15)
        eye_y_end = int(height * 0.45)
        eye_x_start = int(width * 0.3)
        eye_x_end = int(width * 0.7)

        if eye_x_end <= eye_x_start or eye_y_end <= eye_y_start:
            return [{"name": "眼睛区域未识别", "confidence": 0.3, "advice": "请确保照片包含清晰的眼睛区域", "severity": "轻度",
                     "body_part": "眼睛"}]

        eye_roi = img_rgb[eye_y_start:eye_y_end, eye_x_start:eye_x_end]
        if eye_roi.size == 0:
            return [{"name": "眼睛区域为空", "confidence": 0.3, "advice": "无法提取眼睛区域", "severity": "轻度",
                     "body_part": "眼睛"}]

        eye_hsv = cv2.cvtColor(eye_roi, cv2.COLOR_BGR2HSV)
        eye_gray = cv2.cvtColor(eye_roi, cv2.COLOR_BGR2GRAY)

        # 检测红眼（红色调）
        lower_red1 = np.array([0, 50, 50])
        upper_red1 = np.array([10, 255, 255])
        lower_red2 = np.array([170, 50, 50])
        upper_red2 = np.array([180, 255, 255])

        red_mask1 = cv2.inRange(eye_hsv, lower_red1, upper_red1)
        red_mask2 = cv2.inRange(eye_hsv, lower_red2, upper_red2)
        red_mask = cv2.bitwise_or(red_mask1, red_mask2)
        red_ratio = np.sum(red_mask > 0) / red_mask.size if red_mask.size > 0 else 0

        # 检测分泌物（黄白色）
        lower_secretion = np.array([20, 50, 150])
        upper_secretion = np.array([40, 255, 255])
        secretion_mask = cv2.inRange(eye_hsv, lower_secretion, upper_secretion)
        secretion_ratio = np.sum(secretion_mask > 0) / secretion_mask.size if secretion_mask.size > 0 else 0

        # 检测肿胀（通过纹理变化）
        eye_blur = cv2.GaussianBlur(eye_gray, (5, 5), 0)
        eye_edges = cv2.Canny(eye_blur, 30, 100)
        edge_density = np.sum(eye_edges > 0) / eye_edges.size if eye_edges.size > 0 else 0

        # 降低阈值，提高灵敏度
        if red_ratio > 0.02 or secretion_ratio > 0.01 or edge_density < 0.03:
            red_conf = min(red_ratio * 8, 0.9)          # 提高放大系数
            secretion_conf = min(secretion_ratio * 12, 0.9)
            edge_conf = max(0, min(0.7, (0.05 - edge_density) * 15))

            confidence = max(red_conf, secretion_conf, edge_conf)
            confidence = min(confidence + 0.1, 0.95)

            if red_conf > secretion_conf and red_conf > edge_conf:
                name = "眼睛发红"
                advice = "眼睛发红，可能有结膜炎或过敏，建议使用宠物专用眼药水"
                severity = "中度" if confidence > 0.6 else "轻度"
            elif secretion_conf > red_conf and secretion_conf > edge_conf:
                name = "眼部分泌物"
                advice = "检测到眼部分泌物，可能是感染或泪腺问题，建议清洁并观察"
                severity = "中度"
            else:
                name = "眼部肿胀"
                advice = "眼部肿胀，可能有炎症或外伤，建议冷敷并观察"
                severity = "严重" if confidence > 0.7 else "中度"

            return [{
                "name": name,
                "confidence": confidence,
                "advice": advice,
                "severity": severity,
                "body_part": "眼睛"
            }]
        else:
            return [{
                "name": "眼睛正常",
                "confidence": 0.8,
                "advice": "眼睛未见明显异常",
                "severity": "轻度",
                "body_part": "眼睛"
            }]
    except Exception as e:
        return [{
            "name": "眼睛检测异常",
            "confidence": 0.3,
            "advice": f"分析出错: {str(e)}",
            "severity": "轻度",
            "body_part": "眼睛"
        }]


def analyze_skin(img_rgb, hsv, gray, height, width, kernel, kernel_large, total_pixels):
    """检测皮肤健康状况（改进版）"""
    symptoms = []
    try:
        # 1. 皮肤发红检测 - 降低阈值
        lower_red1 = np.array([0, 50, 50])
        upper_red1 = np.array([10, 255, 255])
        lower_red2 = np.array([170, 50, 50])
        upper_red2 = np.array([180, 255, 255])

        red_mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
        red_mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
        red_mask = cv2.bitwise_or(red_mask1, red_mask2)
        red_mask = cv2.morphologyEx(red_mask, cv2.MORPH_OPEN, kernel)
        red_percent = np.sum(red_mask > 0) / total_pixels

        if red_percent > 0.02:  # 原0.03
            confidence = min(red_percent * 5, 0.85)  # 原*4
            symptoms.append({
                "name": "皮肤发红",
                "confidence": confidence,
                "advice": "皮肤发红，可能有炎症或过敏，建议检查过敏源",
                "severity": "中度" if confidence > 0.6 else "轻度",
                "body_part": "皮肤"
            })

        # 2. 皮肤溃烂检测 - 降低面积要求
        lower_ulcer = np.array([0, 100, 30])
        upper_ulcer = np.array([30, 255, 100])
        ulcer_mask = cv2.inRange(hsv, lower_ulcer, upper_ulcer)
        ulcer_mask = cv2.morphologyEx(ulcer_mask, cv2.MORPH_CLOSE, kernel_large)
        ulcer_contours, _ = cv2.findContours(ulcer_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        ulcer_detected = False
        ulcer_confidence = 0
        for contour in ulcer_contours:
            area = cv2.contourArea(contour)
            if area > 200:  # 原300
                confidence = min(area / 5000, 0.9)  # 原/6000
                if confidence > ulcer_confidence:
                    ulcer_confidence = confidence
                    ulcer_detected = True

        if ulcer_detected and ulcer_confidence > 0.2:  # 原0.25
            symptoms.append({
                "name": "皮肤溃烂",
                "confidence": ulcer_confidence,
                "advice": "检测到皮肤溃烂，需要清创和抗感染治疗",
                "severity": "严重",
                "body_part": "皮肤"
            })

        # 3. 皮屑检测 - 降低阈值
        lower_white = np.array([0, 0, 200])
        upper_white = np.array([180, 30, 255])
        white_mask = cv2.inRange(hsv, lower_white, upper_white)
        white_mask = cv2.morphologyEx(white_mask, cv2.MORPH_OPEN, kernel)
        white_percent = np.sum(white_mask > 0) / total_pixels

        if white_percent > 0.015:  # 原0.02
            confidence = min(white_percent * 8, 0.75)  # 原*6
            symptoms.append({
                "name": "皮屑",
                "confidence": confidence,
                "advice": "检测到皮屑，可能是皮肤干燥或真菌感染",
                "severity": "中度",
                "body_part": "皮肤"
            })

        # 4. 脱毛检测 - 降低阈值
        _, bright_mask = cv2.threshold(gray, 220, 255, cv2.THRESH_BINARY)
        bright_mask = cv2.morphologyEx(bright_mask, cv2.MORPH_OPEN, kernel)
        bright_percent = np.sum(bright_mask > 0) / total_pixels

        if bright_percent > 0.06:  # 原0.08
            confidence = min(bright_percent * 3, 0.8)  # 原*2.5
            symptoms.append({
                "name": "脱毛",
                "confidence": confidence,
                "advice": "检测到脱毛现象，建议检查是否有真菌感染或寄生虫",
                "severity": "中度",
                "body_part": "皮肤"
            })

        # 如果没有皮肤症状，添加一个默认的皮肤正常
        if not symptoms:
            symptoms.append({
                "name": "皮肤正常",
                "confidence": 0.8,
                "advice": "皮肤状态良好",
                "severity": "轻度",
                "body_part": "皮肤"
            })

        return symptoms
    except Exception as e:
        return [{
            "name": "皮肤检测异常",
            "confidence": 0.3,
            "advice": f"分析出错: {str(e)}",
            "severity": "轻度",
            "body_part": "皮肤"
        }]


def analyze_ears(img_rgb, hsv, gray, height, width, kernel, kernel_large):
    """检测耳道健康状况（改进版）"""
    try:
        # 假设耳朵位于图像上半部分两侧
        ear_y_start = int(height * 0.2)
        ear_y_end = int(height * 0.5)
        left_ear_x_start = int(width * 0.05)
        left_ear_x_end = int(width * 0.25)
        right_ear_x_start = int(width * 0.75)
        right_ear_x_end = int(width * 0.95)

        # 取两侧耳朵区域合并分析
        if left_ear_x_end > left_ear_x_start and right_ear_x_end > right_ear_x_start:
            left_ear = img_rgb[ear_y_start:ear_y_end, left_ear_x_start:left_ear_x_end]
            right_ear = img_rgb[ear_y_start:ear_y_end, right_ear_x_start:right_ear_x_end]

            # 合并区域
            if left_ear.size > 0 and right_ear.size > 0:
                ear_region = np.vstack([left_ear, right_ear]) if left_ear.shape == right_ear.shape else left_ear
            elif left_ear.size > 0:
                ear_region = left_ear
            elif right_ear.size > 0:
                ear_region = right_ear
            else:
                return [{"name": "耳道定位失败", "confidence": 0.3, "advice": "无法定位耳道", "severity": "轻度",
                         "body_part": "耳道"}]
        else:
            return [{"name": "耳道定位失败", "confidence": 0.3, "advice": "无法定位耳道", "severity": "轻度",
                     "body_part": "耳道"}]

        ear_hsv = cv2.cvtColor(ear_region, cv2.COLOR_BGR2HSV)

        # 检测红肿（红色）
        lower_red1 = np.array([0, 50, 50])
        upper_red1 = np.array([10, 255, 255])
        lower_red2 = np.array([170, 50, 50])
        upper_red2 = np.array([180, 255, 255])

        red_mask1 = cv2.inRange(ear_hsv, lower_red1, upper_red1)
        red_mask2 = cv2.inRange(ear_hsv, lower_red2, upper_red2)
        red_mask = cv2.bitwise_or(red_mask1, red_mask2)
        red_ratio = np.sum(red_mask > 0) / red_mask.size if red_mask.size > 0 else 0

        # 检测分泌物（黄褐色）
        lower_discharge = np.array([15, 80, 80])
        upper_discharge = np.array([30, 255, 200])
        discharge_mask = cv2.inRange(ear_hsv, lower_discharge, upper_discharge)
        discharge_ratio = np.sum(discharge_mask > 0) / discharge_mask.size if discharge_mask.size > 0 else 0

        # 降低阈值
        if red_ratio > 0.03 or discharge_ratio > 0.02:  # 原0.04/0.03
            red_conf = min(red_ratio * 6, 0.8)  # 原*5
            discharge_conf = min(discharge_ratio * 10, 0.8)  # 原*8
            confidence = max(red_conf, discharge_conf)

            if red_conf > discharge_conf:
                name = "耳道红肿"
                advice = "耳道红肿，可能有炎症，建议清洁并使用耳药"
                severity = "中度"
            else:
                name = "耳道分泌物"
                advice = "耳道有异常分泌物，可能是感染或耳螨，建议检查"
                severity = "中度"

            return [{
                "name": name,
                "confidence": confidence,
                "advice": advice,
                "severity": severity,
                "body_part": "耳道"
            }]
        else:
            return [{
                "name": "耳道正常",
                "confidence": 0.8,
                "advice": "耳道未见明显异常",
                "severity": "轻度",
                "body_part": "耳道"
            }]
    except Exception as e:
        return [{
            "name": "耳道检测异常",
            "confidence": 0.3,
            "advice": f"分析出错: {str(e)}",
            "severity": "轻度",
            "body_part": "耳道"
        }]


def analyze_vomit(img_rgb, hsv, gray, height, width, kernel, kernel_large, total_pixels):
    """检测图像中是否存在呕吐物（改进版）"""
    try:
        # 呕吐物通常颜色异常（黄、绿、棕），且形状不规则
        # 检测黄绿色区域（可能胆汁）
        lower_yellow_green = np.array([20, 100, 100])
        upper_yellow_green = np.array([40, 255, 255])
        vomit_mask1 = cv2.inRange(hsv, lower_yellow_green, upper_yellow_green)

        # 检测棕色区域（可能食物残渣）
        lower_brown = np.array([10, 100, 50])
        upper_brown = np.array([30, 255, 150])
        vomit_mask2 = cv2.inRange(hsv, lower_brown, upper_brown)

        vomit_mask = cv2.bitwise_or(vomit_mask1, vomit_mask2)
        vomit_mask = cv2.morphologyEx(vomit_mask, cv2.MORPH_CLOSE, kernel_large)

        vomit_percent = np.sum(vomit_mask > 0) / total_pixels

        if vomit_percent > 0.015:  # 原0.02
            confidence = min(vomit_percent * 10, 0.9)  # 原*8
            return [{
                "name": "呕吐物",
                "confidence": confidence,
                "advice": "检测到疑似呕吐物，建议观察宠物是否有呕吐症状，并检查呕吐物颜色和性状",
                "severity": "中度" if confidence > 0.6 else "轻度",
                "body_part": "呕吐物"
            }]
        else:
            return [{
                "name": "未检测到呕吐物",
                "confidence": 0.8,
                "advice": "图像中未发现明显呕吐物",
                "severity": "轻度",
                "body_part": "呕吐物"
            }]
    except Exception as e:
        return [{
            "name": "呕吐物检测异常",
            "confidence": 0.3,
            "advice": f"分析出错: {str(e)}",
            "severity": "轻度",
            "body_part": "呕吐物"
        }]


def analyze_mouth(img_rgb, hsv, gray, height, width, kernel, kernel_large):
    """检测口腔健康状况（改进版）"""
    try:
        # 假设口腔位于图像下半部分中间
        mouth_y_start = int(height * 0.5)
        mouth_y_end = int(height * 0.8)
        mouth_x_start = int(width * 0.3)
        mouth_x_end = int(width * 0.7)

        if mouth_x_end <= mouth_x_start or mouth_y_end <= mouth_y_start:
            return [{"name": "口腔定位失败", "confidence": 0.3, "advice": "无法定位口腔区域", "severity": "轻度",
                     "body_part": "口腔"}]

        mouth_roi = img_rgb[mouth_y_start:mouth_y_end, mouth_x_start:mouth_x_end]
        if mouth_roi.size == 0:
            return [{"name": "口腔区域为空", "confidence": 0.3, "advice": "无法提取口腔区域", "severity": "轻度",
                     "body_part": "口腔"}]

        mouth_hsv = cv2.cvtColor(mouth_roi, cv2.COLOR_BGR2HSV)
        mouth_gray = cv2.cvtColor(mouth_roi, cv2.COLOR_BGR2GRAY)

        # 检测牙龈发红（红色）
        lower_red1 = np.array([0, 50, 50])
        upper_red1 = np.array([10, 255, 255])
        lower_red2 = np.array([170, 50, 50])
        upper_red2 = np.array([180, 255, 255])

        red_mask1 = cv2.inRange(mouth_hsv, lower_red1, upper_red1)
        red_mask2 = cv2.inRange(mouth_hsv, lower_red2, upper_red2)
        red_mask = cv2.bitwise_or(red_mask1, red_mask2)
        red_ratio = np.sum(red_mask > 0) / red_mask.size if red_mask.size > 0 else 0

        # 检测牙结石（黄褐色沉积）
        lower_tartar = np.array([15, 100, 100])
        upper_tartar = np.array([30, 255, 200])
        tartar_mask = cv2.inRange(mouth_hsv, lower_tartar, upper_tartar)
        tartar_ratio = np.sum(tartar_mask > 0) / tartar_mask.size if tartar_mask.size > 0 else 0

        # 检测口腔溃疡（亮红色斑点）
        lower_ulcer = np.array([0, 150, 150])
        upper_ulcer = np.array([10, 255, 255])
        ulcer_mask = cv2.inRange(mouth_hsv, lower_ulcer, upper_ulcer)
        ulcer_ratio = np.sum(ulcer_mask > 0) / ulcer_mask.size if ulcer_mask.size > 0 else 0

        # 降低阈值
        if red_ratio > 0.03 or tartar_ratio > 0.03 or ulcer_ratio > 0.01:  # 原0.05/0.04/0.02
            red_conf = min(red_ratio * 5, 0.8)      # 原*4
            tartar_conf = min(tartar_ratio * 6, 0.8) # 原*5
            ulcer_conf = min(ulcer_ratio * 10, 0.8)  # 原*8

            if ulcer_conf > red_conf and ulcer_conf > tartar_conf:
                name = "口腔溃疡"
                advice = "检测到口腔溃疡，建议软食并就医检查"
                severity = "严重"
                confidence = ulcer_conf
            elif red_conf > tartar_conf:
                name = "牙龈发红"
                advice = "牙龈发红，可能有牙龈炎，建议注意口腔卫生"
                severity = "中度"
                confidence = red_conf
            else:
                name = "牙结石"
                advice = "检测到牙结石，建议洁牙并注意口腔护理"
                severity = "中度"
                confidence = tartar_conf

            return [{
                "name": name,
                "confidence": confidence,
                "advice": advice,
                "severity": severity,
                "body_part": "口腔"
            }]
        else:
            return [{
                "name": "口腔正常",
                "confidence": 0.8,
                "advice": "口腔未见明显异常",
                "severity": "轻度",
                "body_part": "口腔"
            }]
    except Exception as e:
        return [{
            "name": "口腔检测异常",
            "confidence": 0.3,
            "advice": f"分析出错: {str(e)}",
            "severity": "轻度",
            "body_part": "口腔"
        }]


def analyze_feces(img_rgb, hsv, gray, height, width, kernel, kernel_large, total_pixels):
    """检测图像中是否存在排泄物（改进版）"""
    try:
        # 排泄物通常为棕色、黄色、绿色等，可能位于图像底部
        # 检测棕色区域
        lower_brown = np.array([10, 100, 50])
        upper_brown = np.array([30, 255, 150])
        feces_mask1 = cv2.inRange(hsv, lower_brown, upper_brown)

        # 检测黄色区域（可能腹泻）
        lower_yellow = np.array([20, 100, 100])
        upper_yellow = np.array([35, 255, 255])
        feces_mask2 = cv2.inRange(hsv, lower_yellow, upper_yellow)

        # 检测绿色区域（可能胆汁问题）
        lower_green = np.array([35, 100, 100])
        upper_green = np.array([85, 255, 255])
        feces_mask3 = cv2.inRange(hsv, lower_green, upper_green)

        feces_mask = cv2.bitwise_or(feces_mask1, feces_mask2)
        feces_mask = cv2.bitwise_or(feces_mask, feces_mask3)
        feces_mask = cv2.morphologyEx(feces_mask, cv2.MORPH_CLOSE, kernel_large)

        feces_percent = np.sum(feces_mask > 0) / total_pixels

        if feces_percent > 0.015:  # 原0.02
            confidence = min(feces_percent * 10, 0.9)  # 原*8

            # 判断颜色类型
            brown_ratio = np.sum(feces_mask1 > 0) / total_pixels
            yellow_ratio = np.sum(feces_mask2 > 0) / total_pixels
            green_ratio = np.sum(feces_mask3 > 0) / total_pixels

            if green_ratio > yellow_ratio and green_ratio > brown_ratio:
                advice = "检测到绿色排泄物，可能提示胆汁问题或消化异常"
            elif yellow_ratio > brown_ratio:
                advice = "检测到黄色排泄物，可能提示腹泻或消化不良"
            else:
                advice = "检测到棕色排泄物，建议观察性状是否正常"

            return [{
                "name": "排泄物异常",
                "confidence": confidence,
                "advice": advice,
                "severity": "中度",
                "body_part": "排泄物"
            }]
        else:
            return [{
                "name": "未检测到排泄物",
                "confidence": 0.8,
                "advice": "图像中未发现明显排泄物",
                "severity": "轻度",
                "body_part": "排泄物"
            }]
    except Exception as e:
        return [{
            "name": "排泄物检测异常",
            "confidence": 0.3,
            "advice": f"分析出错: {str(e)}",
            "severity": "轻度",
            "body_part": "排泄物"
        }]


# ===== 主分析函数（根据部位调用）=====
def analyze_image_symptoms(image, body_part):
    """根据部位分析图片症状"""
    try:
        img_array = np.array(image)

        if len(img_array.shape) < 3:
            return [{"name": "无效图像", "confidence": 0, "advice": "请上传有效的图片", "severity": "轻度"}]

        # 转换颜色空间
        img_rgb = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
        hsv = cv2.cvtColor(img_rgb, cv2.COLOR_BGR2HSV)
        gray = cv2.cvtColor(img_rgb, cv2.COLOR_BGR2GRAY)

        height, width = gray.shape
        total_pixels = height * width

        kernel = np.ones((3, 3), np.uint8)
        kernel_large = np.ones((5, 5), np.uint8)

        if body_part == "眼睛":
            return analyze_eyes(img_rgb, hsv, gray, height, width, kernel, kernel_large)
        elif body_part == "皮肤":
            return analyze_skin(img_rgb, hsv, gray, height, width, kernel, kernel_large, total_pixels)
        elif body_part == "耳道":
            return analyze_ears(img_rgb, hsv, gray, height, width, kernel, kernel_large)
        elif body_part == "呕吐物":
            return analyze_vomit(img_rgb, hsv, gray, height, width, kernel, kernel_large, total_pixels)
        elif body_part == "口腔":
            return analyze_mouth(img_rgb, hsv, gray, height, width, kernel, kernel_large)
        elif body_part == "排泄物":
            return analyze_feces(img_rgb, hsv, gray, height, width, kernel, kernel_large, total_pixels)
        else:  # 综合
            symptoms = []
            symptoms.extend(analyze_eyes(img_rgb, hsv, gray, height, width, kernel, kernel_large))
            symptoms.extend(analyze_skin(img_rgb, hsv, gray, height, width, kernel, kernel_large, total_pixels))
            symptoms.extend(analyze_ears(img_rgb, hsv, gray, height, width, kernel, kernel_large))
            symptoms.extend(analyze_vomit(img_rgb, hsv, gray, height, width, kernel, kernel_large, total_pixels))
            symptoms.extend(analyze_mouth(img_rgb, hsv, gray, height, width, kernel, kernel_large))
            symptoms.extend(analyze_feces(img_rgb, hsv, gray, height, width, kernel, kernel_large, total_pixels))
            return symptoms
    except Exception as e:
        return [{
            "name": "分析失败",
            "confidence": 0.3,
            "advice": f"图片分析出错: {str(e)}",
            "severity": "轻度"
        }]


# ===== 图片分析类 =====
class PetImageAnalyzer:
    def __init__(self):
        pass

    def analyze(self, image, body_part="综合"):
        """分析宠物图片，指定部位"""
        # 使用增强的图像
        enhanced = self.enhance_image(image)
        symptoms = analyze_image_symptoms(enhanced, body_part)
        return {
            'success': True,
            'symptoms': symptoms,
            'message': f'检测到{len(symptoms)}个症状' if len(symptoms) > 0 else '未检测到明显症状'
        }

    def enhance_image(self, image):
        """图像增强（改进版）"""
        return enhance_image_for_analysis(image)


pet_analyzer = PetImageAnalyzer()


# ===== 生成回答函数 =====
def generate_answer(question):
    if "感冒" in question:
        return """
        **🐕 狗狗感冒的处理建议：**

        1. **保暖措施**：增加垫子，避免吹空调
        2. **饮食调理**：提供温水，易消化食物
        3. **观察症状**：测量体温，注意精神状态
        4. **何时就医**：持续发烧、精神萎靡需就医
        """
    elif "不吃东西" in question:
        return """
        **🐈 猫咪不吃东西的建议：**

        1. 检查食物是否新鲜
        2. 尝试不同口味的罐头
        3. 观察是否有其他症状
        4. 超过24小时需就医
        """
    elif "刷牙" in question:
        return """
        **🦷 宠物刷牙指南：**

        1. 使用宠物专用牙膏
        2. 每周刷牙2-3次
        3. 从小培养习惯
        4. 可配合洁牙零食
        """
    elif "疫苗" in question:
        return """
        **💉 疫苗接种时间表：**

        1. 首年：6-8周第一针
        2. 每3-4周加强一次
        3. 16周后接种狂犬疫苗
        4. 每年加强一次
        """
    elif "饮食" in question:
        return """
        **🍖 宠物饮食建议：**

        1. 选择优质宠物粮
        2. 定时定量喂养
        3. 保证充足饮水
        4. 避免人类食物
        """
    else:
        return f"""
        关于「{question}」的建议：

        1. 建议观察宠物的症状表现
        2. 记录症状出现的时间和频率
        3. 可以上传照片进行智能诊断
        4. 如症状严重请及时就医
        """


# ===== 侧边栏 =====
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

    # ===== 登录区域 =====
    st.markdown("### 🔐 登录")
    if not st.session_state.logged_in:
        col1, col2 = st.columns(2)
        with col1:
            username_input = st.text_input("用户名", key="login_username")
        with col2:
            password_input = st.text_input("密码", type="password", key="login_password")
        if st.button("登录", key="login_btn"):
            # 简单验证：任何用户名密码均可
            if username_input.strip():
                st.session_state.logged_in = True
                st.session_state.username = username_input.strip()
                st.rerun()
            else:
                st.warning("请输入用户名")
    else:
        st.success(f"欢迎, {st.session_state.username}!")
        if st.button("退出", key="logout_btn"):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.rerun()

    st.markdown("---")

    # ===== 朋友互聊区 =====
    st.markdown("### 👥 朋友互聊")
    # 添加朋友
    new_friend = st.text_input("输入朋友名字", key="new_friend")
    if st.button("添加朋友", key="add_friend"):
        if new_friend and new_friend not in st.session_state.friends_list:
            st.session_state.friends_list.append(new_friend)
            st.success(f"已添加 {new_friend}")
        elif new_friend in st.session_state.friends_list:
            st.warning("朋友已存在")

    # 显示朋友列表及私聊输入框
    if st.session_state.friends_list:
        st.markdown("**朋友列表:**")
        for friend in st.session_state.friends_list:
            with st.container():
                st.markdown(f"👤 **{friend}**")
                # 为每个朋友创建一个消息输入框和发送按钮
                msg_key = f"msg_to_{friend}"
                send_key = f"send_to_{friend}"
                msg = st.text_input("", placeholder=f"给{friend}的消息", key=msg_key, label_visibility="collapsed")
                if st.button("发送", key=send_key, use_container_width=True):
                    if msg:
                        # 将消息添加到聊天记录
                        user_msg = f"@{friend} {msg}"
                        st.session_state.messages.append({"role": "user", "content": user_msg})
                        # 模拟回复
                        st.session_state.messages.append({"role": "assistant", "content": f"消息已发送给 {friend}"})
                        st.rerun()
        st.markdown("---")
    else:
        st.info("暂无朋友，添加一些吧")

    st.markdown("---")

    # ===== 城市选择 =====
    st.markdown("### 📍 选择城市")
    current_loc = get_current_location()
    cities = list(CITY_HOSPITALS.keys())
    default_index = cities.index(current_loc['city']) if current_loc['city'] in cities else 0
    selected_city = st.selectbox("城市", options=cities, index=default_index, key="city_selector")
    if "黔南" in selected_city:
        st.info("📍 包含都匀市、福泉市等")
    if selected_city != st.session_state.selected_city:
        st.session_state.selected_city = selected_city
        st.rerun()

    st.markdown("---")

    # ===== 宠物档案 =====
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

    if 'pet_info' in st.session_state:
        with st.expander("📌 当前档案", expanded=False):
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
    selected_color = st.radio(
        "选择主题颜色",
        options=list(color_themes.keys()),
        index=list(color_themes.keys()).index(st.session_state.selected_theme_name),
        key="color_theme_selector"
    )
    if selected_color != st.session_state.selected_theme_name:
        st.session_state.selected_theme_name = selected_color
        st.session_state['theme'] = color_themes[selected_color]
        st.rerun()

    current_theme = color_themes[st.session_state.selected_theme_name]
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            f"<div style='background:{current_theme['primary']}; width:40px; height:40px; border-radius:50%; margin:0 auto;'></div><p style='text-align:center;color:#666;'>主色</p>",
            unsafe_allow_html=True)
    with col2:
        st.markdown(
            f"<div style='background:{current_theme['secondary']}; width:40px; height:40px; border-radius:50%; margin:0 auto;'></div><p style='text-align:center;color:#666;'>辅色</p>",
            unsafe_allow_html=True)
    with col3:
        st.markdown(
            f"<div style='background:{current_theme['primary']}; width:40px; height:40px; border-radius:50%; margin:0 auto; opacity:0.5;'></div><p style='text-align:center;color:#666;'>浅色</p>",
            unsafe_allow_html=True)

    st.markdown("---")

    # ===== 快速查询 =====
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

    st.markdown("---")

    # ===== 当前配置状态 =====
    with st.expander("⚙️ 当前配置状态"):
        st.markdown(f"""
        - **高德地图密钥**: {'✅ 已配置' if AMAP_KEY else '❌ 未配置'}
        - **百度API Key**: {'✅ 已配置' if BAIDU_API_KEY else '❌ 未配置'}
        - **百度Secret Key**: {'✅ 已配置' if BAIDU_SECRET_KEY else '❌ 未配置'}
        - **当前城市**: {st.session_state.get('selected_city', '贵阳市')}
        - **图片分析**: 六部位专业检测
        - **主题颜色**: {st.session_state.selected_theme_name}
        - **登录状态**: {'已登录' if st.session_state.logged_in else '未登录'}
        """)

    st.markdown("---")

    # ===== 清空对话 =====
    if st.button("🗑️ 清空对话", use_container_width=True):
        st.session_state.messages = [
            {"role": "assistant", "content": "你好！我是AI宠物医生。请告诉我你的宠物有什么症状或问题？"}
        ]
        st.rerun()

# ===== 主界面 =====
st.markdown("""
<div class="main-header">
    <h1>🐕 AI宠物医生</h1>
    <p>专业的宠物健康顾问，24小时在线解答</p>
</div>
""", unsafe_allow_html=True)

# ===== 体征识别区域 =====
st.markdown("### 📸 体征识别")
st.markdown("选择要检测的部位，然后上传或拍照")

# 部位选择
body_part_options = ["综合", "眼睛", "皮肤", "耳道", "呕吐物", "口腔", "排泄物"]
selected_body_part = st.radio(
    "选择检测部位",
    options=body_part_options,
    horizontal=True,
    key="body_part_selector"
)

# 图片输入方式
col1, col2 = st.columns(2)

with col1:
    # 文件上传始终显示
    uploaded_file = st.file_uploader(
        "📤 上传照片",
        type=['jpg', 'jpeg', 'png'],
        key="image_uploader",
        help="支持 JPG、PNG 格式"
    )

with col2:
    # 拍照按钮控制相机显示
    if st.button("📷 拍照", key="toggle_camera"):
        st.session_state.show_camera = not st.session_state.show_camera

    if st.session_state.show_camera:
        camera_photo = st.camera_input("点击拍照", key="camera_input")
    else:
        camera_photo = None

# 获取当前图片
current_image = None
current_source = None
if uploaded_file is not None:
    current_image = Image.open(uploaded_file)
    current_source = "上传"
    st.session_state.analysis_result = None  # 新图片清除之前结果
elif camera_photo is not None:
    current_image = Image.open(camera_photo)
    current_source = "拍摄"
    st.session_state.analysis_result = None

# 显示图片（如果有）
if current_image is not None:
    st.image(current_image, caption="当前图片", use_container_width=True)
    st.session_state.analysis_image = current_image
    st.session_state.analysis_source = current_source

    # 分析按钮
    if st.button("🔍 开始分析", type="primary", use_container_width=True, key="analyze_btn"):
        with st.spinner("正在分析图片..."):
            progress_bar = st.progress(0)
            for i in range(100):
                time.sleep(0.01)
                progress_bar.progress(i + 1)

            result = pet_analyzer.analyze(current_image, selected_body_part)
            st.session_state.analysis_result = result
            st.rerun()

# 显示分析结果
if st.session_state.analysis_result is not None:
    result = st.session_state.analysis_result
    current_source = st.session_state.analysis_source

    with st.container():
        if result['success']:
            st.success(f"✅ {result['message']}")
            st.subheader("📊 分析结果")

            severity_icons = {"紧急": "🚨", "严重": "⚠️", "中度": "📋", "轻度": "✅"}

            for symptom in result['symptoms']:
                if symptom['confidence'] > 0.7:
                    tag_class = "symptom-high"
                elif symptom['confidence'] > 0.4:
                    tag_class = "symptom-medium"
                else:
                    tag_class = "symptom-low"

                icon = severity_icons.get(symptom.get('severity', '轻度'), '✅')
                body_part = symptom.get('body_part', '')
                part_display = f"[{body_part}] " if body_part else ""

                st.markdown(f"""
                <div style="margin:15px 0; padding:15px; background:#f8f9fa; border-radius:10px; border-left:4px solid {'#ff0000' if symptom.get('severity') == '紧急' else '#ff9900' if symptom.get('severity') == '严重' else theme['primary']};">
                    <div style="display:flex; align-items:center; margin-bottom:8px; flex-wrap:wrap;">
                        <span class="symptom-tag {tag_class}" style="font-size:1rem;">{icon} {part_display}{symptom['name']}</span>
                        <span style="margin-left:10px; color:#666; font-size:0.9rem;">{symptom['confidence'] * 100:.1f}% 置信度</span>
                        <span style="margin-left:10px; color:{'#ff0000' if symptom.get('severity') == '紧急' else '#ff9900' if symptom.get('severity') == '严重' else '#666'}; font-weight:500; font-size:0.9rem;">
                            {symptom.get('severity', '轻度')}
                        </span>
                    </div>
                    <div style="width:100%; height:8px; background:#e9ecef; border-radius:4px; margin:10px 0;">
                        <div style="width:{symptom['confidence'] * 100}%; height:8px; background:{'#ff0000' if symptom.get('severity') == '紧急' else '#ff9900' if symptom.get('severity') == '严重' else theme['primary']}; border-radius:4px;"></div>
                    </div>
                    <div style="margin-top:10px; color:#666; background:white; padding:10px; border-radius:8px;">
                        💡 <strong>建议：</strong> {symptom['advice']}
                    </div>
                </div>
                """, unsafe_allow_html=True)

            # 生成报告
            report_text = f"""**📋 诊断报告**

**基本信息：**
- 分析时间：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- 图片来源：{current_source}
- 检测部位：{selected_body_part}
- 检测结果：{result['message']}

**检测到的症状：**
{chr(10).join([f'- [{s.get("severity", "轻度")}] {s.get("body_part", "")} {s["name"]}: {s["confidence"] * 100:.1f}%' for s in result['symptoms']])}

**详细建议：**
{chr(10).join([f'- {s["advice"]}' for s in result['symptoms']])}

*注：本分析仅供参考，如有严重症状请及时就医*"""

            st.markdown("---")
            st.markdown("#### 📋 诊断报告详情")
            st.markdown(report_text)

            st.session_state.messages.append({"role": "assistant", "content": report_text})

            if st.button("清除结果", key="clear_result"):
                st.session_state.analysis_result = None
                st.rerun()

st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)

# ===== 聊天历史 =====
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ===== 处理快速查询 =====
if st.session_state.question:
    question = st.session_state.question
    st.session_state.question = None
    with st.chat_message("user"):
        st.markdown(question)
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("assistant"):
        with st.spinner("AI正在思考..."):
            time.sleep(1)
            answer = generate_answer(question)
            st.markdown(answer)
    st.session_state.messages.append({"role": "assistant", "content": answer})

# ===== 文字咨询 =====
st.markdown("### 💬 文字咨询")
prompt = st.chat_input("请输入你的问题...")
if prompt:
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("assistant"):
        with st.spinner("AI正在思考..."):
            time.sleep(1)
            answer = generate_answer(prompt)
            st.markdown(answer)
    st.session_state.messages.append({"role": "assistant", "content": answer})

st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)

# ===== 紧急联系和医院 =====
col1, col2 = st.columns([1, 2])

with col1:
    st.markdown("### 📞 紧急联系")
    current_city = st.session_state.get('selected_city', '贵阳市')
    hospitals = CITY_HOSPITALS.get(current_city, CITY_HOSPITALS['贵阳市'])
    for hospital in hospitals[:2]:
        with st.container():
            st.markdown(f"""
            <div style="background:white; padding:1rem; border-radius:10px; border:1px solid #e9ecef; margin:0.5rem 0; box-shadow:0 2px 5px rgba(0,0,0,0.05);">
                <strong style="color:{theme['primary']};">🏥 {hospital['name']}</strong><br>
                <span style="color:#666;">📍 {hospital['address']}</span><br>
                <span style="color:#666;">📞 {hospital['phone']}</span><br>
                <span style="color:#ff0000; font-weight:bold;">🚑 {hospital['emergency']}</span><br>
                <span style="color:#666;">⏰ {hospital['hours']}</span>
            </div>
            """, unsafe_allow_html=True)
    st.markdown("""
    <div style="margin-top:10px;">
        <a href="https://baike.baidu.com/item/%E5%AE%A0%E7%89%A9%E6%80%A5%E6%95%91" target="_blank" style="text-decoration:none;">
            <div style="background:#f0f0f0; padding:0.5rem; border-radius:8px; text-align:center; color:#666; font-size:0.9rem;">📚 急救指南 →</div>
        </a>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"### 🏥 {current_city}宠物医院")
    for hospital in hospitals:
        with st.expander(f"🏥 {hospital['name']}", expanded=False):
            st.markdown(f"""
            📍 **地址：** {hospital['address']}  
            📞 **电话：** {hospital['phone']}  
            🚑 **急诊：** {hospital['emergency']}  
            ⏰ **营业时间：** {hospital['hours']}
            """)

st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)

# ===== 底部信息 =====
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    <small>⚠️ 免责声明：本应用仅供参考，不能替代专业兽医诊断。如遇紧急情况，请立即联系宠物医院。</small>
    <br>
    <small>📍 支持贵州全省（含都匀市） | 24小时在线问诊 | 六部位专业检测</small>
</div>
""", unsafe_allow_html=True)