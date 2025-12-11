import streamlit as st
from supabase import create_client
import pandas as pd
import plotly.express as px
import time
import requests
import json

# -----------------------------------------------------------------------------
# 1. AYARLAR
# -----------------------------------------------------------------------------
st.set_page_config(page_title="CPM Analiz", layout="wide", page_icon="📉")

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
    webhook_url = "https://hook.eu1.make.com/ixxd5cuuqkhhkpd8sqn5soiyol0a952x" 
    try:
        requests.get(f"{webhook_url}?username={username}")
        return True
    except:
        return False

def get_avg_views_from_json(row):
    """JSON paketini açar ve ortalama izlenmeyi bulur"""
    raw_data = row.get('posts_raw_data')
    
    # Veri yoksa 0 dön
    if not raw_data: return 0
    
    try:
        # Supabase bazen string, bazen direkt list verir. İkisini de dene.
        if isinstance(raw_data, str):
            posts = json.loads(raw_data)
        else:
            posts = raw_data
            
        views_list = []
        if isinstance(posts, list):
            for post in posts:
                # Video izlenmesi (Farklı isimlerle gelebilir, hepsini dene)
                views = post.get('videoViewCount') or post.get('playCount') or post.get('viewCount') or 0
                if views > 0:
                    views_list.append(views)
        
        if views_list:
            return int(sum(views_list) / len(views_list))
        else:
            return 0 # Hiç video yoksa 0
            
    except Exception as e:
        return 0 # Hata varsa 0

def calculate_pure_metrics(row, cost_of_ad, total_revenue):
    """CPM ve RPM Hesabı"""
    impressions = row.get('avg_views', 0)
    
    if impressions <= 0:
        return pd.Series([0, 0], index=['CPM ($)', 'RPM ($)'])

    cpm = (cost_of_ad / impressions) * 1000
    rpm = (total_revenue / impressions) * 1000
    
    return pd.Series([cpm, rpm], index=['CPM ($)', 'RPM ($)'])

# -----------------------------------------------------------------------------
# 3. ARAYÜZ
# -----------------------------------------------------------------------------

if not st.session_state['logged_in']:
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.header("🔒 Giriş")
        with st.form("login"):
            email = st.text_input("Kullanıcı")
            password = st.text_input("Şifre", type="password")
            if st.form_submit_button("Giriş Yap"):
                try:
                    supabase.auth.sign_in_with_password({"email": email, "password": password})
                    st.session_state['logged_in'] = True
                    st.rerun()
                except:
                    st.error("Hata")
else:
    with st.sidebar:
        st.header("Ayarlar")
        cost_of_ad = st.number_input("Cost of Ad ($)", value=1000, step=100)
        total_revenue = st.number_input("Total Revenue ($)", value=1500, step=100)
        st.divider()
        new_u = st.text_input("Kullanıcı Adı:")
        if st.button("Analiz Et"):
            if new_u:
                trigger_webhook(new_u)
                st.success("İstek gönderildi.")

    st.title("📊 CPM & RPM Tablosu")

    response = supabase.table('influencers').select("*").execute()
    
    if response.data:
        df = pd.DataFrame(response.data)
        
        # Hesaplamalar
        df['avg_views'] = df.apply(get_avg_views_from_json, axis=1)
        metrics = df.apply(calculate_pure_metrics, args=(cost_of_ad, total_revenue), axis=1)
        df = pd.concat([df, metrics], axis=1)
        
        # TABLO
        st.dataframe(
            df[['username', 'avg_views', 'CPM ($)', 'RPM ($)']].style.format({
                "avg_views": "{:,.0f}",
                "CPM ($)": "${:.2f}",
                "RPM ($)": "${:.2f}"
            }),
            use_container_width=True
        )
        
        # --- 🛠️ HATA TESPİT KUTUSU (DEBUGGER) ---
        st.markdown("---")
        st.error("🛠️ HATA TESPİT ALANI (Geliştirici Modu)")
        
        st.write("Veritabanından gelen son veriyi kontrol ediyoruz...")
        if not df.empty:
            last_user = df.iloc[-1] # Listedeki son kişiyi al
            st.write(f"**Son İncelenen Kişi:** {last_user['username']}")
            st.write(f"**Bulunan Ortalama İzlenme:** {last_user['avg_views']}")
            
            raw = last_user.get('posts_raw_data')
            if not raw:
                st.warning("⚠️ SONUÇ: 'posts_raw_data' kutusu BOŞ! Make.com veriyi Supabase'e yazamıyor.")
                st.info("ÇÖZÜM: Make.com -> Supabase modülünde 'posts_raw_data' eşleştirmesini kontrol et.")
            else:
                st.success("✅ SONUÇ: Veri Paketi (JSON) dolu görünüyor. İçeriği aşağıdadır:")
                st.json(raw) # Gelen paketin içini göster
        
    else:
        st.info("Veri yok.")
