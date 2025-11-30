import streamlit as st
from supabase import create_client
import pandas as pd
import plotly.express as px
import time
import requests

# -----------------------------------------------------------------------------
# 1. AYARLAR
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Influencer Insights Platform", layout="wide", page_icon="🚀")

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
# 2. FONKSİYONLAR
# -----------------------------------------------------------------------------
def trigger_analysis(username):
    """Make.com Webhook tetikleyici"""
    # DİKKAT: Buradaki linkin sonunda ?username=... OLMAMALI!
    # Sadece make.com'dan aldığın saf linki yapıştır.
    # Örnek: https://hook.eu2.make.com/Kjd73hd7823hd28
    webhook_url = "https://hook.eu1.make.com/ixxd5cuuqkhhkpd8sqn5soiyol0a952x" 
    
    try:
        # Username parametresini biz burada ekliyoruz
        requests.get(f"{webhook_url}?username={username}")
        return True
    except:
        return False

def parse_ai_data(raw_text):
    data = {"Niche": "Genel", "Score": 0, "Brands": "-"} # Score varsayılan 0
    if not raw_text: return data
    for line in raw_text.split('\n'):
        if "Niche:" in line: data["Niche"] = line.split("Niche:")[1].strip()
        elif "Score:" in line: 
            try: data["Score"] = int(''.join(filter(str.isdigit, line.split("Score:")[1])))
            except: data["Score"] = 0
        elif "Brands:" in line: data["Brands"] = line.split("Brands:")[1].strip()
    return data

def calculate_metrics(row):
    # Takipçi sayısı yoksa hesaplama yapma
    followers = row.get('follower_count', 0)
    if pd.isna(followers) or followers == 0:
        return pd.Series([0, "Veri Yok"], index=['Tahmini Bütçe ($)', 'ROI Tahmini'])

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
        st.markdown("<br><h1 style='text-align: center;'>🔒 Giriş Paneli</h1>", unsafe_allow_html=True)
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
    with st.sidebar:
        st.title("⚙️ İşlemler")
        
        # YENİ KULLANICI EKLEME
        with st.form("new_analysis"):
            st.write("Yeni Analiz Başlat")
            new_user = st.text_input("Instagram Kullanıcı Adı", placeholder="Örn: hadise")
            if st.form_submit_button("Analiz Et 🚀"):
                if new_user:
                    with st.spinner("Make.com tetikleniyor..."):
                        if trigger_analysis(new_user):
                            st.success("İstek gönderildi! 1 dk sonra sayfayı yenileyin.")
                        else:
                            st.error("Bağlantı hatası.")

        st.markdown("---")
        if st.button("Çıkış Yap"):
            st.session_state['logged_in'] = False
            st.rerun()
            
    st.title("🚀 Influencer Analiz Paneli")
    
    # Veriyi Supabase'den Çek
    response = supabase.table('influencers').select("*").execute()
    
    if response.data:
        df = pd.DataFrame(response.data)

        # 1. VERİ TEMİZLİĞİ (GRAFİK PATLAMASIN DİYE)
        # Takipçi sayısını sayıya çevirmeye çalış, olmuyorsa NaN (Boş) bırak
        df['follower_count'] = pd.to_numeric(df['follower_count'], errors='coerce')
        
        # Verileri İşle
        # AI verisi boşsa hata vermesin diye string'e çevir
        df['ai_analysis_raw'] = df['ai_analysis_raw'].fillna("")
        ai_data = df['ai_analysis_raw'].apply(parse_ai_data).apply(pd.Series)
        df = pd.concat([df, ai_data], axis=1)
        
        metrics = df.apply(calculate_metrics, axis=1)
        df = pd.concat([df, metrics], axis=1)
        
        # Filtreler
        if 'Niche' in df.columns:
            niche = st.sidebar.multiselect("Kategori", df['Niche'].unique())
            if niche: df = df[df['Niche'].isin(niche)]
        
        # 2. KPI KARTLARI (Sadece geçerli verileri say)
        # Sadece takipçi sayısı olanları topla
        valid_followers = df['follower_count'].sum()
        
        k1, k2, k3 = st.columns(3)
        k1.metric("Toplam Profil", len(df))
        k2.metric("Ortalama Skor", f"{df['Score'].mean():.1f}")
        k3.metric("Toplam Erişim", f"{valid_followers:,.0f}")
        
        # 3. TABLO (Hepsini Göster - Bozuk veri olsa bile tabloda görünsün)
        st.subheader("📋 Detaylı Liste")
        st.dataframe(df[['username', 'Niche', 'Score', 'Tahmini Bütçe ($)', 'ROI Tahmini']], use_container_width=True)
        
        # 4. GRAFİK (Sadece Verisi SAĞLAM olanları çiz)
        # Bozuk verili satırları grafiğe sokma, yoksa site çöker.
        df_clean = df.dropna(subset=['follower_count', 'Score', 'Tahmini Bütçe ($)'])
        
        if not df_clean.empty:
            st.subheader("📊 Bütçe Analizi")
            fig = px.scatter(
                df_clean, 
                x="Tahmini Bütçe ($)", 
                y="Score", 
                color="Niche", 
                size="follower_count", 
                hover_name="username"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Grafik oluşturmak için yeterli geçerli veri yok (Takipçi sayıları eksik olabilir).")
        
    else:
        st.info("Veri yok.")
