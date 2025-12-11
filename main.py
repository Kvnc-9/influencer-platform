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
st.set_page_config(page_title="CPM/RPM Calculator", layout="wide", page_icon="🧮")

st.markdown("""
<style>
    .big-font { font-size: 16px !important; }
    div[data-testid="stMetricValue"] { font-size: 24px; }
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
# 2. VERİ MOTORU (JSON TAMİR EDİCİ EKLENDİ)
# -----------------------------------------------------------------------------

def trigger_webhook(username):
    webhook_url = "https://hook.eu1.make.com/ixxd5cuuqkhhkpd8sqn5soiyol0a952x" 
    try:
        requests.get(f"{webhook_url}?username={username}")
        return True
    except:
        return False

def safe_json_parse(raw_data):
    """
    🛠️ ÖZEL TAMİR FONKSİYONU
    Gelen veri {..}, {..} şeklindeyse bunu [{..}, {..}] şekline çevirir.
    """
    if not raw_data: return []
    
    # Zaten listeyse direkt döndür
    if isinstance(raw_data, list): return raw_data
    
    # String değilse boş dön
    if not isinstance(raw_data, str): return []

    try:
        # Önce normal deneme yap
        return json.loads(raw_data)
    except json.JSONDecodeError:
        try:
            # Hata verdiyse, başına ve sonuna köşeli parantez ekleyip dene
            # Bu işlem senin hatanı çözen kısımdır.
            fixed_data = f"[{raw_data}]"
            return json.loads(fixed_data)
        except:
            return [] # Yine de olmazsa boş dön

def get_avg_views_from_json(row):
    """Ortalama izlenmeyi hesaplar"""
    raw_data = row.get('posts_raw_data')
    posts = safe_json_parse(raw_data) # Tamirciyi kullan

    views_list = []
    if posts and isinstance(posts, list):
        for post in posts:
            # Video izlenmesi (Farklı isimlerle gelebilir)
            views = post.get('videoViewCount') or post.get('playCount') or post.get('viewCount') or 0
            # Eğer 0'dan büyükse ve type Video ise veya views varsa al
            if views > 0:
                views_list.append(views)

    if views_list:
        return int(sum(views_list) / len(views_list))
    else:
        return 0

def calculate_pure_metrics(row, cost_of_ad, total_revenue):
    """Saf CPM ve RPM Hesabı"""
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
        if st.button("Veri Çek"):
            if new_u:
                trigger_webhook(new_u)
                st.success("İstek gönderildi.")
        
        st.divider()
        if st.button("Çıkış"):
            st.session_state['logged_in'] = False
            st.rerun()

    st.title("📊 CPM & RPM Tablosu")

    response = supabase.table('influencers').select("*").execute()
    
    if response.data:
        df = pd.DataFrame(response.data)
        
        # 1. İzlenmeleri Hesapla (Artık Hata Vermez)
        df['avg_views'] = df.apply(get_avg_views_from_json, axis=1)
        
        # 2. Metrikleri Hesapla
        metrics = df.apply(calculate_pure_metrics, args=(cost_of_ad, total_revenue), axis=1)
        df = pd.concat([df, metrics], axis=1)
        
        # Tablo
        df_display = df.sort_values(by='CPM ($)', ascending=True)
        
        st.dataframe(
            df_display[['username', 'avg_views', 'CPM ($)', 'RPM ($)']].style.format({
                "avg_views": "{:,.0f}",
                "CPM ($)": "${:.2f}",
                "RPM ($)": "${:.2f}"
            }),
            use_container_width=True,
            height=500
        )
        
        # Grafikler
        df_chart = df[df['avg_views'] > 0]
        if not df_chart.empty:
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("CPM (Maliyet)")
                fig = px.bar(df_chart, x='username', y='CPM ($)', color='CPM ($)', text_auto='.2f')
                st.plotly_chart(fig, use_container_width=True)
            with c2:
                st.subheader("RPM (Gelir)")
                fig2 = px.bar(df_chart, x='username', y='RPM ($)', color='RPM ($)', text_auto='.2f')
                st.plotly_chart(fig2, use_container_width=True)
        
        # --- HATA KONTROLÜ (Son Durum) ---
        with st.expander("🛠️ Veri Kontrolü"):
            if not df.empty:
                last_user = df.iloc[-1]
                st.write(f"Son Kişi: {last_user['username']}")
                st.write(f"Hesaplanan Ortalama İzlenme: {last_user['avg_views']}")
                if last_user['avg_views'] > 0:
                    st.success("✅ Veri başarıyla okundu ve hesaplandı!")
                else:
                    st.warning("⚠️ İzlenme hala 0 görünüyor. Kullanıcının son postlarında video olmayabilir.")

    else:
        st.info("Veri yok.")
