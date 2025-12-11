import streamlit as st
from supabase import create_client
import pandas as pd
import plotly.express as px
import time
import requests
import json

# -----------------------------------------------------------------------------
# 1. AYARLAR VE GÜVENLİK
# -----------------------------------------------------------------------------
st.set_page_config(page_title="CPM/RPM Analiz", layout="wide", page_icon="📉")

# Tablo yazı boyutunu büyütme ve ortalama
st.markdown("""
<style>
    .big-font { font-size: 16px !important; }
    div[data-testid="stMetricValue"] { font-size: 24px; }
    thead tr th:first-child {display:none}
    tbody th {display:none}
</style>
""", unsafe_allow_html=True)

try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except:
    st.error("⚠️ Secrets ayarları eksik!")
    st.stop()

@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# -----------------------------------------------------------------------------
# 2. VERİ MOTORU
# -----------------------------------------------------------------------------

def trigger_webhook(username):
    # DİKKAT: BURAYA KENDİ MAKE.COM WEBHOOK LİNKİNİ YAPIŞTIR
    # Soru işareti (?) olmadan temiz link olmalı
    webhook_url = "https://hook.eu1.make.com/ixxd5cuuqkhhkpd8sqn5soiyol0a952x" 
    try:
        requests.get(f"{webhook_url}?username={username}")
        return True
    except:
        return False

def get_avg_views_from_json(row):
    """JSON'dan izlenme verisini çeker, yoksa 0 döndürür"""
    raw_data = row.get('posts_raw_data')
    if not raw_data: return 0
    
    try:
        posts = json.loads(raw_data) if isinstance(raw_data, str) else raw_data
    except:
        return 0

    views_list = []
    if isinstance(posts, list):
        for post in posts:
            views = post.get('videoViewCount') or post.get('playCount') or 0
            if views > 0: views_list.append(views)

    if views_list:
        return int(sum(views_list) / len(views_list))
    else:
        return 0

def calculate_pure_metrics(row, cost_of_ad, total_revenue):
    """Saf CPM ve RPM Hesabı"""
    impressions = row.get('avg_views', 0)
    
    # Veri yoksa veya 0 ise hesaplama yapma (0 döndür)
    if impressions <= 0:
        return pd.Series([0, 0], index=['CPM ($)', 'RPM ($)'])

    # Formüller
    cpm = (cost_of_ad / impressions) * 1000
    rpm = (total_revenue / impressions) * 1000
    
    return pd.Series([cpm, rpm], index=['CPM ($)', 'RPM ($)'])

# -----------------------------------------------------------------------------
# 3. ARAYÜZ
# -----------------------------------------------------------------------------

# --- GİRİŞ EKRANI ---
if not st.session_state['logged_in']:
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.header("🔒 Giriş")
        with st.form("login"):
            email = st.text_input("Kullanıcı Adı")
            password = st.text_input("Şifre", type="password")
            if st.form_submit_button("Giriş Yap", use_container_width=True):
                try:
                    supabase.auth.sign_in_with_password({"email": email, "password": password})
                    st.session_state['logged_in'] = True
                    st.rerun()
                except:
                    st.error("Hatalı Giriş")

# --- DASHBOARD ---
else:
    # YAN MENÜ
    with st.sidebar:
        st.header("Ayarlar")
        cost_of_ad = st.number_input("Cost of Ad ($)", value=1000, step=100)
        total_revenue = st.number_input("Total Revenue ($)", value=1500, step=100)
        
        st.divider()
        st.subheader("Yeni Kişi Ekle")
        new_u = st.text_input("Kullanıcı Adı:")
        if st.button("Analiz Et"):
            if new_u:
                trigger_webhook(new_u)
                st.success("İstek gönderildi.")
        
        st.divider()
        if st.button("Çıkış"):
            st.session_state['logged_in'] = False
            st.rerun()

    # ANA EKRAN
    st.title("📊 CPM & RPM Tablosu")

    # Veriyi Çek
    response = supabase.table('influencers').select("*").execute()
    
    if response.data:
        df = pd.DataFrame(response.data)
        
        # 1. İzlenmeleri Hesapla
        df['avg_views'] = df.apply(get_avg_views_from_json, axis=1)
        
        # 2. Metrikleri Hesapla
        metrics = df.apply(calculate_pure_metrics, args=(cost_of_ad, total_revenue), axis=1)
        df = pd.concat([df, metrics], axis=1)
        
        # --- TABLOYU GÖSTER (FİLTRE YOK, HEPSİNİ GÖSTERİR) ---
        
        # Gösterilecek sütunları seç ve isimlendir
        display_df = df[['username', 'avg_views', 'CPM ($)', 'RPM ($)']].copy()
        display_df.columns = ['Kullanıcı Adı', 'Ort. İzlenme (Impression)', 'CPM ($)', 'RPM ($)']
        
        # CPM'e göre sırala (0 olanlar en sona gitsin diye mantık kurabiliriz ama şimdilik düz sıralayalım)
        display_df = display_df.sort_values(by='CPM ($)', ascending=True)

        # Tabloyu Bas
        st.dataframe(
            display_df.style.format({
                "Ort. İzlenme (Impression)": "{:,.0f}",
                "CPM ($)": "${:.2f}",
                "RPM ($)": "${:.2f}"
            }),
            use_container_width=True,
            height=500
        )
        
        # --- GRAFİKLER (Sadece Verisi Olanları Çiz - Yoksa Hata Verir) ---
        df_chart = df[df['avg_views'] > 0]
        
        if not df_chart.empty:
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("CPM Maliyeti (Düşük İyidir)")
                fig = px.bar(df_chart, x='username', y='CPM ($)', color='CPM ($)', text_auto='.2f')
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.subheader("RPM Geliri (Yüksek İyidir)")
                fig2 = px.bar(df_chart, x='username', y='RPM ($)', color='RPM ($)', text_auto='.2f')
                st.plotly_chart(fig2, use_container_width=True)
    else:
        st.warning("Veri bulunamadı. Supabase tablosu boş olabilir.")
