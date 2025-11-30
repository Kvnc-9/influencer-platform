import streamlit as st
from supabase import create_client
import pandas as pd
import plotly.express as px
import time
import requests  # YENİ EKLENDİ

# -----------------------------------------------------------------------------
# 1. AYARLAR
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Influencer Insights Platform", layout="wide", page_icon="🚀")

# GÜVENLİK AYARLARI
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    # Webhook URL'sini buraya Secrets'tan da çekebilirsin veya aşağıya elle yazabilirsin.
    # Güvenlik için doğrusu Secrets'tır ama test için aşağıda elle yazacağız.
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
# 2. FONKSİYONLAR
# -----------------------------------------------------------------------------
def trigger_analysis(username):
    """Make.com Webhook'unu tetikler"""
    # BURAYA MAKE.COM'DAN ALDIĞIN URL'Yİ YAPIŞTIR:
    webhook_url = "https://hook.eu1.make.com/ixxd5cuuqkhhkpd8sqn5soiyol0a952x?username=testkullanicisi"
    
    try:
        # Webhook'a username verisini gönderiyoruz
        requests.get(f"{webhook_url}?username={username}")
        return True
    except Exception as e:
        return False

def parse_ai_data(raw_text):
    data = {"Niche": "Genel", "Score": 5, "Brands": "-"}
    if not raw_text: return data
    for line in raw_text.split('\n'):
        if "Niche:" in line: data["Niche"] = line.split("Niche:")[1].strip()
        elif "Score:" in line: 
            try: data["Score"] = int(''.join(filter(str.isdigit, line.split("Score:")[1])))
            except: data["Score"] = 5
        elif "Brands:" in line: data["Brands"] = line.split("Brands:")[1].strip()
    return data

def calculate_metrics(row):
    followers = row.get('follower_count', 0) or 0
    score = row.get('Score', 5)
    est_budget = (followers / 1000) * 10 * (1 + score/10)
    roi = (score * 0.4) + 1.0 
    return pd.Series([est_budget, f"{roi:.1f}x"], index=['Tahmini Bütçe ($)', 'ROI Tahmini'])

# -----------------------------------------------------------------------------
# 3. ARAYÜZ
# -----------------------------------------------------------------------------

# --- GİRİŞ EKRANI ---
if not st.session_state['logged_in']:
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("<br><br><h1 style='text-align: center;'>🔒 Özel Giriş</h1>", unsafe_allow_html=True)
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
    # YAN MENÜ (YENİ ANALİZ EKLEME YERİ)
    with st.sidebar:
        st.title("⚙️ Kontrol Paneli")
        
        st.markdown("### 🕵️ Yeni Analiz Ekle")
        with st.form("new_analysis"):
            new_user = st.text_input("Instagram Kullanıcı Adı", placeholder="Örn: acunilicali")
            btn_analyze = st.form_submit_button("Analizi Başlat 🚀")
            
            if btn_analyze and new_user:
                with st.spinner("Make.com tetikleniyor..."):
                    success = trigger_analysis(new_user)
                    if success:
                        st.success("Analiz talebi gönderildi! 1-2 dakika içinde listeye düşecek.")
                        time.sleep(2) # Mesajı okusun diye bekle
                        st.rerun()
                    else:
                        st.error("Bağlantı hatası oluştu.")
        
        st.markdown("---")
        if st.button("Çıkış Yap"):
            st.session_state['logged_in'] = False
            st.rerun()
            
    # ANA EKRAN
    st.title("🚀 Influencer Analiz Paneli")
    
    response = supabase.table('influencers').select("*").execute()
    
    if response.data:
        df = pd.DataFrame(response.data)
        
        # Veri İşleme
        ai_data = df['ai_analysis_raw'].apply(parse_ai_data).apply(pd.Series)
        df = pd.concat([df, ai_data], axis=1)
        metrics = df.apply(calculate_metrics, axis=1)
        df = pd.concat([df, metrics], axis=1)
        
        # Filtreler
        niche = st.sidebar.multiselect("Kategori", df['Niche'].unique())
        if niche: df = df[df['Niche'].isin(niche)]
        
        # Kartlar
        k1, k2, k3 = st.columns(3)
        k1.metric("Analiz Edilen Profil", len(df))
        k2.metric("Ortalama Skor", f"{df['Score'].mean():.1f}")
        k3.metric("Toplam Erişim", f"{df['follower_count'].sum():,}")
        
        # Tablo
        st.dataframe(df[['username', 'Niche', 'Score', 'Tahmini Bütçe ($)', 'ROI Tahmini']], use_container_width=True)
        
        # Grafik
        fig = px.scatter(df, x="Tahmini Bütçe ($)", y="Score", color="Niche", size="follower_count", hover_name="username")
        st.plotly_chart(fig, use_container_width=True)
        
    else:
        st.info("Henüz veri yok. Sol taraftan yeni bir kullanıcı ekleyin!")
