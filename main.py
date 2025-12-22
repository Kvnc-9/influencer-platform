import streamlit as st
import pandas as pd
import plotly.express as px

# Sayfa Genişliği ve Tasarımı
st.set_page_config(page_title="Influencer AI Optimizer", layout="wide")

# --- GERÇEKÇİ VERİ SETİ (Kategorilere Göre 10 Influencer) ---
INFLUENCER_DATABASE = {
    "Wellness & Spor": [
        {"username": "ecevahapoglu", "followers": 455000, "avg_views": 85000, "rpm": 85, "cpm": 40, "alignment": 98},
        {"username": "elvinlevinler", "followers": 1300000, "avg_views": 420000, "rpm": 60, "cpm": 55, "alignment": 92},
        {"username": "tugce_incee", "followers": 185000, "avg_views": 55000, "rpm": 75, "cpm": 30, "alignment": 94},
        {"username": "cansuyegin", "followers": 225000, "avg_views": 70000, "rpm": 70, "cpm": 35, "alignment": 90},
        {"username": "dilara_kocak", "followers": 860000, "avg_views": 110000, "rpm": 95, "cpm": 50, "alignment": 100},
        {"username": "ebrusalli", "followers": 3300000, "avg_views": 380000, "rpm": 55, "cpm": 65, "alignment": 85},
        {"username": "cetincetintas", "followers": 615000, "avg_views": 190000, "rpm": 90, "cpm": 45, "alignment": 97},
        {"username": "muratbur", "followers": 142000, "avg_views": 45000, "rpm": 65, "cpm": 25, "alignment": 80},
        {"username": "aysunbekcan", "followers": 98000, "avg_views": 35000, "rpm": 70, "cpm": 20, "alignment": 87},
        {"username": "polat_ozdemir", "followers": 110000, "avg_views": 28000, "rpm": 72, "cpm": 22, "alignment": 89},
    ],
    "Teknoloji": [
        {"username": "hakki_alkan", "followers": 1200000, "avg_views": 450000, "rpm": 120, "cpm": 75, "alignment": 95},
        {"username": "mesutcevik", "followers": 350000, "avg_views": 180000, "rpm": 140, "cpm": 85, "alignment": 98},
        {"username": "barisozcan", "followers": 6500000, "avg_views": 2500000, "rpm": 200, "cpm": 120, "alignment": 88},
        {"username": "can_deger", "followers": 150000, "avg_views": 85000, "rpm": 180, "cpm": 90, "alignment": 99},
        {"username": "murat_gamsiz", "followers": 100000, "avg_views": 45000, "rpm": 110, "cpm": 60, "alignment": 96},
        {"username": "shiftdelete", "followers": 2000000, "avg_views": 600000, "rpm": 100, "cpm": 70, "alignment": 85},
        {"username": "webtekno", "followers": 2500000, "avg_views": 750000, "rpm": 90, "cpm": 65, "alignment": 80},
        {"username": "tamer_yesildag", "followers": 1800000, "avg_views": 400000, "rpm": 80, "cpm": 55, "alignment": 75},
        {"username": "iphonedo", "followers": 900000, "avg_views": 350000, "rpm": 150, "cpm": 100, "alignment": 94},
        {"username": "enis_kirazoglu", "followers": 1100000, "avg_views": 800000, "rpm": 130, "cpm": 80, "alignment": 82},
    ],
    "Güzellik & Bakım": [
        {"username": "merveozkaynak", "followers": 2200000, "avg_views": 550000, "rpm": 55, "cpm": 50, "alignment": 96},
        {"username": "duyguozaslan", "followers": 2000000, "avg_views": 380000, "rpm": 65, "cpm": 60, "alignment": 85},
        {"username": "danlabilic", "followers": 6000000, "avg_views": 1500000, "rpm": 50, "cpm": 80, "alignment": 70},
        {"username": "sebibebi", "followers": 950000, "avg_views": 120000, "rpm": 60, "cpm": 45, "alignment": 92},
        {"username": "polen_sarica", "followers": 210000, "avg_views": 65000, "rpm": 70, "cpm": 35, "alignment": 90},
        {"username": "gorkemkarman", "followers": 550000, "avg_views": 110000, "rpm": 75, "cpm": 40, "alignment": 94},
        {"username": "aslicira", "followers": 300000, "avg_views": 85000, "rpm": 68, "cpm": 38, "alignment": 91},
        {"username": "aysenur_yazici", "followers": 400000, "avg_views": 45000, "rpm": 90, "cpm": 55, "alignment": 98},
        {"username": "damla_kalaycik", "followers": 750000, "avg_views": 190000, "rpm": 62, "cpm": 48, "alignment": 88},
        {"username": "ceren_ceyhun", "followers": 180000, "avg_views": 40000, "rpm": 65, "cpm": 30, "alignment": 89},
    ]
}

