import streamlit as st
import pandas as pd
import plotly.express as px

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Influencer AI | Optimizer", layout="wide")

# --- CUSTOM CSS (Görseldeki Tasarım Dili) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;500;700&display=swap');
    
    /* Genel Sayfa Yapısı */
    .stApp {
        background-color: #FAFAFA;
        font-family: 'Outfit', sans-serif;
    }
    
    /* Üst Başlık Stili */
    h1 {
        color: #1A1A1A;
        font-weight: 700;
        letter-spacing: -1px;
    }
    
    /* Metrik Kartları (Görseldeki beyaz kutular gibi) */
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #FFFFFF 0%, #FFF5F5 100%);
        border: 1px solid #FFE4E4;
        border-radius: 20px;
        padding: 20px;
        box-shadow: 0 10px 25px rgba(255, 75, 75, 0.08);
        transition: transform 0.3s ease;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 35px rgba(255, 75, 75, 0.15);
    }
    div[data-testid="stMetricLabel"] {
        font-size: 14px;
        color: #888;
        font-weight: 500;
    }
    div[data-testid="stMetricValue"] {
        font-size: 28px;
        color: #FF4B4B; /* Canlı Kırmızı/Turuncu Ton */
        font-weight: 700;
    }

    /* Sidebar Tasarımı */
    section[data-testid="stSidebar"] {
        background-color: #1E1E1E; /* Koyu Sidebar */
    }
    section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] label {
        color: #FFFFFF !important;
    }
    
    /* Buton Tasarımı (Gradient) */
    .stButton>button {
        background: linear-gradient(90deg, #FF4B4B 0%, #FF9068 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 15px 30px;
        font-size: 16px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
        width: 100%;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        box-shadow: 0 10px 20px rgba(255, 75, 75, 0.4);
        transform: scale(1.02);
    }

    /* Tablo Düzeni */
    .stDataFrame {
        border-radius: 15px;
        box-shadow: 0 5px 15px rgba(0,0,0,0.05);
        border: 1px solid #eee;
    }

    /* Bilgi Kutusu */
    .info-box {
        background-color: #FFF0F0;
        border-left: 5px solid #FF4B4B;
        padding: 20px;
        border-radius: 10px;
        margin-top: 20px;
        color: #333;
    }
    </style>
    """, unsafe_allow_html=True)

# --- VERİ SETİ (Aynı Kalan Veriler) ---
def get_database():
    return {
        "Beauty & Güzellik": [
            {"username": "merveozkaynak", "followers": 2200000, "avg_views": 550000, "base_cpm": 55, "base_rpm": 95, "alignment": 96},
            {"username": "duyguozaslan", "followers": 2000000, "avg_views": 380000, "base_cpm": 65, "base_rpm": 110, "alignment": 85},
            {"username": "danlabilic", "followers": 6000000, "avg_views": 1500000, "base_cpm": 50, "base_rpm": 80, "alignment": 70},
            {"username": "sebibebi", "followers": 950000, "avg_views": 120000, "base_cpm": 60, "base_rpm": 130, "alignment": 92},
            {"username": "polen_sarica", "followers": 210000, "avg_views": 65000, "base_cpm": 35, "base_rpm": 140, "alignment": 90},
            {"username": "gorkemkarman", "followers": 550000, "avg_views": 110000, "base_cpm": 40, "base_rpm": 120, "alignment": 94},
            {"username": "aslicira", "followers": 300000, "avg_views": 85000, "base_cpm": 38, "base_rpm": 115, "alignment": 91},
            {"username": "aysenur_yazici", "followers": 400000, "avg_views": 45000, "base_cpm": 55, "base_rpm": 160, "alignment": 98},
            {"username": "damla_kalaycik", "followers": 750000, "avg_views": 190000, "base_cpm": 48, "base_rpm": 105, "alignment": 88},
            {"username": "ceren_ceyhun", "followers": 180000, "avg_views": 40000, "base_cpm": 30, "base_rpm": 125, "alignment": 89},
        ],
        "Wellness & Sport": [
            {"username": "ecevahapoglu", "followers": 455000, "avg_views": 85000, "base_cpm": 40, "base_rpm": 85, "alignment": 98},
            {"username": "elvinlevinler", "followers": 1300000, "avg_views": 420000, "base_cpm": 55, "base_rpm": 120, "alignment": 92},
            {"username": "tugce_incee", "followers": 185000, "avg_views": 55000, "base_cpm": 30, "base_rpm": 95, "alignment": 94},
            {"username": "cansuyegin", "followers": 225000, "avg_views": 70000, "base_cpm": 35, "base_rpm": 100, "alignment": 90},
            {"username": "dilara_kocak", "followers": 860000, "avg_views": 110000, "base_cpm": 50, "base_rpm": 150, "alignment": 100},
            {"username": "ebrusalli", "followers": 3300000, "avg_views": 380000, "base_cpm": 65, "base_rpm": 110, "alignment": 85},
            {"username": "cetincetintas", "followers": 615000, "avg_views": 190000, "base_cpm": 45, "base_rpm": 130, "alignment": 97},
            {"username": "muratbur", "followers": 142000, "avg_views": 45000, "base_cpm": 25, "base_rpm": 80, "alignment": 88},
            {"username": "aysunbekcan", "followers": 98000, "avg_views": 35000, "base_cpm": 20, "base_rpm": 75, "alignment": 91},
            {"username": "polat_ozdemir", "followers": 110000, "avg_views": 28000, "base_cpm": 22, "base_rpm": 89, "alignment": 89},
        ],
        "Teknoloji": [
            {"username": "hakki_alkan", "followers": 1200000, "avg_views": 450000, "base_cpm": 80, "base_rpm": 150, "alignment": 95},
            {"username": "mesutcevik", "followers": 350000, "avg_views": 180000, "base_cpm": 90, "base_rpm": 180, "alignment": 98},
            {"username": "can_deger", "followers": 150000, "avg_views": 95000, "base_cpm": 100, "base_rpm": 220, "alignment": 99},
            {"username": "barisozcan", "followers": 6500000, "avg_views": 2500000, "base_cpm": 150, "base_rpm": 300, "alignment": 90},
            {"username": "iphonedo", "followers": 900000, "avg_views": 350000, "base_cpm": 110, "base_rpm": 250, "alignment": 94},
            {"username": "donanimarsivi", "followers": 1000000, "avg_views": 400000, "base_cpm": 85, "base_rpm": 160, "alignment": 92},
            {"username": "enis_kirazoglu", "followers": 1100000, "avg_views": 800000, "base_cpm": 70, "base_rpm": 130, "alignment": 85},
            {"username": "webtekno", "followers": 2500000, "avg_views": 700000, "base_cpm": 60, "base_rpm": 110, "alignment": 80},
            {"username": "technopat", "followers": 500000, "avg_views": 150000, "base_cpm": 95, "base_rpm": 170, "alignment": 96},
            {"username": "shiftdelete", "followers": 2000000, "avg_views": 600000, "base_cpm": 65, "base_rpm": 120, "alignment": 82},
        ]
    }

# --- ANA UYGULAMA MANTIĞI ---
st.title("🚀 Influencer AI | Optimizer")
st.markdown("Veriye dayalı kampanya planlama asistanınız.")

# --- SIDEBAR (Koyu Tema) ---
with st.sidebar:
    st.header("🎯 Kampanya Parametreleri")
    niche = st.selectbox("Kategori Seçimi", list(get_database().keys()))
    total_budget = st.number_input("Reklam Bütçesi (₺)", min_value=1000, value=150000)
    product_price = st.number_input("Ürün Birim Fiyatı (₺)", min_value=1, value=1500)
    
    st.markdown("---")
    calculate = st.button("ANALİZİ BAŞLAT")
    
    st.markdown("""
    <div style='margin-top: 30px; font-size: 12px; color: #888;'>
    Influencer AI © 2024<br>
    Powered by Data Analytics
    </div>
    """, unsafe_allow_html=True)

if calculate:
    df = pd.DataFrame(get_database()[niche])
    
    # --- FORMÜLLER (Aynen Korundu) ---
    # 1. Bütçe Dağılımı (Alignment'a göre)
    total_alignment = df['alignment'].sum()
    df['allocated_budget'] = (df['alignment'] / total_alignment) * total_budget
    
    # 2. Gösterim (Impressions) = (Cost / CPM) * 1000
    df['est_impressions'] = (df['allocated_budget'] / df['base_cpm']) * 1000
    
    # 3. Gelir (Revenue) = (RPM * Impressions) / 1000
    df['total_revenue'] = (df['base_rpm'] * df['est_impressions']) / 1000
    
    # 4. ROI = (Revenue - Cost) / Cost * 100
    df['roi_percentage'] = ((df['total_revenue'] - df['allocated_budget']) / df['allocated_budget']) * 100

    # --- ÜST METRİK KARTLARI ---
    col1, col2, col3 = st.columns(3)
    col1.metric("🔥 Toplam Tahmini Ciro", f"₺{df['total_revenue'].sum():,.0f}")
    col2.metric("📈 Ortalama ROI", f"%{df['roi_percentage'].mean():.1f}")
    col3.metric("👀 Toplam Gösterim", f"{int(df['est_impressions'].sum()):,}")

    st.markdown("<br>", unsafe_allow_html=True)

    # --- GRAFİKLER ---
    c1, c2 = st.columns(2)
    with c1:
        # Pie Chart - Renkli ve Modern
        fig_pie = px.pie(df, values='allocated_budget', names='username', hole=0.6, 
                         title="Bütçe Dağılımı",
                         color_discrete_sequence=px.colors.sequential.RdBu)
        fig_pie.update_layout(showlegend=False)
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with c2:
        # Bar Chart - ROI
        fig_bar = px.bar(df, x='username', y='roi_percentage', 
                         title="Yüzdesel ROI Geri Dönüşü",
                         color='roi_percentage',
                         color_continuous_scale='Reds')
        st.plotly_chart(fig_bar, use_container_width=True)

    # --- DETAYLI TABLO ---
    st.subheader("📋 Detaylı Analiz Raporu")
    st.dataframe(df[['username', 'alignment', 'allocated_budget', 'est_impressions', 'total_revenue', 'roi_percentage']].style.format({
        'allocated_budget': '₺{:.2f}',
        'total_revenue': '₺{:.2f}',
        'roi_percentage': '%{:.2f}',
        'est_impressions': '{:,.0f}'
    }), use_container_width=True)

    # --- METODOLOJİ (Bilgi Kutusu) ---
    st.markdown(f"""
    <div class="info-box">
        <h4>💡 Hesaplama Algoritması</h4>
        <ul>
            <li><b>CPM (Cost Per Mille):</b> (Maliyet / Gösterim) x 1,000 formülü baz alınmıştır.</li>
            <li><b>RPM (Revenue Per Mille):</b> (Gelir / Gösterim) x 1,000 formülü ile ciro hesaplanır.</li>
            <li><b>ROI (Return on Investment):</b> (Kar / Maliyet) x 100 formülü ile yatırım geri dönüş oranı bulunur.</li>
            <li><b>Bütçe Dağılımı:</b> Influencer'ın markaya uyum skoru (Alignment) oranında bütçeden pay almasını sağlar.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

else:
    # Boş Durum (Empty State)
    st.info("👈 Lütfen sol menüden kampanya detaylarını girin ve analizi başlatın.")
