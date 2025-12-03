import streamlit as st
from supabase import create_client
import pandas as pd
import plotly.express as px
import time
import requests
import json
import math

# -----------------------------------------------------------------------------
# 1. AYARLAR VE GÜVENLİK
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Influencer CPM/RPM Pro", layout="wide", page_icon="📊")

# CSS: Kart Görünümleri
st.markdown("""
<style>
    .metric-card {
        background-color: #f9f9f9;
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 15px;
        text-align: center;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except:
    st.error("⚠️ Secrets ayarları eksik! Lütfen Streamlit panelinden API anahtarlarını girin.")
    st.stop()

@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# -----------------------------------------------------------------------------
# 2. VERİ ANALİZ MOTORU
# -----------------------------------------------------------------------------

def trigger_webhook(username):
    # DİKKAT: Buraya kendi Make.com Webhook URL'ini yapıştır.
    # Sonunda ?username= OLMASIN. Temiz link olsun.
    webhook_url = "https://hook.eu2.make.com/BURAYA_SENIN_MAKE_LINKIN" 
    try:
        requests.get(f"{webhook_url}?username={username}")
        return True
    except:
        return False

def analyze_posts_json(row):
    """
    Supabase'den gelen JSON verisini açar, Video İzlenmelerini ve Yorumları çeker.
    """
    raw_data = row.get('posts_raw_data')
    stats = {
        "avg_views": 0, 
        "total_likes": 0, 
        "comment_quality": "Veri Yok", 
        "top_comment_likes": 0,
        "video_count": 0
    }
    
    # Veri boşsa veya hatalıysa boş dön
    if not raw_data: return pd.Series(stats)
    
    try:
        # Veri string (yazı) olarak geldiyse JSON'a çevir
        posts = json.loads(raw_data) if isinstance(raw_data, str) else raw_data
    except:
        return pd.Series(stats)

    views_list = []
    max_comment_likes = 0
    total_likes = 0
    
    # Liste içinde dön (Her bir post için)
    if isinstance(posts, list):
        for post in posts:
            # 1. Sadece Videoların İzlenmesini Al
            views = post.get('videoViewCount') or post.get('playCount') or 0
            if views > 0:
                views_list.append(views)
            
            # 2. Toplam Beğeni
            total_likes += post.get('likesCount', 0)
            
            # 3. Yorum Analizi
            comments = post.get('previewComments', []) or post.get('latestComments', [])
            if isinstance(comments, list):
                for c in comments:
                    c_likes = c.get('likesCount', 0)
                    if c_likes > max_comment_likes: max_comment_likes = c_likes

    # Ortalamaları Hesapla
    if views_list:
        stats["avg_views"] = int(sum(views_list) / len(views_list))
        stats["video_count"] = len(views_list)
    
    stats["total_likes"] = total_likes
    stats["top_comment_likes"] = max_comment_likes
    
    # Yorum Kalite Etiketi
    if max_comment_likes >= 100: stats["comment_quality"] = "🔥 Yüksek (Topluluk Güçlü)"
    elif max_comment_likes > 20: stats["comment_quality"] = "✅ Orta Seviye"
    else: stats["comment_quality"] = "⚠️ Düşük Etkileşim"
        
    return pd.Series(stats)

def calculate_financials(row, base_cpm_input, platform_fee_percent):
    """
    CPM ve RPM Hesaplama
    """
    # 1. Gösterim (Impressions) Belirle
    views = row.get('avg_views', 0)
    
    # Eğer hiç video yoksa, Takipçi sayısının %10'unu izlenme varsay (Tahmini)
    is_estimated = False
    if views == 0:
        views = row.get('follower_count', 0) * 0.10
        is_estimated = True
    
    # Sıfıra bölme hatasını engellemek için minimum 1 yapıyoruz
    impressions = max(views, 1) 

    score = row.get('Score', 5)

    # --- CPM HESAPLAMA ---
    quality_multiplier = 0.5 + (score / 10) 
    final_cpm = base_cpm_input * quality_multiplier
    
    # Reklam Maliyeti (Ad Cost) = (İzlenme / 1000) * CPM
    estimated_ad_cost = (impressions / 1000) * final_cpm

    # --- RPM HESAPLAMA (GELİR) ---
    creator_share = 1 - (platform_fee_percent / 100)
    final_rpm = final_cpm * creator_share
    
    estimated_revenue = (impressions / 1000) * final_rpm
    
    return pd.Series([estimated_ad_cost, estimated_revenue, final_cpm, final_rpm, is_estimated], 
                     index=['Ad_Cost', 'Est_Revenue', 'CPM', 'RPM', 'Is_Estimated'])

# -----------------------------------------------------------------------------
# 3. ARAYÜZ (FRONTEND)
# -----------------------------------------------------------------------------

# --- GİRİŞ EKRANI ---
if not st.session_state['logged_in']:
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("<br><h1 style='text-align: center;'>🔒 B2B Giriş Paneli</h1>", unsafe_allow_html=True)
        with st.form("login"):
            email = st.text_input("Kullanıcı Adı")
            password = st.text_input("Şifre", type="password")
            if st.form_submit_button("Giriş Yap", use_container_width=True):
                try:
                    supabase.auth.sign_in_with_password({"email": email, "password": password})
                    st.session_state['logged_in'] = True
                    st.rerun()
                except:
                    st.error("Giriş Başarısız")

# --- DASHBOARD ---
else:
    # --- YAN MENÜ (DİNAMİK AYARLAR) ---
    with st.sidebar:
        st.title("⚙️ Pazar Ayarları")
        st.info("Formüller buradaki değerlere göre çalışır.")
        
        # Kullanıcı Girdileri
        base_cpm_input = st.number_input("Sektör Baz CPM ($)", value=5.0, min_value=0.1, step=0.5, help="1000 izlenme için ortalama Pazar Fiyatı")
        
        # --- HATA BURADAYDI, DÜZELTİLDİ ---
        platform_fee = st.slider("Ajans/Platform Kesintisi (%)", 0, 50, 20)
        # ----------------------------------
        
        st.markdown("---")
        st.subheader("Yeni Analiz")
        new_u = st.text_input("Instagram Kullanıcı Adı:")
        if st.button("Analiz Et 🚀"):
            if new_u:
                trigger_webhook(new_u)
                st.success("Analiz talebi Make.com'a iletildi.")
        
        st.markdown("---")
        if st.button("Çıkış Yap"):
            st.session_state['logged_in'] = False
            st.rerun()

    # --- ANA EKRAN ---
    st.title("📊 Influencer CPM & RPM Analizi")
    
    response = supabase.table('influencers').select("*").execute()
    
    if response.data:
        df = pd.DataFrame(response.data)
        
        # 1. Temel Veri Temizliği
        df['follower_count'] = pd.to_numeric(df['follower_count'], errors='coerce').fillna(0)
        
        # 2. Score'u Çek ve Temizle (0-10 Arasında Olmasını Garanti Et)
        def parse_score(text):
            try: 
                val = int(''.join(filter(str.isdigit, str(text).split("Score:")[1])))
                return min(max(val, 0), 10) 
            except: 
                return 5
        
        # AI verisi boşsa hata vermesin
        df['ai_analysis_raw'] = df['ai_analysis_raw'].fillna("")
        df['Score'] = df['ai_analysis_raw'].apply(parse_score)
        
        # 3. Video Analizi (JSON)
        video_stats = df.apply(analyze_posts_json, axis=1)
        df = pd.concat([df, video_stats], axis=1)
        
        # 4. Finansal Hesaplama (Kullanıcı Girdileriyle)
        financials = df.apply(calculate_financials, args=(base_cpm_input, platform_fee), axis=1)
        df = pd.concat([df, financials], axis=1)
        
        # --- SEKMELER ---
        tab1, tab2 = st.tabs(["📈 Genel Pazar Tablosu", "🎥 Detaylı Profil İnceleme"])
        
        with tab1:
            # KPI Kartları
            c1, c2, c3 = st.columns(3)
            c1.metric("Taban CPM", f"${base_cpm_input}")
            c2.metric("Ortalama Video İzlenme", f"{df['avg_views'].mean():,.0f}")
            c3.metric("Toplam Potansiyel Ciro", f"${df['Est_Revenue'].sum():,.0f}")
            
            # Ana Tablo
            st.dataframe(
                df[['username', 'avg_views', 'CPM', 'RPM', 'Ad_Cost', 'Est_Revenue', 'comment_quality']].style.format({
                    "CPM": "${:.2f}", 
                    "RPM": "${:.2f}",
                    "Ad_Cost": "${:,.2f}",
                    "Est_Revenue": "${:,.2f}",
                    "avg_views": "{:,.0f}"
                }), 
                use_container_width=True
            )
            
            # Grafik (Sadece Geçerli Veriler)
            df_chart = df[df['Ad_Cost'] > 0]
            if not df_chart.empty:
                st.subheader("Maliyet vs Gelir Analizi")
                fig = px.scatter(
                    df_chart, 
                    x="avg_views", 
                    y="RPM", 
                    size="Ad_Cost", 
                    color="Score",
                    hover_name="username",
                    title="İzlenme Arttıkça RPM Değişimi",
                    labels={"avg_views": "Ortalama İzlenme", "RPM": "RPM (Gelir)"}
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Grafik için yeterli video verisi yok.")

        with tab2:
            user_sel = st.selectbox("İncelenecek Influencer Seçin:", df['username'].unique())
            
            if user_sel:
                p = df[df['username'] == user_sel].iloc[0]
                
                # Detay Kartları
                st.subheader(f"Analiz: {p['username']}")
                
                c1, c2 = st.columns(2)
                with c1:
                    st.success(f"💰 **Tahmini Video Maliyeti:** ${p['Ad_Cost']:,.2f}")
                    st.info(f"💵 **Net Kazanç (RPM):** ${p['Est_Revenue']:,.2f}")
                    if p['Is_Estimated']:
                        st.warning("⚠️ Not: Video verisi çekilemediği için takipçi bazlı tahmin yapıldı.")
                
                with c2:
                    st.write(f"**Ortalama İzlenme:** {p['avg_views']:,.0f}")
                    st.write(f"**Yorum Kalitesi:** {p['comment_quality']}")
                    
                    # Score değerini 0 ile 10 arasına sıkıştırıp progress bar'a veriyoruz.
                    safe_score = min(max(p['Score'], 0), 10)
                    st.progress(safe_score / 10, text=f"AI Kalite Puanı: {safe_score}/10")

    else:
        st.info("Veritabanında henüz veri yok.")
