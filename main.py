import streamlit as st
from supabase import create_client
import pandas as pd
import plotly.express as px
import time

# -----------------------------------------------------------------------------
# 1. AYARLAR VE GÜVENLİK (Secrets'tan Okur)
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Influencer Insights Platform", layout="wide", page_icon="🚀")

# Bağlantı Hatası Kontrolü: Şifreleri Streamlit Cloud'dan alır
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except:
    st.error("⚠️ Sunucu ayarları eksik! Lütfen Streamlit panelinden 'Secrets' kısmına API anahtarlarını girin.")
    st.stop()

# Supabase Bağlantısını Başlat
@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

# Oturum Kontrolü (Giriş yapıldı mı?)
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# -----------------------------------------------------------------------------
# 2. HESAPLAMA MOTORU (ROI & Bütçe)
# -----------------------------------------------------------------------------
def parse_ai_data(raw_text):
    """AI verisini parçalar"""
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
    """Bütçe ve ROI Hesaplar"""
    followers = row.get('follower_count', 0) or 0
    score = row.get('Score', 5)
    
    # Basit bir Bütçe Formülü: (Takipçi / 1000) * 10$ * Kalite Çarpanı
    est_budget = (followers / 1000) * 10 * (1 + score/10)
    
    # ROI Tahmini: Puan yüksekse ROI yüksek
    roi = (score * 0.4) + 1.0  # Örn: 8 puan -> 4.2x ROI
    
    return pd.Series([est_budget, f"{roi:.1f}x"], index=['Tahmini Bütçe ($)', 'ROI Tahmini'])

# -----------------------------------------------------------------------------
# 3. WEB SİTESİ ARAYÜZÜ
# -----------------------------------------------------------------------------

# --- GİRİŞ EKRANI ---
if not st.session_state['logged_in']:
    st.markdown("<h1 style='text-align: center;'>🔒 Influencer Insights Platform</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>B2B Analiz Paneline Hoşgeldiniz</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        tab1, tab2 = st.tabs(["Giriş Yap", "Kayıt Ol"])
        
        # GİRİŞ SEKMESİ
        with tab1:
            email = st.text_input("E-Posta")
            password = st.text_input("Şifre", type="password")
            if st.button("Giriş Yap", use_container_width=True):
                try:
                    user = supabase.auth.sign_in_with_password({"email": email, "password": password})
                    st.session_state['logged_in'] = True
                    st.success("Giriş başarılı! Yönlendiriliyorsunuz...")
                    time.sleep(1)
                    st.rerun()
                except:
                    st.error("Hatalı e-posta veya şifre.")

        # KAYIT SEKMESİ
        with tab2:
            reg_email = st.text_input("Kayıt E-Posta")
            reg_pass = st.text_input("Kayıt Şifre", type="password")
            if st.button("Kayıt Ol", use_container_width=True):
                try:
                    supabase.auth.sign_up({"email": reg_email, "password": reg_pass})
                    st.success("Kayıt başarılı! Şimdi 'Giriş Yap' sekmesinden girebilirsiniz.")
                except Exception as e:
                    st.error(f"Kayıt hatası: {e}")

# --- DASHBOARD (Giriş Yapıldıysa Görünecek Kısım) ---
else:
    with st.sidebar:
        st.title("⚙️ Yönetim Paneli")
        if st.button("Çıkış Yap"):
            st.session_state['logged_in'] = False
            st.rerun()
            
    st.title("🚀 Influencer Analiz Paneli")
    st.markdown("Yapay zeka destekli ROI ve Bütçe tahminleri.")
    st.markdown("---")
    
    # Veriyi Çek
    response = supabase.table('influencers').select("*").execute()
    
    if response.data:
        df = pd.DataFrame(response.data)
        
        # Verileri İşle (AI Metnini Parçala + Hesaplama Yap)
        ai_data = df['ai_analysis_raw'].apply(parse_ai_data).apply(pd.Series)
        df = pd.concat([df, ai_data], axis=1)
        metrics = df.apply(calculate_metrics, axis=1)
        df = pd.concat([df, metrics], axis=1)
        
        # Filtreleme Menüsü
        niche = st.sidebar.multiselect("Kategori Filtrele", df['Niche'].unique())
        if niche: df = df[df['Niche'].isin(niche)]
        
        # KPI Kartları (En Üstteki Sayılar)
        k1, k2, k3 = st.columns(3)
        k1.metric("Toplam Influencer", len(df))
        k2.metric("Ortalama Kalite Puanı", f"{df['Score'].mean():.1f}/10")
        k3.metric("Toplam Takipçi Kitlesi", f"{df['follower_count'].sum():,}")
        
        # Ana Tablo
        st.subheader("📋 Detaylı Analiz Listesi")
        st.dataframe(
            df[['username', 'Niche', 'Score', 'Brands', 'Tahmini Bütçe ($)', 'ROI Tahmini']], 
            use_container_width=True
        )
        
        # Grafikler
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Bütçe vs Kalite")
            fig = px.scatter(df, x="Tahmini Bütçe ($)", y="Score", color="Niche", size="follower_count", hover_name="username")
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            st.subheader("Kategori Dağılımı")
            fig2 = px.pie(df, names='Niche')
            st.plotly_chart(fig2, use_container_width=True)
        
    else:
        st.warning("Veritabanında henüz veri yok. Lütfen önce Make.com otomasyonunu çalıştırın.")