import streamlit as st
import pandas as pd
import plotly.express as px

# --- SAYFA YAPILANDIRMASI ---
st.set_page_config(page_title="Influencer ROI Calculator", layout="wide")

# --- CUSTOM CSS (BEYAZ, TURUNCU, SİYAH YAZI) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Roboto', sans-serif;
        background-color: #FFFFFF; /* Arka Plan Beyaz */
        color: #000000; /* Yazılar Siyah */
    }
    
    /* Metrik Kartları */
    div[data-testid="stMetric"] {
        background-color: #FFF3E0; /* Çok Açık Turuncu */
        border: 2px solid #FF9800; /* Turuncu Çerçeve */
        border-radius: 10px;
        padding: 15px;
        color: #000000;
    }
    div[data-testid="stMetricLabel"] {
        color: #E65100; /* Koyu Turuncu Etiket */
        font-weight: bold;
    }
    div[data-testid="stMetricValue"] {
        color: #000000;
        font-weight: 700;
    }

    /* Tablo Başlıkları ve Hücreleri */
    .stDataFrame {
        border: 1px solid #FF9800;
    }

    /* Buton Tasarımı */
    .stButton>button {
        background-color: #FF6D00; /* Canlı Turuncu */
        color: white; /* Buton yazısı beyaz (okunabilirlik için) */
        border: none;
        border-radius: 8px;
        font-weight: bold;
        padding: 15px;
        font-size: 18px;
        width: 100%;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #E65100;
        color: white;
    }
    
    /* Başlıklar */
    h1, h2, h3 {
        color: #000000 !important;
    }
    
    /* Sidebar (Varsa) veya Üst Input Alanları */
    .stNumberInput label, .stSelectbox label {
        color: #000000 !important;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# --- VERİ SETİ ---
def get_initial_data():
    return {
        "Beauty & Güzellik": [
            {"Influencer": "Merve Özkaynak", "Alignment": 96, "Base_CPM": 55, "Manuel_Tiklanma": 500},
            {"Influencer": "Duygu Özaslan", "Alignment": 85, "Base_CPM": 65, "Manuel_Tiklanma": 450},
            {"Influencer": "Danla Bilic", "Alignment": 70, "Base_CPM": 50, "Manuel_Tiklanma": 1200},
            {"Influencer": "Sebi Bebi", "Alignment": 92, "Base_CPM": 60, "Manuel_Tiklanma": 300},
            {"Influencer": "Polen Sarıca", "Alignment": 90, "Base_CPM": 35, "Manuel_Tiklanma": 250},
            {"Influencer": "Görkem Karman", "Alignment": 94, "Base_CPM": 40, "Manuel_Tiklanma": 350},
            {"Influencer": "Aslı Çıra", "Alignment": 91, "Base_CPM": 38, "Manuel_Tiklanma": 200},
            {"Influencer": "Ayşenur Yazıcı", "Alignment": 98, "Base_CPM": 55, "Manuel_Tiklanma": 150},
            {"Influencer": "Damla Kalaycık", "Alignment": 88, "Base_CPM": 48, "Manuel_Tiklanma": 400},
            {"Influencer": "Ceren Ceyhun", "Alignment": 89, "Base_CPM": 30, "Manuel_Tiklanma": 180},
        ],
        "Teknoloji": [
            {"Influencer": "Hakkı Alkan", "Alignment": 95, "Base_CPM": 80, "Manuel_Tiklanma": 800},
            {"Influencer": "Mesut Çevik", "Alignment": 98, "Base_CPM": 90, "Manuel_Tiklanma": 400},
            {"Influencer": "Barış Özcan", "Alignment": 90, "Base_CPM": 150, "Manuel_Tiklanma": 2500},
            {"Influencer": "Can Değer", "Alignment": 99, "Base_CPM": 100, "Manuel_Tiklanma": 300},
            {"Influencer": "Enis Kirazoğlu", "Alignment": 85, "Base_CPM": 70, "Manuel_Tiklanma": 1500},
            {"Influencer": "Webtekno", "Alignment": 80, "Base_CPM": 60, "Manuel_Tiklanma": 1800},
            {"Influencer": "iPhonedo", "Alignment": 94, "Base_CPM": 110, "Manuel_Tiklanma": 600},
            {"Influencer": "ShiftDelete", "Alignment": 82, "Base_CPM": 65, "Manuel_Tiklanma": 1000},
            {"Influencer": "Donanım Arşivi", "Alignment": 92, "Base_CPM": 85, "Manuel_Tiklanma": 750},
            {"Influencer": "Technopat", "Alignment": 96, "Base_CPM": 95, "Manuel_Tiklanma": 350},
        ],
        "Wellness & Spor": [
            {"Influencer": "Ece Vahapoğlu", "Alignment": 98, "Base_CPM": 40, "Manuel_Tiklanma": 200},
            {"Influencer": "Elvin Levinler", "Alignment": 92, "Base_CPM": 55, "Manuel_Tiklanma": 600},
            {"Influencer": "Tuğçe İnce", "Alignment": 94, "Base_CPM": 30, "Manuel_Tiklanma": 150},
            {"Influencer": "Cansu Yeğin", "Alignment": 90, "Base_CPM": 35, "Manuel_Tiklanma": 180},
            {"Influencer": "Dilara Koçak", "Alignment": 100, "Base_CPM": 50, "Manuel_Tiklanma": 400},
            {"Influencer": "Ebru Şallı", "Alignment": 85, "Base_CPM": 65, "Manuel_Tiklanma": 900},
            {"Influencer": "Çetin Çetintaş", "Alignment": 97, "Base_CPM": 45, "Manuel_Tiklanma": 350},
            {"Influencer": "Murat Bür", "Alignment": 88, "Base_CPM": 25, "Manuel_Tiklanma": 120},
            {"Influencer": "Aysun Bekcan", "Alignment": 91, "Base_CPM": 20, "Manuel_Tiklanma": 100},
            {"Influencer": "Polat Özdemir", "Alignment": 89, "Base_CPM": 22, "Manuel_Tiklanma": 110},
        ]
    }

# --- ARAYÜZ ---
st.title("🍊 Influencer ROI & Bütçe Hesaplayıcı")
st.write("Verileri girin, tıklanma sayılarını düzenleyin ve kesin formüllerle sonucu görün.")

# GİRİŞ ALANI (TEK EKRAN ÜST KISIM)
col_input1, col_input2, col_input3 = st.columns(3)

with col_input1:
    niche = st.selectbox("Kategori Seçimi", list(get_initial_data().keys()))
with col_input2:
    total_budget = st.number_input("Toplam Reklam Bütçesi (₺)", min_value=1000, value=100000, step=1000)
with col_input3:
    product_price = st.number_input("Ürün Satış Fiyatı (₺)", min_value=1, value=500)

st.markdown("---")

# MANUEL TIKLANMA GİRİŞİ (DATA EDITOR)
st.subheader("👇 Tıklanma Sayılarını Buradan Düzenleyin")
st.info("Aşağıdaki tablodaki 'Manuel_Tiklanma' sütununa her influencer için beklediğiniz tıklama sayısını giriniz.")

# Veriyi çek ve session state'e kaydet (düzenleme için)
if 'df_data' not in st.session_state or st.session_state.get('current_niche') != niche:
    st.session_state.df_data = pd.DataFrame(get_initial_data()[niche])
    st.session_state.current_niche = niche

# Editable Dataframe (Kullanıcı Tıklamaları Elle Girer)
edited_df = st.data_editor(
    st.session_state.df_data,
    column_config={
        "Manuel_Tiklanma": st.column_config.NumberColumn(
            "Manuel Tıklanma (Adet)",
            help="Bu influencer'dan kaç tıklama/satış bekliyorsunuz?",
            min_value=0,
            step=1,
            required=True
        ),
        "Alignment": st.column_config.ProgressColumn(
            "Marka Uyumu",
            format="%d",
            min_value=0,
            max_value=100,
        ),
        "Base_CPM": "CPM Maliyeti (₺)"
    },
    use_container_width=True,
    hide_index=True,
    num_rows="fixed"
)

# HESAPLA BUTONU
if st.button("HESAPLAMALARI BAŞLAT"):
    
    # --- SENİN FORMÜLLERİNE GÖRE HESAPLAMA ---
    df_calc = edited_df.copy()

    # 1. Bütçe Dağılımı (Alignment Ağırlıklı)
    total_alignment = df_calc['Alignment'].sum()
    df_calc['Maliyet (Cost)'] = (df_calc['Alignment'] / total_alignment) * total_budget

    # 2. Gösterim Sayısı (Impressions)
    # Formül Tersi: CPM = (Cost / Impressions) * 1000  => Impressions = (Cost / CPM) * 1000
    df_calc['Impressions'] = (df_calc['Maliyet (Cost)'] / df_calc['Base_CPM']) * 1000

    # 3. Gelir (Revenue)
    # Gelir = Tıklanma Sayısı * Ürün Fiyatı (Kullanıcının isteği üzerine)
    df_calc['Gelir (Revenue)'] = df_calc['Manuel_Tiklanma'] * product_price

    # 4. RPM HESABI (SENİN FORMÜLÜN)
    # RPM = ((Tıklanma x Ürün Fiyatı) / Impressions) x 1000
    df_calc['RPM'] = ((df_calc['Manuel_Tiklanma'] * product_price) / df_calc['Impressions']) * 1000

    # 5. ROI HESABI (SENİN FORMÜLÜN)
    # ROI = (Gelir - Maliyet) / Maliyet x 100
    # Not: (Kar) = (Gelir - Maliyet) olduğu için formül aslında matematiksel olarak aynıdır.
    df_calc['Kar (Profit)'] = df_calc['Gelir (Revenue)'] - df_calc['Maliyet (Cost)']
    df_calc['ROI (%)'] = (df_calc['Kar (Profit)'] / df_calc['Maliyet (Cost)']) * 100

    # --- SONUÇLARIN GÖSTERİMİ ---
    
    # ÖZET METRİKLER
    m1, m2, m3 = st.columns(3)
    m1.metric("TOPLAM GELİR", f"₺{df_calc['Gelir (Revenue)'].sum():,.2f}")
    m2.metric("TOPLAM KAR (NET)", f"₺{df_calc['Kar (Profit)'].sum():,.2f}")
    m3.metric("GENEL ROI", f"%{df_calc['ROI (%)'].mean():.2f}")

    st.markdown("### 📊 Grafiksel Dağılım")
    
    col_graph1, col_graph2 = st.columns(2)
    
    with col_graph1:
        # Bütçe Pastası
        fig_pie = px.pie(df_calc, values='Maliyet (Cost)', names='Influencer', 
                         title='Bütçe Dağılımı (Maliyet)',
                         color_discrete_sequence=px.colors.sequential.Oranges)
        fig_pie.update_layout(paper_bgcolor='rgba(0,0,0,0)', font=dict(color='black'))
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_graph2:
        # ROI Bar Grafiği
        fig_bar = px.bar(df_calc, x='Influencer', y='ROI (%)',
                         title='Influencer Bazlı ROI Başarısı (%)',
                         text_auto='.1f',
                         color='ROI (%)',
                         color_continuous_scale='Oranges')
        fig_bar.update_layout(paper_bgcolor='rgba(0,0,0,0)', font=dict(color='black'), xaxis_title="", yaxis_title="ROI %")
        st.plotly_chart(fig_bar, use_container_width=True)

    # DETAYLI SONUÇ TABLOSU
    st.markdown("### 📋 Kesin Sonuç Tablosu")
    st.dataframe(
        df_calc[['Influencer', 'Manuel_Tiklanma', 'Impressions', 'Maliyet (Cost)', 'Gelir (Revenue)', 'RPM', 'ROI (%)']].style.format({
            'Impressions': '{:,.0f}',
            'Maliyet (Cost)': '₺{:,.2f}',
            'Gelir (Revenue)': '₺{:,.2f}',
            'RPM': '₺{:,.2f}',
            'ROI (%)': '%{:.2f}'
        }),
        use_container_width=True
    )

    # FORMÜL KONTROL KUTUSU
    st.success("""
    ✅ **HESAPLAMA DOĞRULAMASI (Kullanılan Formüller):**
    * **CPM:** `(Maliyet / Gösterim) x 1.000` mantığıyla tersine hesaplanarak Gösterim bulundu.
    * **RPM:** `((Manuel Tıklanma x Ürün Fiyatı) / Gösterim) x 1.000`
    * **ROI:** `(Gelir - Maliyet) / Maliyet x 100` (Kar formülü uygulandı)
    """)
