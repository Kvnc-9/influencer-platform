import streamlit as st
import pandas as pd
import plotly.express as px

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Influencer ROI Calculator", layout="wide")

# --- CSS TASARIMI (KOYU ZEMİN, BEYAZ YAZI, TURUNCU VURGU) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap');
    
    /* Genel Sayfa Yapısı - Koyu Mod */
    .stApp {
        background-color: #0E1117; /* Çok Koyu Gri/Siyah */
        font-family: 'Roboto', sans-serif;
    }
    
    /* Tüm Yazılar Beyaz */
    h1, h2, h3, h4, h5, h6, p, label, span, div {
        color: #FFFFFF !important;
    }
    
    /* Metrik Kartları */
    div[data-testid="stMetric"] {
        background-color: #1E1E1E; /* Kart Rengi */
        border: 1px solid #FF6D00; /* Turuncu Çerçeve */
        border-radius: 12px;
        padding: 15px;
    }
    div[data-testid="stMetricLabel"] {
        color: #FF9E80 !important; /* Açık Turuncu Etiket */
        font-weight: bold;
    }
    div[data-testid="stMetricValue"] {
        color: #FFFFFF !important; /* Değer Beyaz */
        font-weight: 700;
    }

    /* Tablo Tasarımı */
    .stDataFrame {
        border: 1px solid #FF6D00;
    }
    
    /* Buton Tasarımı */
    .stButton>button {
        background: linear-gradient(90deg, #FF6D00 0%, #FF9100 100%);
        color: white !important;
        border: none;
        border-radius: 8px;
        font-weight: bold;
        padding: 15px;
        font-size: 18px;
        width: 100%;
        transition: 0.3s;
    }
    .stButton>button:hover {
        opacity: 0.9;
        transform: scale(1.01);
    }
    
    /* Input Alanları */
    .stNumberInput input {
        color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- VERİ SETİ ---
def get_initial_data():
    return {
        "Beauty": [
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
        "Technology": [
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
        "Wellness & Fitness": [
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

# --- ARAYÜZ ---
st.title("🍊 Influencer Insights Platform ")
st.write("İzlenme verileri otomatik gelir. Sadece tıklanma sayılarını girin ve hesaplayın.")

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
st.subheader("👇 Tıklanma Sayılarını Manuel Giriniz.")

# Veriyi session state'e kaydet
if 'df_data_dark' not in st.session_state or st.session_state.get('current_niche_dark') != niche:
    st.session_state.df_data_dark = pd.DataFrame(get_initial_data()[niche])
    st.session_state.current_niche_dark = niche

# Editable Dataframe (HATA DÜZELTİLDİ: disabled parametresi data_editor içine alındı)
edited_df = st.data_editor(
    st.session_state.df_data_dark,
    column_config={
        "Manuel_Tiklanma": st.column_config.NumberColumn(
            "Manuel Tıklanma (Adet)",
            help="Bu influencer'dan kaç tıklama bekliyorsunuz?",
            min_value=0,
            step=1,
            required=True
        ),
        "Avg_Views": st.column_config.NumberColumn(
            "Ort. İzlenme (Sabit)"
        ),
        "Alignment": st.column_config.ProgressColumn(
            "Marka Uyumu",
            format="%d",
            min_value=0,
            max_value=100
        ),
        "Influencer": st.column_config.TextColumn(
            "Influencer"
        )
    },
    # DÜZELTME BURADA: Düzenlenmesini istemediğimiz sütunları buraya yazıyoruz
    disabled=["Influencer", "Avg_Views", "Alignment"],
    use_container_width=True,
    hide_index=True,
    num_rows="fixed"
)

# HESAPLA BUTONU
st.markdown("<br>", unsafe_allow_html=True)
if st.button("HESAPLAMALARI BAŞLAT"):
    
    # --- HESAPLAMA MOTORU ---
    df_calc = edited_df.copy()

    # 1. Maliyet Dağılımı (Alignment'a göre)
    total_alignment = df_calc['Alignment'].sum()
    df_calc['Maliyet'] = (df_calc['Alignment'] / total_alignment) * total_budget

    # 2. CPM HESABI (OTOMATİK)
    # Formül: CPM = (Maliyet / İzlenme) * 1000
    df_calc['CPM'] = (df_calc['Maliyet'] / df_calc['Avg_Views']) * 1000

    # 3. GELİR HESABI
    # Gelir = Tıklanma * Ürün Fiyatı
    df_calc['Gelir'] = df_calc['Manuel_Tiklanma'] * product_price

    # 4. RPM HESABI (SENİN FORMÜLÜN)
    # RPM = ((Tıklanma x Ürün Fiyatı) / İzlenme) x 1000
    df_calc['RPM'] = (df_calc['Gelir'] / df_calc['Avg_Views']) * 1000

    # 5. ROI HESABI (SENİN FORMÜLÜN)
    # ROI = (Gelir - Maliyet) / Maliyet x 100
    df_calc['Kar'] = df_calc['Gelir'] - df_calc['Maliyet']
    df_calc['ROI (%)'] = (df_calc['Kar'] / df_calc['Maliyet']) * 100

    # --- SONUÇLARIN GÖSTERİMİ ---
    
    # ÖZET METRİKLER
    m1, m2, m3 = st.columns(3)
    m1.metric("TOPLAM GELİR", f"₺{df_calc['Gelir'].sum():,.2f}")
    m2.metric("TOPLAM KAR (NET)", f"₺{df_calc['Kar'].sum():,.2f}")
    m3.metric("GENEL ROI ORANI", f"%{df_calc['ROI (%)'].mean():.2f}")

    st.markdown("### 📊 Performans Grafikleri")
    
    col_graph1, col_graph2 = st.columns(2)
    
    with col_graph1:
        # Bütçe Pastası
        fig_pie = px.pie(df_calc, values='Maliyet', names='Influencer', 
                         title='Bütçe Dağılımı (Maliyet)',
                         color_discrete_sequence=px.colors.sequential.Oranges)
        # Koyu moda uygun grafik ayarları
        fig_pie.update_layout(
            paper_bgcolor='#0E1117',
            plot_bgcolor='#0E1117',
            font=dict(color='white')
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_graph2:
        # ROI Bar Grafiği
        fig_bar = px.bar(df_calc, x='Influencer', y='ROI (%)',
                         title='Influencer Bazlı ROI (%)',
                         text_auto='.1f',
                         color='ROI (%)',
                         color_continuous_scale='Oranges')
        fig_bar.update_layout(
            paper_bgcolor='#0E1117',
            plot_bgcolor='#0E1117',
            font=dict(color='white'),
            xaxis_title="", yaxis_title="ROI %"
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    # DETAYLI SONUÇ TABLOSU
    st.markdown("### 📋 Hesaplanan Veriler")
    st.dataframe(
        df_calc[['Influencer', 'Avg_Views', 'Maliyet', 'CPM', 'Gelir', 'RPM', 'ROI (%)']].style.format({
            'Avg_Views': '{:,.0f}',
            'Maliyet': '₺{:,.2f}',
            'CPM': '₺{:,.2f}',
            'Gelir': '₺{:,.2f}',
            'RPM': '₺{:,.2f}',
            'ROI (%)': '%{:.2f}'
        }),
        use_container_width=True
    )

    # FORMÜL KONTROL KUTUSU (ŞEFFAFLIK)
    st.markdown("""
    <div style="background-color: #1E1E1E; padding: 15px; border-radius: 10px; border: 1px solid #FF6D00; color: white;">
        <strong>✅ KULLANILAN FORMÜLLER:</strong><br>
        1. <b>CPM:</b> (Maliyet / İzlenme) x 1.000 <br>
        2. <b>RPM:</b> ((Tıklanma x Fiyat) / İzlenme) x 1.000 <br>
        3. <b>ROI:</b> (Gelir - Maliyet) / Maliyet x 100
    </div>
    """, unsafe_allow_html=True)
