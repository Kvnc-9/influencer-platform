import streamlit as st
import pandas as pd
import plotly.express as px

# Sayfa Genişliği ve Apple Temalı Stil
st.set_page_config(page_title="Influencer AI | Optimizer", layout="wide")

# Apple Stil CSS Entegrasyonu
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        background-color: #f5f5f7;
    }
    
    .main {
        background-color: #f5f5f7;
    }
    
    /* Apple Stil Kartlar */
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        border-radius: 18px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.02);
        border: 1px solid #e5e5e7;
    }
    
    /* Buton Tasarımı */
    .stButton>button {
        background-color: #0071e3;
        color: white;
        border-radius: 20px;
        padding: 10px 25px;
        border: none;
        font-weight: 500;
        transition: all 0.3s;
    }
    
    .stButton>button:hover {
        background-color: #0077ed;
        transform: scale(1.02);
    }
    
    /* Kenar Çubuğu Tasarımı */
    section[data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e5e5e7;
    }
    
    h1, h2, h3 {
        color: #1d1d1f;
        letter-spacing: -0.02em;
    }
    </style>
    """, unsafe_allow_html=True)

# --- VERİ SETİ (İçerik Korundu) ---
def get_database():
    return {
        "Teknoloji": [
            {"username": "hakki_alkan", "followers": 1200000, "avg_views": 450000, "base_cpm": 80, "base_rpm": 150, "alignment": 95},
            {"username": "mesutcevik", "followers": 350000, "avg_views": 180000, "base_cpm": 90, "base_rpm": 180, "alignment": 98},
            {"username": "can_deger", "followers": 150000, "avg_views": 95000, "base_cpm": 100, "base_rpm": 220, "alignment": 99},
            {"username": "enis_kirazoglu", "followers": 1100000, "avg_views": 850000, "base_cpm": 70, "base_rpm": 130, "alignment": 85},
            {"username": "barisozcan", "followers": 6500000, "avg_views": 2500000, "base_cpm": 150, "base_rpm": 300, "alignment": 90},
            {"username": "webtekno", "followers": 2500000, "avg_views": 700000, "base_cpm": 60, "base_rpm": 110, "alignment": 80},
            {"username": "iphonedo", "followers": 900000, "avg_views": 350000, "base_cpm": 110, "base_rpm": 250, "alignment": 94},
            {"username": "shiftdelete", "followers": 2000000, "avg_views": 600000, "base_cpm": 65, "base_rpm": 120, "alignment": 82},
            {"username": "donanimarsivi", "followers": 1000000, "avg_views": 400000, "base_cpm": 85, "base_rpm": 160, "alignment": 92},
            {"username": "technopat", "followers": 500000, "avg_views": 150000, "base_cpm": 95, "base_rpm": 170, "alignment": 96},
        ],
        "Wellness & Spor": [
            {"username": "ecevahapoglu", "followers": 455000, "avg_views": 85000, "base_cpm": 40, "base_rpm": 85, "alignment": 98},
            {"username": "elvinlevinler", "followers": 1300000, "avg_views": 420000, "base_cpm": 55, "base_rpm": 120, "alignment": 92},
            {"username": "dilara_kocak", "followers": 860000, "avg_views": 110000, "base_cpm": 50, "base_rpm": 150, "alignment": 100},
            {"username": "cetincetintas", "followers": 615000, "avg_views": 190000, "base_cpm": 45, "base_rpm": 130, "alignment": 97},
            {"username": "ebrusalli", "followers": 3300000, "avg_views": 380000, "base_cpm": 65, "base_rpm": 110, "alignment": 85},
            {"username": "tugce_incee", "followers": 185000, "avg_views": 55000, "base_cpm": 30, "base_rpm": 95, "alignment": 94},
            {"username": "cansuyegin", "followers": 225000, "avg_views": 70000, "base_cpm": 35, "base_rpm": 100, "alignment": 90},
            {"username": "muratbur", "followers": 142000, "avg_views": 45000, "base_cpm": 25, "base_rpm": 80, "alignment": 88},
            {"username": "aysunbekcan", "followers": 98000, "avg_views": 35000, "base_cpm": 20, "base_rpm": 75, "alignment": 91},
            {"username": "merveozkaynak", "followers": 2200000, "avg_views": 550000, "base_cpm": 50, "base_rpm": 95, "alignment": 75}
        ]
    }

# --- ARAYÜZ ---
st.title(" Influencer AI")
st.subheader("Bütçenizi en akıllı şekilde paylaştırın.")

with st.sidebar:
    st.markdown("### ⚙️ Kampanya")
    niche = st.selectbox("Kategori", list(get_database().keys()))
    total_budget = st.number_input("Toplam Bütçe (₺)", min_value=1000, value=100000)
    product_price = st.number_input("Ürün Fiyatı (₺)", min_value=1, value=1500)
    
    st.markdown("---")
    calculate = st.button("HESAPLAMAYI BAŞLAT", use_container_width=True)

if calculate:
    data = get_database()[niche]
    df = pd.DataFrame(data)
    
    # --- FORMÜLLER (İçerik Korundu) ---
    total_alignment = df['alignment'].sum()
    df['allocated_budget'] = (df['alignment'] / total_alignment) * total_budget
    df['est_impressions'] = (df['allocated_budget'] / df['base_cpm']) * 1000
    df['total_revenue'] = (df['base_rpm'] * df['est_impressions']) / 1000
    df['roi_percentage'] = ((df['total_revenue'] - df['allocated_budget']) / df['allocated_budget']) * 100

    # Özet Kartları
    col1, col2, col3 = st.columns(3)
    col1.metric("Tahmini Toplam Gelir", f"₺{df['total_revenue'].sum():,.2f}")
    col2.metric("Kampanya ROI", f"%{df['roi_percentage'].mean():.2f}")
    col3.metric("Toplam Gösterim", f"{int(df['est_impressions'].sum()):,}")

    st.markdown("---")

    # Grafikler
    c_left, c_right = st.columns(2)
    with c_left:
        fig_pie = px.pie(df, values='allocated_budget', names='username', hole=0.7, 
                         title="Bütçe Dağılımı",
                         color_discrete_sequence=px.colors.qualitative.Pastel)
        fig_pie.update_layout(showlegend=False)
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with c_right:
        fig_roi = px.bar(df, x='username', y='roi_percentage', title="ROI Analizi (%)",
                         color_discrete_sequence=['#0071e3'])
        fig_roi.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_roi, use_container_width=True)

    # Tablo - Apple Stil
    st.markdown("### 📋 Performans Raporu")
    st.dataframe(df[['username', 'alignment', 'allocated_budget', 'est_impressions', 'total_revenue', 'roi_percentage']].style.format({
        'allocated_budget': '₺{:.2f}',
        'total_revenue': '₺{:.2f}',
        'roi_percentage': '%{:.2f}',
        'est_impressions': '{:,.0f}'
    }), use_container_width=True)

    # Formül Şeffaflığı
    st.markdown("""
    <div style="background-color: #ffffff; padding: 20px; border-radius: 15px; border: 1px solid #e5e5e7;">
    <h4 style="margin-top:0;">🔍 Analitik Metrikler</h4>
    <p style="color: #86868b; font-size: 0.9em;">
    <b>CPM:</b> (Maliyet / Gösterim) x 1,000 | 
    <b>RPM:</b> (Toplam Gelir / Gösterim) x 1,000 | 
    <b>ROI:</b> ((Gelir - Maliyet) / Maliyet) x 100
    </p>
    </div>
    """, unsafe_allow_html=True)

else:
    # Karşılama Ekranı
    st.info("Analiz için sol menüden verilerinizi girin.")
