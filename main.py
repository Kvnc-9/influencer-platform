import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client, Client
import time

# --- 1. SAYFA VE CSS AYARLARI ---
st.set_page_config(page_title="Influencer ROI Master", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700;900&display=swap');
    
    .stApp { background-color: #0E1117; font-family: 'Roboto', sans-serif; }
    h1, h2, h3, h4, p, span, div, label { color: #FFFFFF !important; }
    
    /* LANDING PAGE CSS (Buranın göründüğünden emin olalım) */
    .hero-container {
        text-align: center;
        padding: 100px 20px;
        background: radial-gradient(circle at center, rgba(255, 109, 0, 0.2) 0%, rgba(14, 17, 23, 0) 70%);
        border-bottom: 1px solid #333;
        margin-bottom: 30px;
        animation: fadeIn 1.5s ease-in;
    }
    .hero-title {
        font-size: 80px;
        font-weight: 900;
        background: -webkit-linear-gradient(#FF9E80, #FF6D00);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 20px;
    }
    .hero-subtitle {
        font-size: 26px;
        color: #B0B0B0 !important;
        font-weight: 300;
        max-width: 800px;
        margin: 0 auto;
    }
    
    /* Özellik Kartları */
    .feature-grid {
        display: flex;
        justify-content: center;
        gap: 30px;
        margin-top: 50px;
    }
    .feature-card {
        background-color: #1E1E1E;
        padding: 40px;
        border-radius: 20px;
        border: 1px solid #333;
        text-align: center;
        width: 300px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }
    
    @keyframes fadeIn {
        0% { opacity: 0; transform: translateY(20px); }
        100% { opacity: 1; transform: translateY(0); }
    }
    
    /* APP STİLLERİ */
    div[data-testid="stMetric"] { background-color: #1E1E1E; border: 1px solid #FF6D00; border-radius: 12px; }
    div[data-testid="stMetricLabel"] { color: #FF9E80 !important; }
    div[data-testid="stMetricValue"] { color: #FFFFFF !important; }
    .stButton>button {
        background: linear-gradient(90deg, #FF6D00 0%, #FF9100 100%);
        color: white !important; border: none; border-radius: 8px; font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. SUPABASE BAĞLANTISI ---
# Session State Tanımlama
if 'user' not in st.session_state:
    st.session_state.user = None

try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error("Supabase bağlantı hatası! .streamlit/secrets.toml dosyasını kontrol et.")
    st.stop()

# --- 3. FONKSİYONLAR ---

def show_landing_page():
    """KARŞILAMA EKRANI (LANDING PAGE)"""
    st.markdown("""
        <div class="hero-container">
            <h1 class="hero-title">Influencer ROI Master</h1>
            <p class="hero-subtitle">Milyonluk bütçeleri şansa bırakma. Yapay zeka destekli analiz ile her kuruşun hesabını sor.</p>
        </div>
        
        <div class="feature-grid">
            <div class="feature-card">
                <h3>🚀 Hızlı Analiz</h3>
                <p style="color:#aaa !important; font-size:14px;">Saniyeler içinde 10'larca influencer verisini işle.</p>
            </div>
            <div class="feature-card">
                <h3>💰 ROI Odaklı</h3>
                <p style="color:#aaa !important; font-size:14px;">Sadece takipçiye değil, karlılığa odaklan.</p>
            </div>
            <div class="feature-card">
                <h3>🔒 Güvenli Veri</h3>
                <p style="color:#aaa !important; font-size:14px;">Kampanya verilerin Supabase ile güvende.</p>
            </div>
        </div>
        
        <div style="text-align:center; margin-top:50px; padding:20px; background-color:#1E1E1E; border-radius:10px; max-width:600px; margin-left:auto; margin-right:auto;">
            <h4 style="color:#FF6D00 !important;">Nasıl Başlarım?</h4>
            <p style="color:#fff !important;">Sol taraftaki menüyü açarak <b>Giriş Yap</b> veya <b>Kayıt Ol</b> butonlarını kullanın.</p>
        </div>
    """, unsafe_allow_html=True)

def login_sidebar():
    """SOL MENÜDEKİ GİRİŞ FORMU"""
    st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3069/3069172.png", width=80)
    st.sidebar.title("🍊 Giriş Paneli")
    
    choice = st.sidebar.radio("İşlem", ["Giriş Yap", "Kayıt Ol"])
    email = st.sidebar.text_input("E-Posta")
    password = st.sidebar.text_input("Şifre", type="password")
    
    if choice == "Giriş Yap":
        if st.sidebar.button("Giriş Yap", use_container_width=True):
            try:
                res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                st.session_state.user = res.user
                st.success("Başarılı! Yönlendiriliyorsunuz...")
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.sidebar.error(f"Hata: {e}")
                
    elif choice == "Kayıt Ol":
        if st.sidebar.button("Kayıt Ol", use_container_width=True):
            try:
                res = supabase.auth.sign_up({"email": email, "password": password})
                st.sidebar.success("Kayıt olundu! Giriş yapabilirsiniz.")
            except Exception as e:
                st.sidebar.error(f"Hata: {e}")

def main_app():
    """ANA HESAPLAMA UYGULAMASI (GİRİŞ YAPILINCA AÇILIR)"""
    
    # Çıkış Butonu
    st.sidebar.title("Hesabım")
    st.sidebar.write(f"📧 {st.session_state.user.email}")
    if st.sidebar.button("Çıkış Yap", type="primary"):
        supabase.auth.sign_out()
        st.session_state.user = None
        st.rerun()

    st.title("🍊 Hesaplama Paneli")
    st.info("İzlenme verileri otomatik gelir, sadece 'Manuel Tıklanma'yı girin.")

    # --- VERİ SETİ (Kısaltılmış örnek, seninkiyle aynı kalacak) ---
    def get_data():
        return {
             "Beauty & Güzellik": [
            {"Influencer": "Merve Özkaynak", "Alignment": 96, "Avg_Views": 550000, "Manuel_Tiklanma": 500},
            {"Influencer": "Duygu Özaslan", "Alignment": 85, "Avg_Views": 380000, "Manuel_Tiklanma": 450},
            {"Influencer": "Danla Bilic", "Alignment": 70, "Avg_Views": 1500000, "Manuel_Tiklanma": 1200},
            {"Influencer": "Sebi Bebi", "Alignment": 92, "Avg_Views": 120000, "Manuel_Tiklanma": 300},
            {"Influencer": "Polen Sarıca", "Alignment": 90, "Avg_Views": 65000, "Manuel_Tiklanma": 250},
            {"Influencer": "Görkem Karman", "Alignment": 94, "Avg_Views": 110000, "Manuel_Tiklanma": 350},
            {"Influencer": "Aslı Çıra", "Alignment": 91, "Avg_Views": 85000, "Manuel_Tiklanma": 200},
            {"Influencer": "Ayşenur Yazıcı", "Alignment": 98, "Avg_Views": 45000, "Manuel_Tiklanma": 150},
            {"Influencer": "Damla Kalaycık", "Alignment": 88, "Avg_Views": 190000, "Manuel_Tiklanma": 400},
            {"Influencer": "Ceren Ceyhun", "Alignment": 89, "Avg_Views": 40000, "Manuel_Tiklanma": 180},
            ],
             "Teknoloji": [
            {"Influencer": "Hakkı Alkan", "Alignment": 95, "Avg_Views": 450000, "Manuel_Tiklanma": 800},
            {"Influencer": "Mesut Çevik", "Alignment": 98, "Avg_Views": 180000, "Manuel_Tiklanma": 400},
            {"Influencer": "Barış Özcan", "Alignment": 90, "Avg_Views": 2500000, "Manuel_Tiklanma": 2500},
            {"Influencer": "Can Değer", "Alignment": 99, "Avg_Views": 95000, "Manuel_Tiklanma": 300},
            {"Influencer": "Enis Kirazoğlu", "Alignment": 85, "Avg_Views": 850000, "Manuel_Tiklanma": 1500},
            {"Influencer": "Webtekno", "Alignment": 80, "Avg_Views": 700000, "Manuel_Tiklanma": 1800},
            {"Influencer": "iPhonedo", "Alignment": 94, "Avg_Views": 350000, "Manuel_Tiklanma": 600},
            {"Influencer": "ShiftDelete", "Alignment": 82, "Avg_Views": 600000, "Manuel_Tiklanma": 1000},
            {"Influencer": "Donanım Arşivi", "Alignment": 92, "Avg_Views": 400000, "Manuel_Tiklanma": 750},
            {"Influencer": "Technopat", "Alignment": 96, "Avg_Views": 150000, "Manuel_Tiklanma": 350},
            ],
             "Wellness & Spor": [
            {"Influencer": "Ece Vahapoğlu", "Alignment": 98, "Avg_Views": 85000, "Manuel_Tiklanma": 200},
            {"Influencer": "Elvin Levinler", "Alignment": 92, "Avg_Views": 420000, "Manuel_Tiklanma": 600},
            {"Influencer": "Tuğçe İnce", "Alignment": 94, "Avg_Views": 55000, "Manuel_Tiklanma": 150},
            {"Influencer": "Cansu Yeğin", "Alignment": 90, "Avg_Views": 70000, "Manuel_Tiklanma": 180},
            {"Influencer": "Dilara Koçak", "Alignment": 100, "Avg_Views": 110000, "Manuel_Tiklanma": 400},
            {"Influencer": "Ebru Şallı", "Alignment": 85, "Avg_Views": 380000, "Manuel_Tiklanma": 900},
            {"Influencer": "Çetin Çetintaş", "Alignment": 97, "Avg_Views": 190000, "Manuel_Tiklanma": 350},
            {"Influencer": "Murat Bür", "Alignment": 88, "Avg_Views": 45000, "Manuel_Tiklanma": 120},
            {"Influencer": "Aysun Bekcan", "Alignment": 91, "Avg_Views": 35000, "Manuel_Tiklanma": 100},
            {"Influencer": "Polat Özdemir", "Alignment": 89, "Avg_Views": 28000, "Manuel_Tiklanma": 110},
            ]
        }

    # APP LOGIC
    c1, c2, c3 = st.columns(3)
    with c1: niche = st.selectbox("Kategori", list(get_data().keys()))
    with c2: budget = st.number_input("Bütçe (₺)", 1000, 1000000, 100000)
    with c3: price = st.number_input("Ürün Fiyatı (₺)", 1, 100000, 500)

    st.divider()

    if 'df_main' not in st.session_state or st.session_state.get('niche_main') != niche:
        st.session_state.df_main = pd.DataFrame(get_data()[niche])
        st.session_state.niche_main = niche

    edited = st.data_editor(
        st.session_state.df_main,
        column_config={
            "Manuel_Tiklanma": st.column_config.NumberColumn("Manuel Tıklanma", required=True),
            "Avg_Views": st.column_config.NumberColumn("Ort. İzlenme"),
            "Alignment": st.column_config.ProgressColumn("Uyum", format="%d", min_value=0, max_value=100)
        },
        disabled=["Influencer", "Avg_Views", "Alignment"],
        use_container_width=True,
        hide_index=True
    )

    if st.button("HESAPLA", use_container_width=True):
        df = edited.copy()
        # Formüller
        total_align = df['Alignment'].sum()
        df['Maliyet'] = (df['Alignment'] / total_align) * budget
        df['CPM'] = (df['Maliyet'] / df['Avg_Views']) * 1000
        df['Gelir'] = df['Manuel_Tiklanma'] * price
        df['RPM'] = (df['Gelir'] / df['Avg_Views']) * 1000
        df['Kar'] = df['Gelir'] - df['Maliyet']
        df['ROI (%)'] = (df['Kar'] / df['Maliyet']) * 100
        
        # Sonuçlar
        m1, m2, m3 = st.columns(3)
        m1.metric("TOPLAM GELİR", f"₺{df['Gelir'].sum():,.0f}")
        m2.metric("TOPLAM KAR", f"₺{df['Kar'].sum():,.0f}")
        m3.metric("GENEL ROI", f"%{df['ROI (%)'].mean():.1f}")
        
        g1, g2 = st.columns(2)
        with g1:
            st.plotly_chart(px.pie(df, values='Maliyet', names='Influencer', title='Bütçe Dağılımı', hole=0.4), use_container_width=True)
        with g2:
            st.plotly_chart(px.bar(df, x='Influencer', y='ROI (%)', title='ROI Sıralaması', color='ROI (%)'), use_container_width=True)
        
        st.dataframe(df)

# --- 4. ANA KONTROL MERKEZİ (FLOW CONTROL) ---

if st.session_state.user is not None:
    # 1. Durum: Kullanıcı Giriş Yapmış -> Ana Uygulamayı Göster
    main_app()
else:
    # 2. Durum: Kullanıcı Yok -> Landing Page + Login Sidebar Göster
    login_sidebar()     # Sidebar'da formu göster
    show_landing_page() # Ana ekranda Landing Page'i göster
