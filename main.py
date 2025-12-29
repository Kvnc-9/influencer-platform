import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client, Client
import time

# --- 1. SAYFA KONFİGÜRASYONU ---
st.set_page_config(page_title="Influencer ROI Master", layout="wide", initial_sidebar_state="expanded")

# --- 2. SUPABASE BAĞLANTISI ---
# Hata almamak için try-except bloğu
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error("Supabase bağlantı hatası! Lütfen secrets.toml dosyanızı kontrol edin.")
    st.stop()

# --- 3. CSS TASARIMI (DARK & ORANGE) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700;900&display=swap');
    
    /* Genel Ayarlar */
    .stApp {
        background-color: #0E1117;
        font-family: 'Roboto', sans-serif;
    }
    h1, h2, h3, h4, p, span, div, label {
        color: #FFFFFF !important;
    }
    
    /* LANDING PAGE STİLLERİ */
    .hero-container {
        text-align: center;
        padding: 60px 20px;
        border-radius: 20px;
        background: linear-gradient(180deg, rgba(255, 109, 0, 0.1) 0%, rgba(14, 17, 23, 0) 100%);
        border: 1px solid rgba(255, 109, 0, 0.2);
        margin-bottom: 30px;
    }
    .hero-title {
        font-size: 64px;
        font-weight: 900;
        background: -webkit-linear-gradient(#FF9E80, #FF6D00);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 20px;
    }
    .hero-subtitle {
        font-size: 24px;
        color: #B0B0B0 !important;
        font-weight: 300;
        margin-bottom: 40px;
    }
    .feature-card {
        background-color: #1E1E1E;
        padding: 30px;
        border-radius: 15px;
        border: 1px solid #333;
        text-align: center;
        transition: transform 0.3s;
    }
    .feature-card:hover {
        transform: translateY(-10px);
        border-color: #FF6D00;
    }
    
    /* APP STİLLERİ (Önceki Koddan) */
    div[data-testid="stMetric"] {
        background-color: #1E1E1E;
        border: 1px solid #FF6D00;
        border-radius: 12px;
    }
    div[data-testid="stMetricLabel"] { color: #FF9E80 !important; }
    div[data-testid="stMetricValue"] { color: #FFFFFF !important; }
    .stButton>button {
        background: linear-gradient(90deg, #FF6D00 0%, #FF9100 100%);
        color: white !important;
        border: none;
        border-radius: 8px;
        font-weight: bold;
        transition: 0.3s;
    }
    .stButton>button:hover { opacity: 0.9; transform: scale(1.02); }
    </style>
    """, unsafe_allow_html=True)

# --- 4. OTURUM YÖNETİMİ (SESSION STATE) ---
if 'user' not in st.session_state:
    st.session_state.user = None

# --- 5. FONKSİYONLAR ---

def login_signup_ui():
    """Sidebar'daki Giriş/Kayıt Paneli"""
    st.sidebar.title("🍊 Giriş Yap")
    
    choice = st.sidebar.radio("İşlem Seçin", ["Giriş Yap", "Kayıt Ol"])
    email = st.sidebar.text_input("E-Posta Adresi")
    password = st.sidebar.text_input("Şifre", type="password")

    if choice == "Giriş Yap":
        if st.sidebar.button("Giriş Yap", use_container_width=True):
            try:
                # Supabase Login
                res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                st.session_state.user = res.user
                st.success("Giriş Başarılı!")
                st.rerun()
            except Exception as e:
                st.sidebar.error(f"Giriş Hatası: {e}")
                
    elif choice == "Kayıt Ol":
        if st.sidebar.button("Hesap Oluştur", use_container_width=True):
            try:
                # Supabase Signup
                res = supabase.auth.sign_up({"email": email, "password": password})
                st.sidebar.success("Kayıt başarılı! Lütfen e-postanızı onaylayın veya giriş yapın.")
            except Exception as e:
                st.sidebar.error(f"Kayıt Hatası: {e}")

def logout():
    """Çıkış Yapma Fonksiyonu"""
    supabase.auth.sign_out()
    st.session_state.user = None
    st.rerun()

def show_landing_page():
    """Açılış Sayfası Tasarımı"""
    # Hero Section
    st.markdown("""
        <div class="hero-container">
            <h1 class="hero-title">Influencer ROI Master</h1>
            <p class="hero-subtitle">Bütçenizi boşa harcamayın. Veriye dayalı influencer pazarlama ile maksimum kar elde edin.</p>
        </div>
    """, unsafe_allow_html=True)

    # Özellikler Grid'i
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <h3>📊 Akıllı Analiz</h3>
            <p style="color:#aaa !important;">CPM, RPM ve ROI hesaplamalarını otomatik yapın.</p>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown("""
        <div class="feature-card">
            <h3>🎯 Hedef Odaklı</h3>
            <p style="color:#aaa !important;">Marka uyumu (Alignment) skoruna göre en doğru kişiyi bulun.</p>
        </div>
        """, unsafe_allow_html=True)
        
    with col3:
        st.markdown("""
        <div class="feature-card">
            <h3>🍊 Dark & Modern</h3>
            <p style="color:#aaa !important;">Göz yormayan, kullanıcı dostu ve hızlı arayüz.</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br><br><h3 style='text-align:center; color:#FF6D00 !important;'>Başlamak için soldaki menüden giriş yapın 👈</h3>", unsafe_allow_html=True)

def main_app():
    """Ana Hesaplama Uygulaması (Önceki Kod)"""
    
    # Çıkış Butonu (Sidebar Altı)
    st.sidebar.markdown("---")
    st.sidebar.write(f"Kullanıcı: {st.session_state.user.email}")
    if st.sidebar.button("Çıkış Yap"):
        logout()

    # --- UYGULAMA BAŞLANGICI ---
    st.title("🍊 Influencer ROI Master (Pro Panel)")
    st.write("Hoşgeldiniz. Lütfen kampanya verilerinizi girin.")

    # VERİ SETİ
    def get_initial_data():
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

    # GİRİŞ ALANI
    col_input1, col_input2, col_input3 = st.columns(3)
    with col_input1:
        niche = st.selectbox("Kategori Seçimi", list(get_initial_data().keys()))
    with col_input2:
        total_budget = st.number_input("Toplam Reklam Bütçesi (₺)", min_value=1000, value=100000, step=1000)
    with col_input3:
        product_price = st.number_input("Ürün Satış Fiyatı (₺)", min_value=1, value=500)

    st.markdown("---")

    # MANUEL TIKLANMA GİRİŞİ (DATA EDITOR)
    st.subheader("👇 Sadece Tıklanma Sayılarını Düzenleyin")

    if 'df_data_dark' not in st.session_state or st.session_state.get('current_niche_dark') != niche:
        st.session_state.df_data_dark = pd.DataFrame(get_initial_data()[niche])
        st.session_state.current_niche_dark = niche

    edited_df = st.data_editor(
        st.session_state.df_data_dark,
        column_config={
            "Manuel_Tiklanma": st.column_config.NumberColumn("Manuel Tıklanma (Adet)", min_value=0, step=1, required=True),
            "Avg_Views": st.column_config.NumberColumn("Ort. İzlenme (Sabit)"),
            "Alignment": st.column_config.ProgressColumn("Marka Uyumu", format="%d", min_value=0, max_value=100),
            "Influencer": st.column_config.TextColumn("Influencer")
        },
        disabled=["Influencer", "Avg_Views", "Alignment"],
        use_container_width=True,
        hide_index=True,
        num_rows="fixed"
    )

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("HESAPLAMALARI BAŞLAT"):
        df_calc = edited_df.copy()

        # FORMÜLLER
        total_alignment = df_calc['Alignment'].sum()
        df_calc['Maliyet'] = (df_calc['Alignment'] / total_alignment) * total_budget
        df_calc['CPM'] = (df_calc['Maliyet'] / df_calc['Avg_Views']) * 1000
        df_calc['Gelir'] = df_calc['Manuel_Tiklanma'] * product_price
        df_calc['RPM'] = (df_calc['Gelir'] / df_calc['Avg_Views']) * 1000
        df_calc['Kar'] = df_calc['Gelir'] - df_calc['Maliyet']
        df_calc['ROI (%)'] = (df_calc['Kar'] / df_calc['Maliyet']) * 100

        # SONUÇLAR
        m1, m2, m3 = st.columns(3)
        m1.metric("TOPLAM GELİR", f"₺{df_calc['Gelir'].sum():,.2f}")
        m2.metric("TOPLAM KAR (NET)", f"₺{df_calc['Kar'].sum():,.2f}")
        m3.metric("GENEL ROI ORANI", f"%{df_calc['ROI (%)'].mean():.2f}")

        st.markdown("### 📊 Performans Grafikleri")
        col_graph1, col_graph2 = st.columns(2)
        with col_graph1:
            fig_pie = px.pie(df_calc, values='Maliyet', names='Influencer', title='Bütçe Dağılımı', color_discrete_sequence=px.colors.sequential.Oranges)
            fig_pie.update_layout(paper_bgcolor='#0E1117', plot_bgcolor='#0E1117', font=dict(color='white'))
            st.plotly_chart(fig_pie, use_container_width=True)
        with col_graph2:
            fig_bar = px.bar(df_calc, x='Influencer', y='ROI (%)', title='Influencer ROI (%)', text_auto='.1f', color='ROI (%)', color_continuous_scale='Oranges')
            fig_bar.update_layout(paper_bgcolor='#0E1117', plot_bgcolor='#0E1117', font=dict(color='white'), xaxis_title="", yaxis_title="ROI %")
            st.plotly_chart(fig_bar, use_container_width=True)

        st.markdown("### 📋 Hesaplanan Veriler")
        st.dataframe(df_calc[['Influencer', 'Avg_Views', 'Maliyet', 'CPM', 'Gelir', 'RPM', 'ROI (%)']].style.format({
            'Avg_Views': '{:,.0f}', 'Maliyet': '₺{:,.2f}', 'CPM': '₺{:,.2f}', 'Gelir': '₺{:,.2f}', 'RPM': '₺{:,.2f}', 'ROI (%)': '%{:.2f}'
        }), use_container_width=True)

# --- 6. ANA KONTROL BLOKU ---

if st.session_state.user:
    # KULLANICI GİRİŞ YAPMIŞSA -> ANA UYGULAMAYI GÖSTER
    main_app()
else:
    # KULLANICI GİRİŞ YAPMAMIŞSA -> LANDING PAGE + LOGIN SIDEBAR
    login_signup_ui()
    show_landing_page()
