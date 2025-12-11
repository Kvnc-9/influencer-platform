import streamlit as st
from supabase import create_client
import pandas as pd
import plotly.express as px
import requests
import json

# -----------------------------------------------------------------------------
# 1. AYARLAR VE GÜVENLİK
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Influencer Fiyat Hesaplayıcı", layout="wide", page_icon="💰")

# Tablo Görünümü İyileştirme
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
# 2. VERİ MOTORU
# -----------------------------------------------------------------------------

def trigger_webhook(username):
    webhook_url = "https://hook.eu1.make.com/ixxd5cuuqkhhkpd8sqn5soiyol0a952x" 
    try:
        requests.get(f"{webhook_url}?username={username}")
        return True
    except:
        return False

def safe_json_parse(raw_data):
    """JSON Tamirci"""
    if not raw_data: return []
    if isinstance(raw_data, list): return raw_data
    if not isinstance(raw_data, str): return []
    try:
        return json.loads(raw_data)
    except json.JSONDecodeError:
        try:
            return json.loads(f"[{raw_data}]")
        except:
            return []

def get_avg_views_from_json(row):
    """Ortalama İzlenme Hesabı"""
    raw_data = row.get('posts_raw_data')
    posts = safe_json_parse(raw_data)

    views_list = []
    if posts and isinstance(posts, list):
        for post in posts:
            views = post.get('videoViewCount') or post.get('playCount') or post.get('viewCount') or 0
            if views > 0:
                views_list.append(views)

    if views_list:
        return int(sum(views_list) / len(views_list))
    else:
        return 0

def calculate_budget_offer(row, target_cpm, total_revenue_goal):
    """
    1. Önerilen Teklif (Budget): (İzlenme / 1000) * Hedef CPM
    2. RPM: (Toplam Gelir Hedefi / İzlenme) * 1000
    """
    impressions = row.get('avg_views', 0)
    
    if impressions <= 0:
        return pd.Series([0, 0], index=['Önerilen Teklif ($)', 'RPM ($)'])

    # --- 1. ÖNERİLEN VİDEO FİYATI (BUDGET) ---
    # Markanın hedeflediği CPM'e göre Influencer'ın hak ettiği para
    recommended_offer = (impressions / 1000) * target_cpm
    
    # --- 2. RPM (GELİR VERİMLİLİĞİ) ---
    # Eğer bu kampanya hedeflenen ciroyu yaparsa verimlilik ne olur?
    rpm = (total_revenue_goal / impressions) * 1000
    
    return pd.Series([recommended_offer, rpm], index=['Önerilen Teklif ($)', 'RPM ($)'])

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
        st.header("💰 Bütçe Planlayıcı")
        st.info("Influencer'a ne kadar ödemelisin?")
        
        # 1. KULLANICI GİRDİSİ: Hedef CPM
        target_cpm = st.number_input("Hedeflediğiniz CPM ($)", value=5.0, step=0.5, help="1000 izlenme başına ödemeye razı olduğunuz tutar. (Piyasa ortalaması 5$-10$)")
        
        # 2. KULLANICI GİRDİSİ: Hedef Ciro
        total_revenue = st.number_input("Hedeflenen Toplam Ciro ($)", value=2000, step=100, help="Bu videodan kazanmayı umduğunuz toplam para.")
        
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

    st.title("💸 Adil Fiyat Hesaplayıcı")
    st.markdown(f"""
    Bu analiz, belirlediğiniz **${target_cpm} CPM** (Birim Fiyat) üzerinden, 
    her bir Influencer'a **video başına ne kadar teklif vermeniz gerektiğini** hesaplar.
    """)

    response = supabase.table('influencers').select("*").execute()
    
    if response.data:
        df = pd.DataFrame(response.data)
        
        # Hesaplamalar
        df['avg_views'] = df.apply(get_avg_views_from_json, axis=1)
        metrics = df.apply(calculate_budget_offer, args=(target_cpm, total_revenue), axis=1)
        df = pd.concat([df, metrics], axis=1)
        
        # --- TABLO ---
        df_valid = df[df['avg_views'] > 0].copy()
        
        if not df_valid.empty:
            # En yüksek tekliften düşüğe sırala
            df_valid = df_valid.sort_values(by="Önerilen Teklif ($)", ascending=False)
            
            st.subheader("📋 Kime Ne Kadar Ödemelisiniz?")
            st.dataframe(
                df_valid[['username', 'avg_views', 'Önerilen Teklif ($)', 'RPM ($)']].style.format({
                    "avg_views": "{:,.0f}",
                    "Önerilen Teklif ($)": "${:,.2f}",
                    "RPM ($)": "${:.2f}"
                }),
                use_container_width=True,
                height=500
            )
            
            # GRAFİK: Fiyat vs Performans
            st.subheader("📊 Fiyat Analizi")
            
            

            fig = px.scatter(
                df_valid, 
                x="avg_views", 
                y="Önerilen Teklif ($)", 
                size="Önerilen Teklif ($)", 
                hover_name="username",
                title=f"${target_cpm} CPM Hedefiyle Fiyat Dağılımı",
                labels={"avg_views": "Ortalama İzlenme", "Önerilen Teklif ($)": "Video Başına Bütçe"}
            )
            st.plotly_chart(fig, use_container_width=True)
            
        else:
            st.warning("Video verisi yok.")
    else:
        st.info("Veri yok.")
