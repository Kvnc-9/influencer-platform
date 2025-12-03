import streamlit as st
from supabase import create_client
import pandas as pd
import plotly.express as px
import time
import requests
import json
import math

# -----------------------------------------------------------------------------
# 1. AYARLAR VE GÜVENLİK
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Influencer CPM/RPM Pro", layout="wide", page_icon="📊")

# CSS: Kart Görünümleri
st.markdown("""
<style>
    .metric-card {
        background-color: #f9f9f9;
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 15px;
        text-align: center;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except:
    st.error("⚠️ Secrets ayarları eksik! Lütfen Streamlit panelinden API anahtarlarını girin.")
    st.stop()

@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# -----------------------------------------------------------------------------
# 2. VERİ ANALİZ MOTORU
# -----------------------------------------------------------------------------

def trigger_webhook(username):
    # DİKKAT: Buraya kendi Make.com Webhook URL'ini yapıştır.
    # Sonunda ?username= OLMASIN. Temiz link olsun.
    webhook_url = "https://hook.eu2.make.com/BURAYA_SENIN_MAKE_LINKIN" 
    try:
        requests.get(f"{webhook_url}?username={username}")
        return True
    except:
        return False

def analyze_posts_json(row):
    """
    Supabase'den gelen JSON verisini açar, Video İzlenmelerini ve Yorumları çeker.
    """
    raw_data = row.get('posts_raw_data')
    stats = {
        "avg_views": 0, 
        "total_likes": 0, 
        "comment_quality": "Veri Yok", 
        "top_comment_likes": 0,
        "video_count": 0
    }
    
    # Veri boşsa veya hatalıysa boş dön
    if not raw_data: return pd.Series(stats)
    
    try:
        # Veri string (yazı) olarak geldiyse JSON'a çevir
        posts = json.loads(raw_data) if isinstance(raw_data, str) else raw_data
    except:
        return pd.Series(stats)

    views_list = []
    max_comment_likes = 0
    total_likes = 0
    
    # Liste içinde dön (Her bir post için)
    if isinstance(posts, list):
        for post in posts:
            # 1. Sadece Videoların İzlenmesini Al
            views = post.get('videoViewCount') or post.get('playCount') or 0
            if views > 0:
                views_list.append(views)
            
            # 2. Toplam Beğeni
            total_likes += post.get('likesCount', 0)
            
            # 3. Yorum Analizi
            comments = post.get('previewComments', []) or post.get('latestComments', [])
            if isinstance(comments, list):
                for c in comments:
                    c_likes = c.get('likesCount', 0)
                    if c_likes > max_comment_likes: max_comment_likes = c_likes

    # Ortalamaları Hesapla
    if views_list:
        stats["avg_views"] = int(sum(views_list) / len(views_list))
        stats["video_count"] = len(views_list)
    
    stats["total_likes"] = total_likes
    stats["top_comment_likes"] = max_comment_likes
    
    # Yorum Kalite Etiketi
    if max_comment_likes >= 100: stats["comment_quality"] = "🔥 Yüksek (Topluluk Güçlü)"
    elif max_comment_likes > 20: stats["comment_quality"] = "✅ Orta Seviye"
    else: stats["comment_quality"] = "⚠️ Düşük Etkileşim"
        
    return pd.Series(stats)

def calculate_financials(row, base_cpm_input, platform_fee_percent):
    """
    CPM ve RPM Hesaplama - Matematiksel Hata Korumalı
    Formül: CPM = (Maliyet / İzlenme) * 1000
    """
    # 1. Gösterim (Impressions) Belirle
    views = row.get('avg_views', 0)
    
    # Eğer hiç video yoksa, Takipçi sayısının %10'unu izlenme varsay (Tahmini)
    is_estimated = False
    if views == 0:
        views = row.get('follower_count', 0) * 0.10
        is_estimated = True
    
    # Sıfıra bölme hatasını engellemek için minimum 1 yapıyoruz
    impressions = max(views, 1) 

    score = row.get('Score', 5)

    # --- CPM HESAPLAMA ---
    # Kullanıcının girdiği "Base CPM" (Örn: 5$) * Kalite Çarpanı
    # Puan 10 ise fiyat 1.5 katına çıkar. Puan 0 ise 0.5 katına düşer.
    quality_multiplier = 0.5 + (score / 10) 
    final_cpm = base_cpm_input * quality_multiplier
    
    # Reklam Maliyeti (Ad Cost) = (İzlenme / 1000) * CPM
    estimated_ad_cost = (impressions / 1000) * final_cpm

    # --- RPM HESAPLAMA (GELİR) ---
    # Influencer'ın cebine giren para.
    # Platform kesintisi düşülür.
    creator_share = 1 - (platform_fee_percent / 100)
    final_rpm = final_cpm * creator_share
    
    estimated_revenue = (impressions / 1000) * final_rpm
    
    return pd.Series([estimated_ad_cost, estimated_revenue, final_cpm, final_rpm, is_estimated], 
                     index=['Ad_Cost', 'Est_Revenue', 'CPM', 'RPM', 'Is_Estimated'])

# -----------------------------------------------------------------------------
# 3. ARAYÜZ (FRONTEND)
# -----------------------------------------------------------------------------

# --- GİRİŞ EKRANI ---
if not st.session_state['logged_in']:
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("<br><h1 style='text-align: center;'>🔒 B2B Giriş Paneli</h1>", unsafe_allow_html=True)
        with st.form("login"):
            email = st.text_input("Kullanıcı Adı")
            password = st.text_input("Şifre", type="password")
            if st.form_submit_button("Giriş Yap", use_container_width=True):
                try:
                    supabase.auth.sign_in_with_password({"email": email, "password": password})
                    st.session_state['logged_in'] = True
                    st.rerun()
                except:
                    st.error("Giriş Başarısız")

# --- DASHBOARD ---
else:
    # --- YAN MENÜ (DİNAMİK AYARLAR) ---
    with st.sidebar:
        st.title("⚙️ Pazar Ayarları")
        st.info("Formüller buradaki değerlere göre çalışır.")
        
        # Kullanıcı Girdileri
        base_cpm_input = st.number_input("Sektör Baz CPM ($)", value=5.0, min_value=0.1, step=0.5, help="1000 izlenme için ortalama Pazar Fiyatı")
        platform_fee = st.
