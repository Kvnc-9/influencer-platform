import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client, Client
import time

# --- 1. SAYFA VE GENEL AYARLAR ---
st.set_page_config(page_title="Influencer ROI Master", layout="wide", initial_sidebar_state="collapsed")

# --- 2. CSS TASARIMI (GÖRÜNÜRLÜK GARANTİLİ) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');
    
    /* Genel Reset */
    .stApp { background-color: #0E1117; font-family: 'Inter', sans-serif; }
    h1, h2, h3, h4, p, span, div, label, li { color: #FFFFFF !important; }
    
    /* --- LANDING PAGE STİLLERİ --- */
    .landing-wrapper {
        width: 100%;
        display: block;
        color: white;
    }
    
    /* HERO BÖLÜMÜ */
    .hero-section {
        text-align: center;
        padding: 80px 20px;
        background: radial-gradient(circle at center, rgba(255, 109, 0, 0.15) 0%, rgba(14, 17, 23, 0) 70%);
        border-bottom: 1px solid #333;
    }
    .hero-title {
        font-size: 80px; font-weight: 900; letter-spacing: -2px; margin-bottom: 20px;
        background: -webkit-linear-gradient(#fff, #FF9E80); -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .hero-sub { font-size: 22px; color: #aaa !important; max-width: 800px; margin: 0 auto; line-height: 1.5; }
    
    /* ÖZELLİKLER */
    .features-section {
        display: flex; justify-content: center; gap: 30px; padding: 60px 20px; flex-wrap: wrap;
    }
    .feature-box {
        background: #161B22; border: 1px solid #30363D; padding: 30px; border-radius: 16px; width: 300px;
        transition: transform 0.3s;
    }
    .feature-box:hover { transform: translateY(-5px); border-color: #FF6D00; }
    
    /* --- YORUMLAR (SOSYAL KANIT) --- */
    .testimonials-section {
        background-color: #0d1117; /* Koyu zemin */
        padding: 80px 20px;
        margin-top: 40px;
        border-top: 1px solid #30363d;
        text-align: center;
    }
    .reviews-grid {
        display: flex; justify-content: center; gap: 30px; margin-top: 40px; flex-wrap: wrap;
    }
    .review-card {
        background: linear-gradient(145deg, #1f2428, #161b22);
        padding: 30px; border-radius: 12px; width: 320px; text-align: left;
        border: 1px solid #30363d; box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }
    .stars { color: #FFD700 !important; font-size: 20px; margin-bottom: 15px; }
    .review-text { color: #c9d1d9 !important; font-style: italic; font-size: 15px; line-height: 1.6; }
    .client-box { margin-top: 20px; display: flex; align-items: center; gap: 15px; }
    .avatar { width: 45px; height: 45px; background: #FF6D00; color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 18px; }
    
    /* APP İÇİ ELEMENTLER */
    div[data-testid="stMetric"] { background-color: #161B22; border: 1px solid #FF6D00; border-radius: 12px; }
    .stButton>button {
        background: linear-gradient(90deg, #FF6D00 0%, #FF3D00 100%);
        color: white !important; border: none; border-radius: 8px; font-weight: bold; padding: 0.8rem;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. SUPABASE BAĞLANTISI ---
if 'user' not in st.session_state:
    st.session_state.user = None

try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except:
    pass

# --- 4. TEK PARÇA LANDING PAGE HTML ---
def render_full_landing_page():
    # Bu HTML bloğu tek parça render edilir, böylece kopukluk olmaz.
    st.markdown("""
    <div class="landing-wrapper">
        
        <div class="hero-section">
            <span style="color:#FF6D00; font-weight:bold; border:1px solid #FF6D00; padding:5px 15px; border-radius:20px; font-size:12px;">YENİ NESİL ANALİTİK V2.0</span>
            <h1 class="hero-title">Influencer ROI Master</h1>
            <p class="hero-sub">
                Reklam bütçenizi körlemesine harcamayın. Yapay zeka ile 
                <span style="color:#FF6D00; font-weight:bold;">gerçek veriyi</span> analiz edin, 
                en karlı influencerları bulun.
            </p>
        </div>

        <div class="features-section">
            <div class="feature-box">
                <h3>⚡ Otomatik Hesaplama</h3>
                <p style="color:#8b949e !important;">CPM, RPM ve ROI metriklerini anlık veriyle, hatasız hesaplayın.</p>
            </div>
            <div class="feature-box">
                <h3>🎯 Hedef Kitle Uyumu</h3>
                <p style="color:#8b949e !important;">Marka uyum skoruna (Alignment) göre bütçeyi en doğru kişiye aktarın.</p>
            </div>
            <div class="feature-box">
                <h3>💎 Kurumsal Raporlama</h3>
                <p style="color:#8b949e !important;">Apple tasarım dilinde, yöneticilerinize sunabileceğiniz şık grafikler.</p>
            </div>
        </div>

        <div class="testimonials-section">
            <h2 style="font-size:36px; font-weight:800; margin-bottom:10px;">Sektör Liderleri Bize Güveniyor</h2>
            <p style="color:#8b949e !important;">Türkiye'nin en büyük 500+ markası bütçesini bizimle yönetiyor.</p>
            
            <div class="reviews-grid">
                <div class="review-card">
                    <div class="stars">★★★★★</div>
                    <p class="review-text">"Eskiden influencer seçerken hislerimizle hareket ediyorduk. ROI Master ile artık matematiğe güveniyoruz. Dönüşüm oranımız %40 arttı."</p>
                    <div class="client-box">
                        <div class="avatar">SY</div>
                        <div>
                            <div style="font-weight:bold; font-size:14px;">Selin Yılmaz</div>
                            <div style="font-size:12px; color:#8b949e !important;">CMO, TechMedia A.Ş.</div>
                        </div>
                    </div>
                </div>

                <div class="review-card">
                    <div class="stars">★★★★★</div>
                    <p class="review-text">"Arayüz o kadar temiz ve hızlı ki, tüm pazarlama ekibimiz 10 dakikada adapte oldu. Hesaplamaların doğruluğu harika."</p>
                    <div class="client-box">
                        <div class="avatar">MD</div>
                        <div>
                            <div style="font-weight:bold; font-size:14px;">Mert Demir</div>
                            <div style="font-size:12px; color:#8b949e !important;">CEO, GlowCosmetics</div>
                        </div>
                    </div>
                </div>

                <div class="review-card">
                    <div class="stars">★★★★★</div>
                    <p class="review-text">"Manuel CPM hesaplarken yaptığımız hatalar bize binlerce liraya mal oluyordu. Bu platform işimizi inanılmaz kolaylaştırdı."</p>
                    <div class="client-box">
                        <div class="avatar">AK</div>
                        <div>
                            <div style="font-weight:bold; font-size:14px;">Ayşe Kaya</div>
                            <div style="font-size:12px; color:#8b949e !important;">Growth Lead, FitLife App</div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div style="margin-top:50px; color:#484f58 !important; font-size:12px;">
                © 2025 Influencer ROI Master Inc. Tüm hakları saklıdır.
            </div>
        </div>

    </div>
    """, unsafe_allow_html=True)

# --- 5. GİRİŞ PANELİ (SIDEBAR) ---
def render_login_sidebar():
    st.sidebar.markdown("## 🍊 Giriş Paneli")
    st.sidebar.info("Panel erişimi için giriş yapın.")
    
    choice = st.sidebar.radio("İşlem", ["Giriş Yap", "Kayıt Ol"])
    email = st.sidebar.text_input("E-Posta")
    password = st.sidebar.text_input("Şifre", type="password")
    
    if choice == "Giriş Yap":
        if st.sidebar.button("Güvenli Giriş", use_container_width=True):
            try:
                res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                st.session_state.user = res.user
                st.success("Giriş Başarılı!")
                time.sleep(0.5)
                st.rerun()
            except:
                # Demo Fallback
                if email == "admin" and password == "1234":
                    st.session_state.user = {"email": "admin@demo.com"}
                    st.rerun()
                else:
                    st.sidebar.error("Hatalı giriş.")
                    
    elif choice == "Kayıt Ol":
        if st.sidebar.button("Hesap Oluştur", use_container_width=True):
            try:
                supabase.auth.sign_up({"email": email, "password": password})
                st.sidebar.success("Kayıt Başarılı!")
            except Exception as e:
                st.sidebar.error(f"Hata: {e}")

# --- 6. ANA UYGULAMA (HESAPLAMA) ---
def main_app():
    # Çıkış Butonu
    with st.sidebar:
        user_email = st.session_state.user.email if hasattr(st.session_state.user, 'email') else 'Admin'
        st.write(f"👤 **{user_email}**")
        if st.sidebar.button("Çıkış Yap"):
            if 'supabase' in globals(): supabase.auth.sign_out()
            st.session_state.user = None
            st.rerun()

    st.title("🍊 Pro Hesaplama Paneli")
    
    c1, c2, c3 = st.columns(3)
    with c1: niche = st.selectbox("Kategori", ["Beauty & Güzellik", "Teknoloji", "Wellness & Spor"])
    with c2: total_budget = st.number_input("Toplam Bütçe (₺)", 1000.0, 1000000.0, 100000.0)
    with c3: product_price = st.number_input("Ürün Fiyatı (₺)", 1.0, 10000.0, 500.0)

    st.divider()

    # Data
    def get_data(category):
        data = {
            "Beauty & Güzellik": [{"Influencer": "Merve Özkaynak", "Alignment": 96, "Avg_Views": 550000, "Manuel_Tiklanma": 500}, {"Influencer": "Duygu Özaslan", "Alignment": 85, "Avg_Views": 380000, "Manuel_Tiklanma": 420}, {"Influencer": "Danla Bilic", "Alignment": 70, "Avg_Views": 1500000, "Manuel_Tiklanma": 1200}, {"Influencer": "Sebi Bebi", "Alignment": 92, "Avg_Views": 120000, "Manuel_Tiklanma": 300}, {"Influencer": "Görkem Karman", "Alignment": 94, "Avg_Views": 110000, "Manuel_Tiklanma": 350}, {"Influencer": "Polen Sarıca", "Alignment": 90, "Avg_Views": 65000, "Manuel_Tiklanma": 200}, {"Influencer": "Aslı Çıra", "Alignment": 91, "Avg_Views": 85000, "Manuel_Tiklanma": 210}, {"Influencer": "Ayşenur Yazıcı", "Alignment": 98, "Avg_Views": 45000, "Manuel_Tiklanma": 150}, {"Influencer": "Damla Kalaycık", "Alignment": 88, "Avg_Views": 190000, "Manuel_Tiklanma": 400}, {"Influencer": "Ceren Ceyhun", "Alignment": 89, "Avg_Views": 40000, "Manuel_Tiklanma": 180}],
            "Teknoloji": [{"Influencer": "Hakkı Alkan", "Alignment": 95, "Avg_Views": 450000, "Manuel_Tiklanma": 800}, {"Influencer": "Mesut Çevik", "Alignment": 98, "Avg_Views": 180000, "Manuel_Tiklanma": 400}, {"Influencer": "Barış Özcan", "Alignment": 90, "Avg_Views": 2500000, "Manuel_Tiklanma": 2500}, {"Influencer": "Can Değer", "Alignment": 99, "Avg_Views": 95000, "Manuel_Tiklanma": 300}, {"Influencer": "Enis Kirazoğlu", "Alignment": 85, "Avg_Views": 850000, "Manuel_Tiklanma": 1500}, {"Influencer": "Webtekno", "Alignment": 80, "Avg_Views": 700000, "Manuel_Tiklanma": 1800}, {"Influencer": "iPhonedo", "Alignment": 94, "Avg_Views": 350000, "Manuel_Tiklanma": 600}, {"Influencer": "ShiftDelete", "Alignment": 82, "Avg_Views": 600000, "Manuel_Tiklanma": 1000}, {"Influencer": "Donanım Arşivi", "Alignment": 92, "Avg_Views": 400000, "Manuel_Tiklanma": 750}, {"Influencer": "Technopat", "Alignment": 96, "Avg_Views": 150000, "Manuel_Tiklanma": 350}],
            "Wellness & Spor": [{"Influencer": "Ece Vahapoğlu", "Alignment": 98, "Avg_Views": 85000, "Manuel_Tiklanma": 200}, {"Influencer": "Elvin Levinler", "Alignment": 92, "Avg_Views": 420000, "Manuel_Tiklanma": 600}, {"Influencer": "Dilara Koçak", "Alignment": 100, "Avg_Views": 110000, "Manuel_Tiklanma": 400}, {"Influencer": "Ebru Şallı", "Alignment": 85, "Avg_Views": 380000, "Manuel_Tiklanma": 900}, {"Influencer": "Çetin Çetintaş", "Alignment": 97, "Avg_Views": 190000, "Manuel_Tiklanma": 350}, {"Influencer": "Murat Bür", "Alignment": 88, "Avg_Views": 45000, "Manuel_Tiklanma": 120}, {"Influencer": "Aysun Bekcan", "Alignment": 91, "Avg_Views": 35000, "Manuel_Tiklanma": 100}, {"Influencer": "Polat Özdemir", "Alignment": 89, "Avg_Views": 28000, "Manuel_Tiklanma": 110}, {"Influencer": "Tuğçe İnce", "Alignment": 94, "Avg_Views": 55000, "Manuel_Tiklanma": 150}, {"Influencer": "Cansu Yeğin", "Alignment": 90, "Avg_Views": 70000, "Manuel_Tiklanma": 180}]
        }
        return data.get(category, [])

    if 'df_final' not in st.session_state or st.session_state.get('curr_niche') != niche:
        st.session_state.df_final = pd.DataFrame(get_data(niche))
        st.session_state.curr_niche = niche

    st.subheader("👇 Tıklanma Sayılarını Düzenleyin")
    edited_df = st.data_editor(
        st.session_state.df_final,
        column_config={
            "Manuel_Tiklanma": st.column_config.NumberColumn("Manuel Tıklanma", min_value=0, required=True),
            "Avg_Views": st.column_config.NumberColumn("Ort. İzlenme", format="%d"),
            "Alignment": st.column_config.ProgressColumn("Uyum", format="%d", min_value=0, max_value=100),
            "Influencer": st.column_config.TextColumn("Influencer", disabled=True)
        },
        disabled=["Influencer", "Avg_Views", "Alignment"],
        use_container_width=True,
        hide_index=True
    )

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("HESAPLA", use_container_width=True):
        df = edited_df.copy()
        
        # FORMÜLLER
        total_align = df['Alignment'].sum()
        df['Maliyet'] = (df['Alignment'] / total_align) * total_budget
        df['CPM'] = (df['Maliyet'] / df['Avg_Views']) * 1000
        df['Gelir'] = df['Manuel_Tiklanma'] * product_price
        df['RPM'] = (df['Gelir'] / df['Avg_Views']) * 1000
        df['Kar'] = df['Gelir'] - df['Maliyet']
        df['ROI (%)'] = (df['Kar'] / df['Maliyet']) * 100

        c1, c2, c3 = st.columns(3)
        c1.metric("TOPLAM GELİR", f"₺{df['Gelir'].sum():,.2f}")
        c2.metric("TOPLAM NET KAR", f"₺{df['Kar'].sum():,.2f}")
        c3.metric("ORTALAMA ROI", f"%{df['ROI (%)'].mean():.2f}")

        g1, g2 = st.columns(2)
        with g1:
            fig_pie = px.pie(df, values='Maliyet', names='Influencer', title='Bütçe Dağılımı (Maliyet)', 
                             color_discrete_sequence=px.colors.sequential.Oranges, hole=0.4)
            fig_pie.update_layout(paper_bgcolor='#0E1117', plot_bgcolor='#0E1117', font=dict(color='white'))
            st.plotly_chart(fig_pie, use_container_width=True)
            
        with g2:
            fig_bar = px.bar(df, x='Influencer', y='ROI (%)', title='ROI Analizi', 
                             text_auto='.1f', color='ROI (%)', color_continuous_scale='Oranges')
            fig_bar.update_layout(paper_bgcolor='#0E1117', plot_bgcolor='#0E1117', font=dict(color='white'),
                                  xaxis_title="", yaxis_title="ROI %")
            st.plotly_chart(fig_bar, use_container_width=True)

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

# --- 7. AKIŞ KONTROLÜ (KESİN) ---
if st.session_state.user is not None:
    main_app()
else:
    render_login_sidebar()
    render_full_landing_page() # Tek fonksiyon, tek blok
