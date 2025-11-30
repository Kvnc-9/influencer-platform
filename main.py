import streamlit as st
from supabase import create_client
import pandas as pd
import plotly.express as px
import time

# -----------------------------------------------------------------------------
# 1. AYARLAR VE GÜVENLİK
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Influencer Insights Platform", layout="wide", page_icon="🚀")

try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except:
    st.error("⚠️ Sunucu ayarları eksik! Secrets ayarlarını kontrol edin.")
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
# 3. WEB SİTESİ ARAYÜZÜ (GÜNCELLENMİŞ GİRİŞ)
# -----------------------------------------------------------------------------

# --- SADECE GİRİŞ EKRANI (Kayıt Ol Yok) ---
if not st.session_state['logged_in']:
    
    # Ortaya Hizalamak için Kolonlar
    col1, col2, col3 = st.columns([1, 1.5, 1])
    
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True) # Biraz boşluk
        st.markdown("<h1 style='text-align: center;'>🔒 Özel Müşteri Girişi</h1>", unsafe_allow_html=True)
        st.info("Bu platforma sadece tanımlanmış üyeler erişebilir.")
        
        # Form Alanı
        with st.form("login_form"):
            email = st.text_input("Kullanıcı Adı (E-Posta)")
            password = st.text_input("Giriş Anahtarı (Şifre)", type="password")
            submit_button = st.form_submit_button("Giriş Yap", use_container_width=True)
            
            if submit_button:
                try:
                    user = supabase.auth.sign_in_with_password({"email": email, "password": password})
                    st.session_state['logged_in'] = True
                    st.success("Giriş Onaylandı! Yönlendiriliyorsunuz...")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error("❌ Erişim Reddedildi: Kullanıcı adı veya şifre hatalı.")

# --- DASHBOARD (Giriş Başarılıysa) ---
else:
    with st.sidebar:
        st.title("⚙️ Panel")
        if st.button("Güvenli Çıkış"):
            st.session_state['logged_in'] = False
            st.rerun()
            
    st.title("🚀 Influencer Analiz Paneli")
    
    # Veri Çekme ve Gösterme Kısmı (Aynı Kalıyor)
    response = supabase.table('influencers').select("*").execute()
    
    if response.data:
        df = pd.DataFrame(response.data)
        ai_data = df['ai_analysis_raw'].apply(parse_ai_data).apply(pd.Series)
        df = pd.concat([df, ai_data], axis=1)
        metrics = df.apply(calculate_metrics, axis=1)
        df = pd.concat([df, metrics], axis=1)
        
        # Filtreler ve Grafikler
        niche = st.sidebar.multiselect("Kategori", df['Niche'].unique())
        if niche: df = df[df['Niche'].isin(niche)]
        
        k1, k2, k3 = st.columns(3)
        k1.metric("Toplam Influencer", len(df))
        k2.metric("Ortalama Puan", f"{df['Score'].mean():.1f}")
        k3.metric("Kitle", f"{df['follower_count'].sum():,}")
        
        st.dataframe(df[['username', 'Niche', 'Score', 'Brands', 'Tahmini Bütçe ($)', 'ROI Tahmini']], use_container_width=True)
        
        fig = px.scatter(df, x="Tahmini Bütçe ($)", y="Score", color="Niche", size="follower_count", hover_name="username", title="Bütçe Analizi")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Veri bulunamadı.")
