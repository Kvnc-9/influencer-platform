import streamlit as st
from supabase import create_client
import pandas as pd
import plotly.express as px
import requests
import json
import time

# -----------------------------------------------------------------------------
# 1. AYARLAR VE TASARIM (GÖRSELDEKİ ÖZEL TASARIM 🎨)
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Influencer ROI Simülatörü", layout="wide", page_icon="✨")

# BURASI SİTENİN GÖRÜNÜMÜNÜ OLUŞTURAN KISIM (CSS)
st.markdown("""
<style>
    /* 1. ARKA PLAN: Görseldeki Mor-Turuncu Geçiş */
    .stApp {
        background: linear-gradient(135deg, #240b36 0%, #c31432 100%);
        background-attachment: fixed;
        color: white;
    }

    /* 2. SIDEBAR: Buzlu Cam Efekti */
    section[data-testid="stSidebar"] {
        background-color: rgba(0, 0, 0, 0.2);
        backdrop-filter: blur(20px);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    /* 3. KUTULAR (Metric Container): Şeffaf ve Modern */
    .metric-container {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 15px;
        padding: 25px;
        margin-bottom: 20px;
        border: 1px solid rgba(255, 255, 255, 0.2);
        backdrop-filter: blur(10px);
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
    }

    /* 4. TABLO TASARIMI */
    .stDataFrame {
        background-color: rgba(0, 0, 0, 0.3);
        border-radius: 10px;
        padding: 10px;
    }

    /* 5. METİNLER VE BAŞLIKLAR */
    h1, h2, h3 {
        color: white !important;
        font-family: 'Helvetica Neue', sans-serif;
        font-weight: 700;
    }
    label {
        color: #e0e0e0 !important;
        font-weight: bold;
    }
    
    /* 6. INPUT ALANLARI */
    div[data-baseweb="input"] {
        background-color: rgba(0, 0, 0, 0.3) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important; 
        color: white !important;
    }
    input { color: white !important; }

    /* 7. KAZANAN KARTI (WINNER BOX) */
    .winner-box {
        background: linear-gradient(90deg, #11998e, #38ef7d);
        color: white;
        padding: 20px;
        border-radius: 15px;
        text-align: center;
        box-shadow: 0 10px 20px rgba(0,0,0,0.2);
        margin-bottom: 25px;
        border: 1px solid rgba(255,255,255,0.3);
    }
    .winner-title { font-size: 24px; font-weight: bold; margin-bottom: 5px; }
    .winner-stat { font-size: 18px; opacity: 0.9; }

</style>
""", unsafe_allow_html=True)

# Supabase Bağlantısı
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except:
    st.error("⚠️ Secrets ayarları eksik!")
    st.stop()

def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

# Session State
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# -----------------------------------------------------------------------------
# 2. FONKSİYONLAR
# -----------------------------------------------------------------------------

def trigger_webhook(username):
    # SENİN MAKE.COM LİNKİN (Otomatik Eklendi) ✅
    webhook_url = "https://hook.eu1.make.com/ixxd5cuuqkhhkpd8sqn5soiyol0a952x"
    try:
        requests.get(f"{webhook_url}?username={username}")
        return True
    except:
        return False

def clear_database():
    """TÜM VERİYİ SİLER"""
    try:
        supabase.table('influencers').delete().neq("username", "xxxx").execute()
        return True
    except Exception as e:
        st.error(f"Silme hatası: {e}")
        return False

def safe_json_parse(raw_data):
    if not raw_data: return []
    if isinstance(raw_data, list): return raw_data
    if not isinstance(raw_data, str): return []
    try:
        return json.loads(raw_data)
    except json.JSONDecodeError:
        try:
            return json.loads(f"[{raw_data}]")
        except:
            return []

def get_avg_views_from_json(row):
    raw_data = row.get('posts_raw_data')
    posts = safe_json_parse(raw_data)
    views_list = []
    
    if posts and isinstance(posts, list):
        for post in posts:
            views = post.get('videoViewCount') or post.get('playCount') or post.get('viewCount') or 0
            if views > 0: views_list.append(views)

    if views_list:
        return int(sum(views_list) / len(views_list))
    else:
        return 0

