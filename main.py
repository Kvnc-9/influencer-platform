import streamlit as st
from supabase import create_client
import pandas as pd
import plotly.express as px
import requests
import json
import time

# -----------------------------------------------------------------------------
# 1. AYARLAR VE TASARIM (GÖRSELE UYGUN YENİLENDİ 🎨)
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Influencer ROI Simülatörü", layout="wide", page_icon="✨")

# GÖRSELDEKİ TASARIMA UYGUN CSS BLOKLARI
st.markdown("""
<style>
    /* 1. ARKA PLAN (Görseldeki Mor-Turuncu Geçiş) */
    .stApp {
        background: linear-gradient(135deg, #1e0538 0%, #581c87 40%, #c2410c 100%);
        background-attachment: fixed;
        color: white;
        font-family: 'Helvetica Neue', sans-serif;
    }

    /* 2. SIDEBAR (Sol Menü - Koyu ve Şeffaf) */
    section[data-testid="stSidebar"] {
        background-color: rgba(20, 10, 40, 0.85);
        backdrop-filter: blur(10px);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }
    section[data-testid="stSidebar"] h1, h2, h3, label {
        color: #e0e0e0 !important;
    }

    /* 3. METRİK KARTLARI (Görseldeki Siyah/Turuncu Kartlar Gibi) */
    .metric-container {
        background: rgba(0, 0, 0, 0.4);
        border-radius: 15px;
        padding: 25px;
        margin-bottom: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(15px);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        color: white;
    }

    /* 4. BAŞLIKLAR (WEB DESIGN Yazısı Gibi Büyük ve Modern) */
    h1 {
        font-size: 3.5rem !important;
        font-weight: 800 !important;
        background: -webkit-linear-gradient(eee, #999);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin-bottom: 0px;
    }
    
    h3 {
        font-weight: 600;
        color: #ffccbc !important; /* Açık turuncu başlıklar */
    }

    /* 5. BUTONLAR (Görseldeki Turuncu Butonlar) */
    div.stButton > button {
        background: linear-gradient(90deg, #ff7e5f, #feb47b);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 10px 25px;
        font-weight: bold;
        text-transform: uppercase;
        box-shadow: 0 4px 15px rgba(255, 126, 95, 0.4);
        transition: all 0.3s ease;
    }
    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(255, 126, 95, 0.6);
        background: linear-gradient(90deg, #feb47b, #ff7e5f);
        color: white;
    }

    /* 6. INPUT ALANLARI (Şeffaf ve Modern) */
    div[data-baseweb="input"] {
        background-color: rgba(255, 255, 255, 0.1) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 10px !important;
        color: white !important;
    }
    input {
        color: white !important;
    }
    label {
        color: #f0f0f0 !important;
    }

    /* 7. METRİK RAKAMLARI */
    div[data-testid="stMetricValue"] {
        font-size: 32px;
        color: #fff;
        font-weight: 700;
        text-shadow: 0 0 10px rgba(255,255,255,0.5);
    }
    div[data-testid="stMetricLabel"] {
        color: #ddd;
    }

    /* 8. TABLO VE GRAFİK ARKAPLANI */
    .stDataFrame {
        background-color: rgba(0, 0, 0, 0.2);
        border-radius: 10px;
        padding: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Supabase Bağlantısı
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except:
    st.error("⚠️ Secrets ayarları eksik!")
    st.stop()

# Cache kullanmıyoruz, her işlemde taze bağlantı
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

# Session State Kontrolü
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# -----------------------------------------------------------------------------
# 2. FONKSİYONLAR
# -----------------------------------------------------------------------------

def trigger_webhook(username):
    # SENİN VERDİĞİN LİNK
    webhook_url = "https://hook.eu1.make.com/ixxd5cuuqkhhkpd8sqn5soiyol0a952x"
    try:
        requests.get(f"{webhook_url}?username={username}")
        return True
    except:
        return False

def clear_database():
    """TÜM VERİYİ SİLER"""
    try:
        # Username'i garip bir şey olmayan herkesi sil
        supabase.table('influencers').delete().neq("username", "bu_asla_olmayacak_bir_isim").execute()
        return True
    except Exception as e:
        st.error(f"Silme hatası: {e}. Lütfen Supabase SQL Editor'den RLS'i kapatın.")
        return False

def safe_json_parse(raw_data):
    """JSON Format Düzeltici"""
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
    """Ortalama İzlenme Hesaplayıcı"""
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
    views = row.get('avg_views', 0)
    if views <= 0:
        return pd.Series([0, 0, 0, 0, 0], index=['CPM ($)', 'RPM ($)', 'Net Kâr ($)', 'ROI (x)', 'Brand Score'])

    cpm = (ad_cost / views) * 1000
    total_revenue = clicks * product_price 
    rpm = (total_revenue / views) * 1000
    net_profit = total_revenue - ad_cost
    roi_x = total_revenue / ad_cost if ad_cost > 0 else 0
    brand_score = min(99, int((roi_x * 20) + 40))
    
    return pd.Series([cpm, rpm, net_profit, roi_x, brand_score], 
                     index=['CPM ($)', 'RPM ($)', 'Net Kâr ($)', 'ROI (x)', 'Brand Score'])

# -----------------------------------------------------------------------------
# 3. ARAYÜZ (Giriş ve Dashboard Ayrımı)
# -----------------------------------------------------------------------------

# --- GİRİŞ PANELİ ---
if not st.session_state['logged_in']:
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown("<br><br><h1 style='text-align: center;'>🔐 GİRİŞ</h1>", unsafe_allow_html=True)
        st.markdown("<div class='metric-container'>", unsafe_allow_html=True)
        
        email = st.text_input("Kullanıcı Adı")
        password = st.text_input("Şifre", type="password")
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Giriş Yap", type="primary", use_container_width=True):
            try:
                user = supabase.auth.sign_in_with_password({"email": email, "password": password})
                if user:
                    st.session_state['logged_in'] = True
                    st.success("Giriş Başarılı!")
                    time.sleep(0.5)
                    st.rerun()
            except Exception as e:
                st.error("Giriş Başarısız! Bilgileri kontrol edin.")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    st.stop() 

# -----------------------------------------------------------------------------
# DASHBOARD (Sadece giriş yapılınca çalışır)
# -----------------------------------------------------------------------------

# Sidebar
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3003/3003202.png", width=50) # Temsili Logo
    st.title("KONTROL PANELİ")
    
    st.markdown("---")
    
    new_u = st.text_input("Yeni Analiz (Kullanıcı Adı):")
    if st.button("Analiz Et 🚀", use_container_width=True):
        if new_u:
            trigger_webhook(new_u)
            st.success("İşlem Başlatıldı! Veri bekleniyor...")
    
    st.divider()
    
    st.markdown("### ⚠️ Veri Yönetimi")
    if st.button("🗑️ TÜM LİSTEYİ SİL", type="primary", use_container_width=True):
        if clear_database():
            st.toast("Veritabanı temizlendi!", icon="✅")
            time.sleep(1)
            st.rerun()
    
    st.divider()
    if st.button("Çıkış Yap"):
        st.session_state['logged_in'] = False
        st.rerun()

# Ana Ekran
st.markdown("<h1>INFLUENCER <br> <span style='color:#FF7F50'>ROI SIMULATOR</span></h1>", unsafe_allow_html=True)
st.markdown("<p style='font-size: 1.2rem; opacity: 0.8;'>Yapay Zeka Destekli Finansal Analiz & Tahminleme Aracı</p>", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

with st.container():
    # Görseldeki gibi kart yapısı için özel HTML
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

# Veri Listesi
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
        df_valid = df_valid.sort_values(by="Net Kâr ($)", ascending=False)
        
        # --- 🏆 KAZANAN KART (ÖZEL TASARIM) ---
        winner = df_valid.iloc[0]
        if winner['Net Kâr ($)'] > 0:
            st.markdown(f"""
            <div style="background: linear-gradient(90deg, #11998e, #38ef7d); padding: 20px; border-radius: 15px; color: white; margin-bottom: 20px; box-shadow: 0 5px 15px rgba(56, 239, 125, 0.4);">
                <h2 style="color:white; margin:0;">🏆 TAVSİYE EDİLEN: {winner['username']}</h2>
                <p style="font-size: 1.2rem; margin:5px 0 0 0;">Tahmini Kâr: <b>${winner['Net Kâr ($)']:,.0f}</b> | ROI: <b>{winner['ROI (x)']:.1f}x</b></p>
            </div>
            """, unsafe_allow_html=True)
        
        st.subheader("📋 Detaylı Analiz")
        
        cols = ['username', 'Niche', 'avg_views', 'Brand Score', 'CPM ($)', 'RPM ($)', 'ROI (x)', 'Net Kâr ($)']
        
        # Tabloyu Koyu Temaya Uygun Hale Getirme
        st.dataframe(
            df_valid[cols].style.format({
                "avg_views": "{:,.0f}",
                "Brand Score": "{:.0f}",
                "CPM ($)": "${:.2f}",
                "RPM ($)": "${:.2f}",
                "ROI (x)": "{:.2f}x",
                "Net Kâr ($)": "${:+.2f}"
            }).background_gradient(subset=['Net Kâr ($)'], cmap="RdYlGn"),
            use_container_width=True,
            height=400
        )
        
        # --- SCATTER PLOT (KOYU TEMA UYUMLU) ---
        st.markdown("---")
        st.subheader("📊 Grafiksel Karşılaştırma")
        
        fig = px.scatter(
            df_valid,
            x="CPM ($)",      
            y="RPM ($)",      
            color="Niche",    
            size="Net Kâr ($)", 
            hover_name="username",
            hover_data=["ROI (x)", "Brand Score"],
            text="username",
            title="Maliyet vs Gelir Analizi",
            labels={"CPM ($)": "Maliyet (CPM)", "RPM ($)": "Gelir (RPM)"},
            height=600,
            template="plotly_dark" # Koyu Tema Grafiği
        )
        
        # Arkaplanı Şeffaf Yapma
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color="white")
        )
        fig.update_traces(textposition='top center')
        
        max_limit = max(df_valid['CPM ($)'].max(), df_valid['RPM ($)'].max()) * 1.1
        fig.add_shape(
            type="line", line=dict(dash='dash', color="gray"),
            x0=0, y0=0, x1=max_limit, y1=max_limit
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    else:
        st.warning("Veri var ama videolu gönderi bulunamadı.")
else:
    st.info("Listeniz boş. Sol menüden yeni kişi ekleyin.")
