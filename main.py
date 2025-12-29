import streamlit as st
import pandas as pd
import plotly.express as px
import time

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Influencer ROI Master", layout="wide", initial_sidebar_state="collapsed")

# --- SESSION STATE (OTURUM DURUMU) ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# --- CSS TASARIMI (DARK & ORANGE) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700;900&display=swap');
    
    .stApp { background-color: #0E1117; font-family: 'Roboto', sans-serif; }
    h1, h2, h3, h4, p, span, div, label { color: #FFFFFF !important; }
    
    /* LANDING PAGE */
    .hero-container {
        text-align: center; padding: 80px 20px;
        background: radial-gradient(circle, rgba(255,109,0,0.15) 0%, rgba(14,17,23,0) 70%);
        border-bottom: 1px solid #333; margin-bottom: 40px;
    }
    .hero-title {
        font-size: 72px; font-weight: 900;
        background: -webkit-linear-gradient(#FF9E80, #FF6D00);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .hero-subtitle { font-size: 24px; color: #B0B0B0 !important; font-weight: 300; }
    
    /* LOGIN KUTUSU */
    .login-box {
        background-color: #1E1E1E; padding: 30px; border-radius: 15px;
        border: 1px solid #FF6D00; max-width: 400px; margin: 0 auto;
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

# --- FONKSİYONLAR ---

def login_function():
    """Giriş Kontrolü (Basit Simülasyon)"""
    st.markdown("<div class='hero-container'><h1 class='hero-title'>Influencer ROI Master</h1><p class='hero-subtitle'>Gelişmiş Analitik Platformu</p></div>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,1,1])
    with col2:
        st.info("Deneme için -> Kullanıcı: admin | Şifre: 1234")
        user_input = st.text_input("Kullanıcı Adı")
        pass_input = st.text_input("Şifre", type="password")
        
        if st.button("Giriş Yap", use_container_width=True):
            if user_input == "admin" and pass_input == "1234":
                st.session_state.logged_in = True
                st.success("Giriş Başarılı!")
                time.sleep(0.5)
                st.rerun()
            else:
                st.error("Hatalı kullanıcı adı veya şifre!")

def main_app():
    """Ana Hesaplama Uygulaması"""
    
    # Çıkış Butonu
    with st.sidebar:
        st.write("👤 **Admin**")
        if st.button("Çıkış Yap"):
            st.session_state.logged_in = False
            st.rerun()

    st.title("🍊 Hesaplama Paneli")
    
    # --- VERİ SETİ ---
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
            # Diğer kategoriler buraya eklenebilir...
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

# --- 2. SAYFA KONTROLÜ ---
if st.session_state.logged_in:
    main_app()
else:
    login_function()