def calculate_roi_metrics(row, ad_cost, clicks, product_price):
    """
    YENİ HESAPLAMA MANTIĞI:
    1. Net Kâr = (Tıklama * Ürün Fiyatı) - Maliyet
    2. ROI Çarpanı = Gelir / Maliyet
    3. Brand Score = ROI performansına göre 0-100 arası puan
    """
    views = row.get('avg_views', 0)
    
    if views <= 0:
        return pd.Series([0, 0, 0, 0, 0], index=['CPM ($)', 'RPM ($)', 'Net Kâr ($)', 'ROI (x)', 'Brand Score'])

    # CPM ve RPM (Mevcut Formüller)
    cpm = (ad_cost / views) * 1000
    total_revenue = clicks * product_price 
    rpm = (total_revenue / views) * 1000
    
    # YENİ: Net Kâr ve ROI
    net_profit = total_revenue - ad_cost
    roi_x = total_revenue / ad_cost if ad_cost > 0 else 0
    
    # YENİ: Otomatik Brand Alignment Score (Yapay Zeka yoksa matematikle üretir)
    # ROI ne kadar yüksekse puan o kadar artar.
    brand_score = min(99, int((roi_x * 25) + 30)) 
    
    return pd.Series([cpm, rpm, net_profit, roi_x, brand_score], 
                     index=['CPM ($)', 'RPM ($)', 'Net Kâr ($)', 'ROI (x)', 'Brand Score'])

# -----------------------------------------------------------------------------
# 3. ARAYÜZ
# -----------------------------------------------------------------------------

