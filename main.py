import streamlit as st
from supabase import create_client
import pandas as pd
import plotly.express as px
import requests
import json
import time

# -----------------------------------------------------------------------------
# 1. AYARLAR VE TASARIM
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Influencer ROI Analizi", layout="wide", page_icon="💎")

# Özel CSS: Tasarım İyileştirmeleri
st.markdown("""
<style>
    .metric-container {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        border: 1px solid #e0e0e0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    .stDataFrame { border-radius: 10px; overflow: hidden; }
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

# Login Kontrolü
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# -----------------------------------------------------------------------------
# 2. FONKSİYONLAR
# -----------------------------------------------------------------------------

def trigger_webhook(username):
    webhook_url = "https://hook.eu2.make.com/BURAYA_SENIN_MAKE_LINKIN" 
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
    views = row.get('avg_views', 0)
    if views <= 0:
        return pd.Series([0, 0, 0], index=['CPM ($)', 'RPM ($)', 'Fark ($)'])

    cpm = (ad_cost / views) * 1000
    total_revenue = clicks * product_price 
    rpm = (total_revenue / views) * 1000
    diff = rpm - cpm
    
    return pd.Series([cpm, rpm, diff], index=['CPM ($)', 'RPM ($)', 'Fark ($)'])

# -----------------------------------------------------------------------------
# 3. ARAYÜZ
# -----------------------------------------------------------------------------

# --- GİRİŞ PANELİ ---
if not st.session_state['logged_in']:
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown("<br><br><h2 style='text-align: center;'>🔐 Giriş Paneli</h2>", unsafe_allow_html=True)
        email = st.text_input("Kullanıcı Adı")
        password = st.text_input("Şifre", type="password")
        
        if st.button("Giriş Yap", type="primary", use_container_width=True):
            try:
                user = supabase.auth.sign_in_with_password({"email": email, "password": password})
                if user:
                    st.session_state['logged_in'] = True
                    st.success("Giriş Başarılı!")
                    time.sleep(0.5)
                    st.rerun()
            except:
                st.error("Kullanıcı adı veya şifre hatalı!")
    st.stop()

# --- DASHBOARD ---
else:
    with st.sidebar:
        st.header("⚙️ Kontrol Paneli")
        new_u = st.text_input("Yeni Analiz (Kullanıcı Adı):")
        if st.button("Analiz Et 🚀", use_container_width=True):
            if new_u:
                trigger_webhook(new_u)
                st.success("İstek Gönderildi! Veri bekleniyor...")
        
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

    # --- ÜST PANEL (INPUTS) ---
    st.title("📈 Influencer Karşılaştırma Matrisi")
    
    with st.container():
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1:
            ad_cost = st.number_input("Influencer Maliyeti ($)", value=1000, step=100)
        with c2:
            exp_clicks = st.number_input("Beklenen Tıklama", value=500, step=50)
        with c3:
            prod_price = st.number_input("Ürün Fiyatı ($)", value=30.0, step=5.0)
        st.markdown('</div>', unsafe_allow_html=True)

    # --- VERİ İŞLEME ---
    response = supabase.table('influencers').select("*").execute()
    
    if response.data:
        df = pd.DataFrame(response.data)
        
        # --- Niche (Kategori) Düzeltme ---
        # Veritabanında küçük harf/büyük harf farkı varsa hepsini kontrol et
        if 'Niche' in df.columns:
            df['Niche'] = df['Niche'].fillna("Genel")
        elif 'niche' in df.columns:
            df['Niche'] = df['niche'].fillna("Genel")
        else:
            df['Niche'] = "Genel" # Hiç sütun yoksa
            
        # Eğer veri boş string "" ise "Genel" yap
        df['Niche'] = df['Niche'].replace("", "Genel")
        # --------------------------------

        # Hesaplamalar
        df['avg_views'] = df.apply(get_avg_views_from_json, axis=1)
        metrics = df.apply(calculate_roi_metrics, args=(ad_cost, exp_clicks, prod_price), axis=1)
        df = pd.concat([df, metrics], axis=1)
        
        # Sadece verisi olanları al
        df_valid = df[df['avg_views'] > 0].copy()
        
        if not df_valid.empty:
            df_valid = df_valid.sort_values(by="Fark ($)", ascending=False)
            
            # --- 1. DETAYLI TABLO ---
            st.subheader("📋 Detaylı Analiz")
            
            cols = ['username', 'Niche', 'avg_views', 'CPM ($)', 'RPM ($)', 'Fark ($)']
            
            def highlight_profit(val):
                color = '#d1e7dd' if val > 0 else '#f8d7da'
                return f'background-color: {color}'

            st.dataframe(
                df_valid[cols].style.format({
                    "avg_views": "{:,.0f}",
                    "CPM ($)": "${:.2f}",
                    "RPM ($)": "${:.2f}",
                    "Fark ($)": "${:+.2f}"
                }).applymap(highlight_profit, subset=['Fark ($)']),
                use_container_width=True,
                height=400
            )
            
            # --- 2. NOKTA GRAFİĞİ (SCATTER PLOT) ---
            st.markdown("---")
            st.subheader("📊 Influencer Karşılaştırması (CPM vs RPM)")
            st.info("💡 **Nasıl Okunur:** Çizginin üstündeki noktalar **KÂRLI**, altındakiler **ZARARLI** demektir. Sağ tarafa ne kadar yakınsa o kadar çok Gelir (RPM) getirir.")
            
            # Scatter Plot Ayarları
            fig = px.scatter(
                df_valid,
                x="CPM ($)",      # X ekseni: Maliyet
                y="RPM ($)",      # Y ekseni: Gelir
                color="Niche",    # Renk: Kategori
                size="avg_views", # Boyut: İzlenme Gücü (Büyük balon = Çok izleniyor)
                hover_name="username",
                text="username",  # İsimleri noktaların yanına yaz
                title="Maliyet (CPM) ve Gelir (RPM) Analizi",
                labels={"CPM ($)": "Maliyet (Düşük İyidir)", "RPM ($)": "Gelir (Yüksek İyidir)"},
                height=600
            )
            
            # İsimlerin pozisyonunu ayarla (noktanın üstüne gelsin)
            fig.update_traces(textposition='top center')
            
            # "Başabaş" (Breakeven) Çizgisi ekle (X=Y doğrusu)
            # Bu çizginin üstü kâr, altı zarardır.
            max_val = max(df_valid['CPM ($)'].max(), df_valid['RPM ($)'].max())
            fig.add_shape(
                type="line", line=dict(dash='dash', color="gray"),
                x0=0, y0=0, x1=max_val, y1=max_val
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
        else:
            st.warning("Henüz video verisi olan bir analiz yok.")
    else:
        st.info("Listeniz boş.")
