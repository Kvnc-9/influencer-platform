import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client, Client
import time

# --- 1. SAYFA VE GENEL AYARLAR ---
st.set_page_config(page_title="Influencer ROI Master", layout="wide", initial_sidebar_state="collapsed")

# --- CSS TASARIMI (DARK MODE & ORANGE & TESTIMONIALS) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');
    
    .stApp { background-color: #0E1117; font-family: 'Inter', sans-serif; }
    h1, h2, h3, h4, p, span, div, label, li { color: #FFFFFF !important; }
    
    /* LANDING PAGE - HERO SECTION */
    .hero-container {
        text-align: center;
        padding: 80px 20px 40px 20px;
        background: radial-gradient(circle at center, rgba(255, 109, 0, 0.15) 0%, rgba(14, 17, 23, 0) 60%);
        border-bottom: 1px solid #333;
        animation: fadeIn 1s ease-in;
    }
    .hero-title {
        font-size: 72px; font-weight: 800; letter-spacing: -2px;
        background: linear-gradient(135deg, #FFFFFF 0%, #FF9E80 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin-bottom: 10px;
    }
    .hero-highlight { color: #FF6D00 !important; }
    
    /* ÖZELLİK KARTLARI */
    .feature-grid { display: flex; justify-content: center; gap: 20px; margin: 40px 0; flex-wrap: wrap; }
    .feature-card {
        background: #161B22; border: 1px solid #30363D; padding: 30px; border-radius: 16px;
        width: 300px; text-align: left; transition: transform 0.3s;
    }
    .feature-card:hover { transform: translateY(-5px); border-color: #FF6D00; }
    
    /* YORUMLAR (TESTIMONIALS) */
    .testimonial-section { text-align: center; margin-top: 60px; padding: 40px; background: #0D1117; }
    .testimonial-grid { display: flex; justify-content: center; gap: 20px; margin-top: 30px; flex-wrap: wrap; }
    .review-card {
        background: linear-gradient(145deg, #1E1E1E, #161616);
        padding: 25px; border-radius: 12px; width: 320px;
        border-left: 4px solid #FF6D00; box-shadow: 0 4px 20px rgba(0,0,0,0.4);
        text-align: left;
    }
    .stars { color: #FFD700 !important; font-size: 18px; margin-bottom: 10px; }
    .client-name { font-weight: bold; font-size: 14px; color: #FFF !important; margin-top: 15px; }
    .client-company { font-size: 12px; color: #888 !important; }

    /* APP İÇİ STİLLER */
    div[data-testid="stMetric"] { background-color: #161B22; border: 1px solid #FF6D00; border-radius: 12px; padding: 15px; }
    div[data-testid="stMetricLabel"] { color: #FF9E80 !important; font-size: 14px; }
    div[data-testid="stMetricValue"] { color: #FFFFFF !important; font-size: 28px; font-weight: 700; }
    
    /* BUTONLAR */
    .stButton>button {
        background: linear-gradient(92deg, #FF6D00 0%, #FF3D00 100%);
        color: white !important; border: none; border-radius: 8px; font-weight: 600;
        padding: 0.75rem 1.5rem; transition: all 0.3s;
    }
    .stButton>button:hover { box-shadow: 0 0 15px rgba(255, 109, 0, 0.5); transform: scale(1.02); }

    @keyframes fadeIn { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
    </style>
    """, unsafe_allow_html=True)

# --- 2. SUPABASE BAĞLANTISI ---
if 'user' not in st.session_state:
    st.session_state.user = None

try:
    # Secrets dosyasından verileri çekiyoruz
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception:
    # Hata durumunda (Localde secrets yoksa) demo modunda çalışsın diye pass geçiyoruz
    # Gerçek canlı ortamda secrets.toml olmalı.
    pass

# --- 3. LANDING PAGE FONKSİYONU ---
def show_landing_page():
    # HERO ALANI
    st.markdown("""
        <div class="hero-container">
            <span style="background-color:rgba(255,109,0,0.1); color:#FF6D00 !important; padding:5px 15px; border-radius:20px; font-size:12px; font-weight:bold; border:1px solid rgba(255,109,0,0.3);">YENİ NESİL ANALİTİK</span>
            <h1 class="hero-title">Influencer ROI Master</h1>
            <p style="font-size: 20px; color: #ccc !important; max-width: 700px; margin: 0 auto; line-height: 1.6;">
                Milyonluk reklam bütçelerinizi şansa bırakmayın. 
                <span class="hero-highlight">Yapay zeka destekli</span> algoritmamız ile en yüksek dönüşümü sağlayan influencerları saniyeler içinde tespit edin.
            </p>
        </div>
    """, unsafe_allow_html=True)

    # ÖZELLİKLER
    st.markdown("""
        <div class="feature-grid">
            <div class="feature-card">
                <h3 style="margin-bottom:10px;">⚡ Otomatik Hesaplama</h3>
                <p style="font-size:14px; color:#aaa !important;">CPM, RPM ve ROI metriklerini karmaşık Excel tablolarıyla uğraşmadan, anlık veriyle hesaplayın.</p>
            </div>
            <div class="feature-card">
                <h3 style="margin-bottom:10px;">🎯 Hedef Kitle Uyumu</h3>
                <p style="font-size:14px; color:#aaa !important;">Markanızın 'Brand Alignment' skoruna göre bütçenizi en doğru kişiye otomatik dağıtın.</p>
            </div>
            <div class="feature-card">
                <h3 style="margin-bottom:10px;">💎 Kurumsal Raporlama</h3>
                <p style="font-size:14px; color:#aaa !important;">Yöneticilerinize sunabileceğiniz, Apple tasarım dilinde şık ve anlaşılır grafikler.</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # SOCIAL PROOF (YENİ EKLENEN KISIM)
    st.markdown("""
        <div class="testimonial-section">
            <h2 style="font-size:32px; font-weight:700;">Sektör Liderleri Bize Güveniyor</h2>
            <p style="color:#888 !important;">500+ Marka ROI Master ile bütçesini yönetiyor.</p>
            
            <div class="testimonial-grid">
                <div class="review-card">
                    <div class="stars">★★★★★</div>
                    <p style="font-size:14px; line-height:1.5; color:#ddd !important;">"Influencer pazarlamasında kör atış yapmayı bıraktık. Artık hangi kuruşun nereye gittiğini ve ne kadar getirdiğini net görüyoruz. ROI oranımız %40 arttı."</p>
                    <div class="client-name">Selin Yılmaz</div>
                    <div class="client-company">Pazarlama Direktörü, TechMedia A.Ş.</div>
                </div>
                
                <div class="review-card">
                    <div class="stars">★★★★★</div>
                    <p style="font-size:14px; line-height:1.5; color:#ddd !important;">"Arayüz o kadar temiz ve hızlı ki, tüm ekibimiz 10 dakikada adapte oldu. Hesaplamaların doğruluğu ve şeffaflığı harika."</p>
                    <div class="client-name">Mert Demir</div>
                    <div class="client-company">CEO, GlowCosmetics</div>
                </div>
                
                <div class="review-card">
                    <div class="stars">★★★★★</div>
                    <p style="font-size:14px; line-height:1.5; color:#ddd !important;">"CPM ve RPM hesaplamaları manuel yaparken çok hata yapıyorduk. Bu platform işimizi inanılmaz kolaylaştırdı."</p>
                    <div class="client-name">Ayşe Kaya</div>
                    <div class="client-company">Growth Manager, FitLife App</div>
                </div>
            </div>
        </div>
        
        <div style="text-align:center; margin-top:50px; padding:30px;">
            <p style="color:#666 !important; font-size:12px;">© 2024 Influencer ROI Master Inc. Tüm hakları saklıdır.</p>
        </div>
    """, unsafe_allow_html=True)

# --- 4. GİRİŞ FORMU (SIDEBAR) ---
def login_sidebar():
    st.sidebar.markdown("## 🍊 Giriş Paneli")
    st.sidebar.info("Platforma erişmek için giriş yapın.")
    
    choice = st.sidebar.radio("İşlem", ["Giriş Yap", "Kayıt Ol"])
    email = st.sidebar.text_input("E-Posta")
    password = st.sidebar.text_input("Şifre", type="password")
    
    if choice == "Giriş Yap":
        if st.sidebar.button("Güvenli Giriş", use_container_width=True):
            try:
                # Supabase Bağlantısı Varsa
                res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                st.session_state.user = res.user
                st.success("Giriş Başarılı!")
                time.sleep(0.5)
                st.rerun()
            except:
                # Supabase Yoksa veya Hata Varsa (Demo Giriş)
                if email == "admin" and password == "1234":
                    st.session_state.user = {"email": "admin@demo.com"}
                    st.rerun()
                else:
                    st.sidebar.error("Kullanıcı bulunamadı veya Supabase bağlı değil.")
                    
    elif choice == "Kayıt Ol":
        if st.sidebar.button("Hesap Oluştur", use_container_width=True):
            try:
                res = supabase.auth.sign_up({"email": email, "password": password})
                st.sidebar.success("Kayıt Başarılı! Giriş yapabilirsiniz.")
            except Exception as e:
                st.sidebar.error(f"Hata: {e}")

# --- 5. ANA UYGULAMA (HESAPLAMA) ---
def main_app():
    # Çıkış Butonu
    with st.sidebar:
        st.write(f"👤 **{st.session_state.user.email if hasattr(st.session_state.user, 'email') else 'Admin'}**")
        if st.sidebar.button("Çıkış Yap"):
            if 'supabase' in globals(): supabase.auth.sign_out()
            st.session_state.user = None
            st.rerun()

    st.title("🍊 Pro Hesaplama Paneli")
    st.markdown("Verilerinizi girin, sistem **sizin belirlediğiniz formüllere göre** kesin sonuç üretsin.")

    # GİRİŞ ALANI
    c1, c2, c3 = st.columns(3)
    with c1: 
        niche = st.selectbox("Kategori", ["Beauty & Güzellik", "Teknoloji", "Wellness & Spor"])
    with c2: 
        total_budget = st.number_input("Toplam Bütçe (₺)", min_value=1000.0, value=100000.0, step=1000.0, format="%.2f")
    with c3: 
        product_price = st.number_input("Ürün Satış Fiyatı (₺)", min_value=1.0, value=500.0, step=10.0, format="%.2f")

    st.divider()

    # VERİ SETİ (GERÇEKÇİ VERİLER)
    def get_data(category):
        data = {
            "Beauty & Güzellik": [
                {"Influencer": "Merve Özkaynak", "Alignment": 96, "Avg_Views": 550000, "Manuel_Tiklanma": 500},
                {"Influencer": "Duygu Özaslan", "Alignment": 85, "Avg_Views": 380000, "Manuel_Tiklanma": 420},
                {"Influencer": "Danla Bilic", "Alignment": 70, "Avg_Views": 1500000, "Manuel_Tiklanma": 1200},
                {"Influencer": "Sebi Bebi", "Alignment": 92, "Avg_Views": 120000, "Manuel_Tiklanma": 300},
                {"Influencer": "Görkem Karman", "Alignment": 94, "Avg_Views": 110000, "Manuel_Tiklanma": 350},
                {"Influencer": "Polen Sarıca", "Alignment": 90, "Avg_Views": 65000, "Manuel_Tiklanma": 200},
                {"Influencer": "Aslı Çıra", "Alignment": 91, "Avg_Views": 85000, "Manuel_Tiklanma": 210},
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
                {"Influencer": "Dilara Koçak", "Alignment": 100, "Avg_Views": 110000, "Manuel_Tiklanma": 400},
                {"Influencer": "Ebru Şallı", "Alignment": 85, "Avg_Views": 380000, "Manuel_Tiklanma": 900},
                {"Influencer": "Çetin Çetintaş", "Alignment": 97, "Avg_Views": 190000, "Manuel_Tiklanma": 350},
                {"Influencer": "Murat Bür", "Alignment": 88, "Avg_Views": 45000, "Manuel_Tiklanma": 120},
                {"Influencer": "Aysun Bekcan", "Alignment": 91, "Avg_Views": 35000, "Manuel_Tiklanma": 100},
                {"Influencer": "Polat Özdemir", "Alignment": 89, "Avg_Views": 28000, "Manuel_Tiklanma": 110},
                {"Influencer": "Tuğçe İnce", "Alignment": 94, "Avg_Views": 55000, "Manuel_Tiklanma": 150},
                {"Influencer": "Cansu Yeğin", "Alignment": 90, "Avg_Views": 70000, "Manuel_Tiklanma": 180},
            ]
        }
        return data.get(category, [])

    # Session State Veri Yükleme
    if 'df_data_final' not in st.session_state or st.session_state.get('current_niche_final') != niche:
        st.session_state.df_data_final = pd.DataFrame(get_data(niche))
        st.session_state.current_niche_final = niche

    st.subheader("👇 Tıklanma Sayılarını Düzenleyin (Diğerleri Otomatiktir)")
    
    # DATA EDITOR (SADECE TIKLANMA AÇIK)
    edited_df = st.data_editor(
        st.session_state.df_data_final,
        column_config={
            "Manuel_Tiklanma": st.column_config.NumberColumn("Manuel Tıklanma (Adet)", min_value=0, step=1, required=True),
            "Avg_Views": st.column_config.NumberColumn("Ort. İzlenme (Sabit)", format="%d"),
            "Alignment": st.column_config.ProgressColumn("Marka Uyumu", format="%d", min_value=0, max_value=100),
            "Influencer": st.column_config.TextColumn("Influencer", disabled=True)
        },
        disabled=["Influencer", "Avg_Views", "Alignment"],
        use_container_width=True,
        hide_index=True
    )

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("HESAPLA", use_container_width=True):
        df = edited_df.copy()
        
        # --- HESAPLAMA MOTORU (SENİN İSTEDİĞİN FORMÜLLER) ---
        
        # 1. Maliyet Dağılımı (Bütçe * (Alignment / Toplam Alignment))
        total_alignment = df['Alignment'].sum()
        df['Maliyet'] = (df['Alignment'] / total_alignment) * total_budget
        
        # 2. CPM = (Maliyet / İzlenme) * 1000
        df['CPM'] = (df['Maliyet'] / df['Avg_Views']) * 1000
        
        # 3. Gelir = Tıklanma * Ürün Fiyatı
        df['Gelir'] = df['Manuel_Tiklanma'] * product_price
        
        # 4. RPM = (Gelir / İzlenme) * 1000
        df['RPM'] = (df['Gelir'] / df['Avg_Views']) * 1000
        
        # 5. Kar = Gelir - Maliyet
        df['Kar'] = df['Gelir'] - df['Maliyet']
        
        # 6. ROI = (Kar / Maliyet) * 100
        df['ROI (%)'] = (df['Kar'] / df['Maliyet']) * 100

        # --- SONUÇLARIN GÖSTERİMİ ---
        
        # ÖZET METRİKLER
        c1, c2, c3 = st.columns(3)
        c1.metric("TOPLAM GELİR", f"₺{df['Gelir'].sum():,.2f}")
        c2.metric("TOPLAM NET KAR", f"₺{df['Kar'].sum():,.2f}")
        c3.metric("ORTALAMA ROI", f"%{df['ROI (%)'].mean():.2f}")

        # GRAFİKLER
        st.markdown("### 📊 Performans Dağılımı")
        g1, g2 = st.columns(2)
        
        with g1:
            fig_pie = px.pie(df, values='Maliyet', names='Influencer', title='Bütçe Dağılımı (Maliyet)', 
                             color_discrete_sequence=px.colors.sequential.Oranges, hole=0.4)
            fig_pie.update_layout(paper_bgcolor='#0E1117', plot_bgcolor='#0E1117', font=dict(color='white'))
            st.plotly_chart(fig_pie, use_container_width=True)
            
        with g2:
            fig_bar = px.bar(df, x='Influencer', y='ROI (%)', title='Influencer ROI (%)', 
                             text_auto='.1f', color='ROI (%)', color_continuous_scale='Oranges')
            fig_bar.update_layout(paper_bgcolor='#0E1117', plot_bgcolor='#0E1117', font=dict(color='white'),
                                  xaxis_title="", yaxis_title="ROI %")
            st.plotly_chart(fig_bar, use_container_width=True)

        # TABLO (FORMATLI)
        st.markdown("### 📋 Detaylı Rapor")
        st.dataframe(
            df[['Influencer', 'Avg_Views', 'Maliyet', 'CPM', 'Gelir', 'RPM', 'ROI (%)']].style.format({
                'Avg_Views': '{:,.0f}',
                'Maliyet': '₺{:,.2f}',
                'CPM': '₺{:,.2f}',
                'Gelir': '₺{:,.2f}',
                'RPM': '₺{:,.2f}',
                'ROI (%)': '%{:.2f}'
            }),
            use_container_width=True
        )

# --- 6. AKIŞ KONTROLÜ ---
if st.session_state.user is not None:
    main_app()
else:
    login_sidebar()
    show_landing_page()
