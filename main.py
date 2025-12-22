import streamlit as st
import pandas as pd
import plotly.express as px

# Sayfa Konfigürasyonu
st.set_page_config(page_title="Influencer AI | Pro Optimizer", layout="wide")

# APPLE DESIGN CSS (Minimalist & Innovative)
st.markdown("""
    <style>
    /* San Francisco benzeri font */
    @import url('https://fonts.googleapis.com/css2?family=SF+Pro+Display:wght@300;400;600&family=Inter:wght@300;400;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #ffffff;
    }

    .main {
        background-color: #ffffff;
    }

    /* Apple Stil Metrik Kartları */
    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.8);
        border: 1px solid #d2d2d7;
        border-radius: 22px;
        padding: 25px;
        transition: all 0.5s ease;
    }
    div[data-testid="stMetric"]:hover {
        box-shadow: 0 20px 40px rgba(0,0,0,0.04);
        transform: translateY(-5px);
    }

    /* Sidebar - Apple Control Center stili */
    section[data-testid="stSidebar"] {
        background-color: #f5f5f7;
        border-right: 1px solid #d2d2d7;
    }

    /* Mavi Apple Butonu */
    .stButton>button {
        background-color: #0071e3;
        color: white;
        border-radius: 980px;
        padding: 12px 30px;
        border: none;
        font-weight: 500;
        font-size: 16px;
        width: 100%;
        transition: all 0.3s cubic-bezier(0.25, 0.1, 0.25, 1);
    }
    .stButton>button:hover {
        background-color: #0077ed;
        box-shadow: 0 8px 15px rgba(0,113,227,0.3);
    }

    /* Tablo Tasarımı */
    .stDataFrame {
        border-radius: 18px;
        overflow: hidden;
        border: 1px solid #d2d2d7;
    }

    /* Başlıklar */
    h1 {
        font-weight: 600;
        letter-spacing: -0.05em;
        color: #1d1d1f;
    }
    </style>
    """, unsafe_allow_html=True)

# --- VERİ SETİ (İstediğin İsimler ve Gerçek Veriler Sabit Tutuldu) ---
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

# --- APP LOGIC ---
st.title(" Influencer AI")
st.write("Analitik verilerle inovatif kampanya planlama.")

with st.sidebar:
    st.markdown("### Kampanya Ayarları")
    niche = st.selectbox("Niş Seçimi", list(get_database().keys()))
    total_budget = st.number_input("Reklam Bütçesi (₺)", min_value=1000, value=150000)
    product_value = st.number_input("Ürün Birim Değeri (₺)", min_value=1, value=2500)
    
    st.markdown("---")
    calculate = st.button("HESAPLA")

if calculate:
    df = pd.DataFrame(get_database()[niche])
    
    # HESAPLAMALAR (Senin İstediğin Formüller Sabit)
    total_alignment = df['alignment'].sum()
    df['allocated_budget'] = (df['alignment'] / total_alignment) * total_budget
    df['est_impressions'] = (df['allocated_budget'] / df['base_cpm']) * 1000
    df['total_revenue'] = (df['base_rpm'] * df['est_impressions']) / 1000
    df['roi_percentage'] = ((df['total_revenue'] - df['allocated_budget']) / df['allocated_budget']) * 100

    # ÜST METRİKLER (Apple Stil Kartlar)
    m1, m2, m3 = st.columns(3)
    m1.metric("Tahmini Toplam Ciro", f"₺{df['total_revenue'].sum():,.0f}")
    m2.metric("Kampanya ROI", f"%{df['roi_percentage'].mean():.1f}")
    m3.metric("Tahmini Gösterim", f"{int(df['est_impressions'].sum()):,}")

    st.markdown("---")

    # GRAFİKLER
    c1, c2 = st.columns(2)
    with c1:
        fig_pie = px.pie(df, values='allocated_budget', names='username', hole=0.7, 
                         title="Bütçe Dağılım Payı", 
                         color_discrete_sequence=px.colors.qualitative.Pastel)
        fig_pie.update_layout(showlegend=False, margin=dict(t=40, b=0, l=0, r=0))
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with c2:
        fig_bar = px.bar(df, x='username', y='roi_percentage', 
                         title="Influencer Bazlı ROI (%)",
                         color_discrete_sequence=['#0071e3'])
        fig_bar.update_layout(xaxis_title="", yaxis_title="", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_bar, use_container_width=True)

    # DETAYLI TABLO
    st.markdown("### 📊 Detaylı Analiz")
    st.dataframe(df[['username', 'alignment', 'allocated_budget', 'est_impressions', 'total_revenue', 'roi_percentage']].style.format({
        'allocated_budget': '₺{:.2f}',
        'total_revenue': '₺{:.2f}',
        'roi_percentage': '%{:.2f}',
        'est_impressions': '{:,.0f}'
    }), use_container_width=True)

    # HESAPLAMA ŞEFFAFLIĞI (Apple Stil Bilgi Paneli)
    st.markdown(f"""
    <div style="background-color: #f5f5f7; padding: 25px; border-radius: 20px; border: 1px solid #d2d2d7;">
    <h4 style="margin-top:0; color: #1d1d1f;"> Algoritma Metodolojisi</h4>
    <p style="color: #86868b; font-size: 14px;">
    Bu rapor, <b>CPM = (Maliyet / Gösterim) x 1,000</b>, <b>RPM = (Gelir / Gösterim) x 1,000</b> ve 
    <b>ROI = (Kar / Maliyet) x 100</b> formülleriyle hesaplanmıştır. 
    Bütçe dağılımı, influencer'ların <i>Brand Alignment</i> skorlarına göre optimize edilerek en yüksek verimlilik hedeflenmiştir.
    </p>
    </div>
    """, unsafe_allow_html=True)

else:
    st.info("Devam etmek için kampanya detaylarını girin ve hesapla butonuna basın.")
