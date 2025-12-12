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
st.set_page_config(page_title="Influencer ROI Simülatörü", layout="wide", page_icon="💸")

# Özel CSS
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
</style>
""", unsafe_allow_html=True)

# Supabase Bağlantısı
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except:
    st.error("⚠️ Secrets ayarları eksik!")
    st.stop()

# Cache kullanmıyoruz, her işlemde taze bağlantı (Login sorununu çözer)
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
    # SENİN VERDİĞİN LİNK BURAYA EKLENDİ ✅
    webhook_url = "https://hook.eu1.make.com/ixxd5cuuqkhhkpd8sqn5soiyol0a952x"
    try:
        # Username parametresini ekliyoruz
        requests.get(f"{webhook_url}?username={username}")
        return True
    except:
        return False

def clear_database():
    """TÜM VERİYİ SİLER"""
    try:
        # Username'i 'X' olmayan her şeyi sil (Yani hepsini)
        # Not: Supabase'de RLS kapalı olmalı!
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
        return pd.Series([0, 0, 0], index=['CPM ($)', 'RPM ($)', 'Fark ($)'])

    cpm = (ad_cost / views) * 1000
    total_revenue = clicks * product_price 
    rpm = (total_revenue / views) * 1000
    diff = rpm - cpm
    
    return pd.Series([cpm, rpm, diff], index=['CPM ($)', 'RPM ($)', 'Fark ($)'])

# -----------------------------------------------------------------------------
# 3. ARAYÜZ (Giriş ve Dashboard Ayrımı)
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
            except Exception as e:
                st.error("Giriş Başarısız! Bilgileri kontrol edin.")
    
    st.stop() # Giriş yapılmadıysa aşağıyı okuma

# -----------------------------------------------------------------------------
# DASHBOARD (Sadece giriş yapılınca çalışır)
# -----------------------------------------------------------------------------

# Sidebar
with st.sidebar:
    st.header("⚙️ Kontrol Paneli")
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
st.title("📈 Influencer Kârlılık Simülatörü")

with st.container():
    st.markdown('<div class="metric-container">', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        ad_cost = st.number_input("Influencer Maliyeti ($)", value=1000, step=100)
    with c2:
        exp_clicks = st.number_input("Beklenen Tıklama", value=500, step=50)
    with c3:
        prod_price = st.number_input("Ürün Fiyatı ($)", value=30.0, step=5.0)
    
    st.divider()
    
    total_rev = exp_clicks * prod_price
    net_profit = total_rev - ad_cost
    
    m1, m2 = st.columns(2)
    m1.metric(label="Hedef Ciro", value=f"${total_rev:,.0f}")
    m2.metric(
        label="Net Kâr Durumu", 
        value=f"${net_profit:,.0f}", 
        delta="KÂR" if net_profit > 0 else "ZARAR",
        delta_color="normal"
    )
    st.markdown('</div>', unsafe_allow_html=True)

# Veri Listesi
response = supabase.table('influencers').select("*").execute()

if response.data:
    df = pd.DataFrame(response.data)
    
    # Niche Kontrolü
    if 'Niche' not in df.columns:
        if 'niche' in df.columns: df['Niche'] = df['niche']
        else: df['Niche'] = "-"
    df['Niche'] = df['Niche'].fillna("-")
    
    # Hesaplamalar
    df['avg_views'] = df.apply(get_avg_views_from_json, axis=1)
    metrics = df.apply(calculate_roi_metrics, args=(ad_cost, exp_clicks, prod_price), axis=1)
    df = pd.concat([df, metrics], axis=1)
    
    df_valid = df[df['avg_views'] > 0].copy()
    
    if not df_valid.empty:
        df_valid = df_valid.sort_values(by="Fark ($)", ascending=False)
        
        st.subheader("📋 Analiz Tablosu")
        
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
            height=450
        )
        
        st.subheader("📊 Kârlılık Sıralaması")
        fig = px.bar(
            df_valid,
            x='username',
            y='Fark ($)',
            color='Fark ($)',
            title="Hangi Influencer Kazandırır?",
            text_auto='+.0f',
            color_continuous_scale=['red', 'green'],
            labels={'Fark ($)': 'Net Kâr ($)'}
        )
        fig.add_hline(y=0, line_dash="dot", line_color="black")
        st.plotly_chart(fig, use_container_width=True)
        
    else:
        st.warning("Veri var ama videolu gönderi bulunamadı.")
else:
    st.info("Veritabanı boş. Sol menüden yeni kişi ekleyin.")