# --- GİRİŞ PANELİ ---
if not st.session_state['logged_in']:
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown("<br><br><h1 style='text-align: center;'>🔐 GİRİŞ</h1>", unsafe_allow_html=True)
        # Giriş Kutusunu Tasarıma Uygun Yap
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        
        email = st.text_input("Kullanıcı Adı")
        password = st.text_input("Şifre", type="password")
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Giriş Yap", type="primary", use_container_width=True):
            try:
                user = supabase.auth.sign_in_with_password({"email": email, "password": password})
                if user:
                    st.session_state['logged_in'] = True
                    st.success("Başarılı!")
                    time.sleep(0.5)
                    st.rerun()
            except:
                st.error("Hatalı Giriş!")
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# --- DASHBOARD ---
else:
    with st.sidebar:
        st.title("KONTROL PANELİ")
        st.markdown("---")
        
        new_u = st.text_input("Yeni Analiz (Kullanıcı Adı):")
        if st.button("Analiz Et 🚀", use_container_width=True):
            if new_u:
                trigger_webhook(new_u)
                st.success("Veri çekiliyor...")
        
        st.divider()
        st.markdown("### ⚠️ Veri Yönetimi")
        if st.button("🗑️ TÜM LİSTEYİ SİL", type="primary", use_container_width=True):
            if clear_database():
                st.toast("Liste Temizlendi!", icon="✅")
                time.sleep(1)
                st.rerun()
        
        st.divider()
        if st.button("Çıkış Yap"):
            st.session_state['logged_in'] = False
            st.rerun()

    # --- ANA EKRAN ---
    st.title("📈 Influencer ROI Simülatörü")
    st.markdown("Yapay Zeka Destekli Finansal Analiz Aracı")
    
    # GİRDİ ALANLARI (INPUTS)
    with st.container():
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("### 💸 Maliyet")
            ad_cost = st.number_input("Influencer Bütçesi ($)", value=1000, step=100)
        with c2:
            st.markdown("### 🖱️ Etkileşim")
            exp_clicks = st.number_input("Beklenen Tıklama", value=500, step=50)
        with c3:
            st.markdown("### 🏷️ Ürün")
            prod_price = st.number_input("Ürün Fiyatı ($)", value=30.0, step=5.0)
        st.markdown('</div>', unsafe_allow_html=True)

    # --- VERİ İŞLEME ---
    response = supabase.table('influencers').select("*").execute()
    
    if response.data:
        df = pd.DataFrame(response.data)
        
        # Niche Kontrolü
        if 'Niche' not in df.columns:
            if 'niche' in df.columns: df['Niche'] = df['niche']
            else: df['Niche'] = "Genel"
        df['Niche'] = df['Niche'].fillna("Genel").replace("", "Genel")

        # Hesaplamalar
        df['avg_views'] = df.apply(get_avg_views_from_json, axis=1)
        metrics = df.apply(calculate_roi_metrics, args=(ad_cost, exp_clicks, prod_price), axis=1)
        df = pd.concat([df, metrics], axis=1)
        
        df_valid = df[df['avg_views'] > 0].copy()
        
        if not df_valid.empty:
            # En kârlı olanı bulmak için sırala
            df_valid = df_valid.sort_values(by="Net Kâr ($)", ascending=False)
            
            # --- 🏆 KAZANANI BUL VE GÖSTER ---
            winner = df_valid.iloc[0]
            if winner['Net Kâr ($)'] > 0:
                st.markdown(f"""
                <div class="winner-box">
                    <div class="winner-title">🏆 TAVSİYE EDİLEN: {winner['username']}</div>
                    <div class="winner-stat">
                        Tahmini Kâr: <b>${winner['Net Kâr ($)']:,.0f}</b> | 
                        ROI Çarpanı: <b>{winner['ROI (x)']:.1f}x</b> | 
                        Marka Skoru: <b>{winner['Brand Score']:.0f}/100</b>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.error("⚠️ Mevcut senaryoda kârlı bir influencer bulunamadı.")

            # --- TABLO ---
            st.subheader("📋 Detaylı Finansal Tablo")
            
            cols = ['username', 'Niche', 'avg_views', 'Brand Score', 'CPM ($)', 'RPM ($)', 'ROI (x)', 'Net Kâr ($)']
            
            # Tablo Renklendirme
            st.dataframe(
                df_valid[cols].style.format({
                    "avg_views": "{:,.0f}",
                    "Brand Score": "{:.0f}",
                    "CPM ($)": "${:.2f}",
                    "RPM ($)": "${:.2f}",
                    "ROI (x)": "{:.2f}x",
                    "Net Kâr ($)": "${:+.2f}"
                }).background_gradient(subset=['Net Kâr ($)'], cmap="RdYlGn"), # Kâr sütununu renklendir
                use_container_width=True,
                height=400
            )
            
            # --- GRAFİK (NOKTALI - SCATTER) ---
            st.markdown("---")
            st.subheader("📊 Grafiksel Karşılaştırma")
            
            fig = px.scatter(
                df_valid,
                x="CPM ($)",      
                y="RPM ($)",      
                color="Niche",    
                size="Net Kâr ($)", # Baloncuk büyüklüğü kâra göre
                hover_name="username",
                hover_data=["ROI (x)", "Brand Score"],
                text="username",
                title="Maliyet vs Gelir Analizi (Büyük Nokta = Çok Kâr)",
                labels={"CPM ($)": "Maliyet (CPM)", "RPM ($)": "Gelir (RPM)"},
                height=600,
                template="plotly_dark" # Koyu Tema Grafiği
            )
            
            # Grafik Arkaplanını Şeffaf Yap
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color="white")
            )
            fig.update_traces(textposition='top center')
            
            # Başabaş Noktası Çizgisi
            max_limit = max(df_valid['CPM ($)'].max(), df_valid['RPM ($)'].max()) * 1.1
            fig.add_shape(
                type="line", line=dict(dash='dash', color="gray"),
                x0=0, y0=0, x1=max_limit, y1=max_limit
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
        else:
            st.warning("Veri var ama videolu gönderi bulunamadı.")
    else:
        st.info("Listeniz boş. Sol menüden analiz başlatın.")
