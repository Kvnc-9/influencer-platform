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
# 2. HESAPLAMA MOTORU
# -----------------------------------------------------------------------------
def trigger_analysis(username):
    # SONUNDA ?username= OLMADAN TEMİZ LINK:
    webhook_url = "https://hook.eu1.make.com/ixxd5cuuqkhhkpd8sqn5soiyol0a952x" 
    try:
        requests.get(f"{webhook_url}?username={username}")
        return True
    except:
        return False

def parse_ai_data(raw_text):
    data = {"Niche": "Genel", "Score": 5, "Brands": "-"}
    if not raw_text: return data
    for line in raw_text.split('\n'):
        if "Niche:" in line: data["Niche"] = line.split("Niche:")[1].strip()
        elif "Score:" in line: 
            try: 
                # Sadece rakamları çek
                score_str = ''.join(filter(str.isdigit, line.split("Score:")[1]))
                data["Score"] = int(score_str) if score_str else 5
            except: data["Score"] = 5
        elif "Brands:" in line: data["Brands"] = line.split("Brands:")[1].strip()
    return data

def calculate_metrics(row):
    # 1. Takipçi Sayısını Al (Garanti Sayı)
    followers = row['follower_count']
    
    # 2. Skoru Al (Garanti Sayı)
    score = row['Score']
    
    # Eğer takipçi 0 ise hesaplama yapma
    if followers <= 0:
        return pd.Series([0, "Veri Bekleniyor"], index=['Tahmini Bütçe ($)', 'ROI Tahmini'])

    # 3. HESAPLAMA (MATEMATİK BURADA)
    # Bütçe Formülü: (Takipçi / 1000) * 10$ * (1 + Puan/10)
    est_budget = (followers / 1000) * 10 * (1 + (score / 10))
    
    # ROI Formülü: (Puan * 0.4) + 1
    roi_val = (score * 0.4) + 1.0
    
    return pd.Series([est_budget, f"{roi_val:.1f}x"], index=['Tahmini Bütçe ($)', 'ROI Tahmini'])

# -----------------------------------------------------------------------------
# 3. ARAYÜZ
# -----------------------------------------------------------------------------

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

else:
    with st.sidebar:
        st.title("⚙️ İşlemler")
        with st.form("new_analysis"):
            st.write("Yeni Analiz Başlat")
            new_user = st.text_input("Instagram Kullanıcı Adı", placeholder="Örn: hadise")
            if st.form_submit_button("Analiz Et 🚀"):
                if new_user:
                    with st.spinner("İstek gönderiliyor..."):
                        if trigger_analysis(new_user):
                            st.success("Başarılı! Lütfen bekleyin...")
                        else:
                            st.error("Hata.")
        st.markdown("---")
        if st.button("Çıkış Yap"):
            st.session_state['logged_in'] = False
            st.rerun()
            
    st.title("🚀 Influencer Analiz Paneli")
    
    response = supabase.table('influencers').select("*").execute()
    
    if response.data:
        df = pd.DataFrame(response.data)

        # --- 🛠️ DÜZELTME BÖLÜMÜ (ÖNEMLİ) ---
        
        # 1. Takipçi sayısını sayıya zorla çevir (Hata varsa 0 yap)
        df['follower_count'] = pd.to_numeric(df['follower_count'], errors='coerce').fillna(0)
        
        # 2. AI verisi yoksa boş string yap
        df['ai_analysis_raw'] = df['ai_analysis_raw'].fillna("")
        
        # 3. AI verisini parçala
        ai_data = df['ai_analysis_raw'].apply(parse_ai_data).apply(pd.Series)
        df = pd.concat([df, ai_data], axis=1)
        
        # 4. Skoru sayıya zorla çevir
        df['Score'] = pd.to_numeric(df['Score'], errors='coerce').fillna(5)
        
        # 5. Hesaplamaları Şimdi Yap (Veriler temizlendiği için çalışacak)
        metrics = df.apply(calculate_metrics, axis=1)
        df = pd.concat([df, metrics], axis=1)
        
        # --- 🛠️ BİTİŞ ---

        # KPI Kartları
        k1, k2, k3 = st.columns(3)
        k1.metric("Toplam Profil", len(df))
        k2.metric("Ortalama Skor", f"{df['Score'].mean():.1f}")
        k3.metric("Toplam Erişim", f"{df['follower_count'].sum():,.0f}")
        
        # Tablo
        st.subheader("📋 Detaylı Liste")
        st.dataframe(
            df[['username', 'Niche', 'Score', 'Tahmini Bütçe ($)', 'ROI Tahmini']], 
            use_container_width=True
        )
        
        # Grafik (Sadece verisi olanları çiz)
        df_clean = df[df['follower_count'] > 0] # Sadece takipçisi 0'dan büyük olanlar
        
        if not df_clean.empty:
            fig = px.scatter(
                df_clean, 
                x="Tahmini Bütçe ($)", 
                y="Score", 
                color="Niche", 
                size="follower_count", 
                hover_name="username",
                title="Bütçe vs Kalite"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Grafik için yeterli veri yok.")

        # --- DEBUG ALANI (HATAYI GÖRMEK İÇİN) ---
        with st.expander("🛠️ Geliştirici Veri Kontrolü (Hata Varsa Buraya Bak)"):
            st.write("Supabase'den gelen ham veri:")
            st.write(df.head())
        
    else:
        st.info("Veri yok.")