# --- ARAYÜZ VE HESAPLAMA ---
st.title("🛡️ Pro Influencer Insights Dashboard")
st.markdown("Gerçek verilerle bütçe optimizasyonu ve ROI tahmini.")

with st.sidebar:
    st.header("🛒 Kampanya Detayları")
    selected_niche = st.selectbox("Bir Niş Seçin", list(INFLUENCER_DATABASE.keys()))
    product_price = st.number_input("Satılacak Ürün Fiyatı (₺)", min_value=1.0, value=1500.0)
    total_budget = st.number_input("Toplam Reklam Bütçesi (₺)", min_value=1000, value=250000)
    
    st.divider()
    calculate = st.button("ANALİZİ BAŞLAT", use_container_width=True)

if calculate:
    df = pd.DataFrame(INFLUENCER_DATABASE[selected_niche])
    
    # 1. Erişim Tahmini (Son 10 video ortalamasının çarpanı)
    df['total_reach'] = df['avg_views'] * 1.4 # Story + Feed Etkisi
    
    # 2. Skorlama Algoritması (Bütçe dağıtımını belirler)
    # Alignment karesi alınarak nişe en uygun isimlerin öne çıkması sağlanır.
    df['dist_score'] = ((df['alignment'] / 100) ** 2) * df['rpm']
    
    # 3. Bütçe Dağılımı
    total_dist_score = df['dist_score'].sum()
    df['allocated_budget'] = (df['dist_score'] / total_dist_score) * total_budget
    
    # 4. ROI ve Kazanç Tahmini
    # (Bin izlenme başına getiri katsayısı ve ürün fiyat çarpanı)
    df['est_revenue'] = (df['total_reach'] / 1000) * df['rpm'] * (product_price / 1000) * 12 
    df['roi'] = df['est_revenue'] / df['allocated_budget']

    # --- ÖZET KARTLARI ---
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Toplam Tahmini Erişim", f"{int(df['total_reach'].sum()):,}")
    c2.metric("Tahmini Ciro", f"₺{int(df['est_revenue'].sum()):,}")
    c3.metric("Kampanya ROI", f"{df['roi'].mean():.2f}x")
    c4.metric("Kazanılacak Müşteri (Tahmini)", f"{int(df['est_revenue'].sum() / product_price):,}")

    # --- ŞEFFAFLIK KUTUSU ---
    with st.expander("📊 Matematiksel Hesaplama Metodolojisi"):
        st.write("""
        Sistem bütçeyi şu adımlarla dağıtır:
        - **Bütçe Payı:** Bir influencer'ın niş uyumunun (Alignment) karesi alınır ve RPM değeri ile çarpılır. Çıkan sonuç toplam havuzdaki payını belirler.
        - **Erişim (Reach):** Son 10 video ortalaması (avg_views) baz alınır ve %40 yan etkileşim (story/paylaşım) eklenir.
        - **RPM (Revenue Per Mille):** Influencer'ın her 1000 izlenmede yarattığı tahmini parasal değerdir.
        - **ROI:** `(Tahmini Ciro / Harcanan Bütçe)` şeklinde hesaplanır.
        """)

    # --- GRAFİKLER ---
    st.divider()
    g1, g2 = st.columns(2)
    with g1:
        fig1 = px.pie(df, values='allocated_budget', names='username', title="Bütçe Dağılım Oranları", hole=0.4)
        st.plotly_chart(fig1, use_container_width=True)
    with g2:
        fig2 = px.bar(df, x='username', y='roi', title="Influencer Başına Beklenen ROI", color='roi', color_continuous_scale='Portland')
        st.plotly_chart(fig2, use_container_width=True)

    # --- TABLO ---
    st.subheader(f"📋 {selected_niche} İçin Detaylı Rapor")
    st.table(df[['username', 'followers', 'avg_views', 'alignment', 'allocated_budget', 'roi']].sort_values(by='roi', ascending=False))

else:
    st.info("Lütfen sol taraftan verileri girin ve 'Analizi Başlat' butonuna basın.")
