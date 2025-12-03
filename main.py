import streamlit as st
from supabase import create_client
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import time
import requests
import json
import numpy as np

# -----------------------------------------------------------------------------
# 1. AYARLAR VE GÜVENLİK
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Influencer CPM/RPM Analiz", layout="wide", page_icon="📊")

# CSS: Kartlar ve Renkler
st.markdown("""
<style>
    .metric-card {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .big-font { font-size: 24px !important; font-weight: bold; color: #333; }
    .small-font { font-size: 14px !important; color: #666; }
</style>
""", unsafe_allow_html=True)

try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except:
    st.error("⚠️ Secrets ayarları eksik!")
    st.stop()

@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# -----------------------------------------------------------------------------
# 2. ANALİZ MOTORU (CPM, RPM, VIDEO)
# -----------------------------------------------------------------------------

def trigger_webhook(username):
    # SONUNDA ?username= OLMADAN TEMİZ LINK:
    webhook_url = "https://hook.eu2.make.com/BURAYA_SENIN_MAKE_LINKIN" 
    try:
        requests.get(f"{webhook_url}?username={username}")
        return True
    except:
        return False

def analyze_posts_json(row):
    """
    JSON paketini açar, video izlenmelerini ve yorumları analiz eder.
    """
    raw_data = row.get('posts_raw_data')
    
    # Varsayılan Değerler
    stats = {
        "avg_views": 0,
        "total_likes": 0,
        "comment_quality": "Düşük Etkileşim ⚠️",
        "top_comment_likes": 0,
        "video_count": 0
    }
    
    if not raw_data:
        return pd.Series(stats)
    
    # JSON verisi bazen string gelir, bazen liste. Kontrol edelim.
    if isinstance(raw_data, str):
        try:
            posts = json.loads(raw_data)
        except:
            return pd.Series(stats)
    else:
        posts = raw_data

    # --- ANALİZ DÖNGÜSÜ ---
    views_list = []
    max_comment_likes = 0
    total_likes = 0
    
    if isinstance(posts, list):
        for post in posts:
            # 1. Video İzlenmesi (Sadece video/reel ise)
            # Apify genelde 'videoViewCount' veya 'playCount' verir
            views = post.get('videoViewCount') or post.get('playCount') or 0
            if views > 0:
                views_list.append(views)
            
            # 2. Toplam Beğeni
            total_likes += post.get('likesCount', 0)

            # 3. Yorum Analizi (En çok beğenilen yorumu bul)
            # Apify 'previewComments' veya 'latestComments' içinde liste verir
            comments = post.get('previewComments', []) or post.get('latestComments', [])
            if comments and isinstance(comments, list):
                for c in comments:
                    c_likes = c.get('likesCount', 0)
                    if c_likes > max_comment_likes:
                        max_comment_likes = c_likes

    # --- SONUÇLARI HESAPLA ---
    if views_list:
        stats["avg_views"] = int(sum(views_list) / len(views_list))
        stats["video_count"] = len(views_list)
    
    stats["total_likes"] = total_likes
    stats["top_comment_likes"] = max_comment_likes
    
    # Yorum Kalite Kontrolü (>100 Beğeni)
    if max_comment_likes >= 100:
        stats["comment_quality"] = "🔥 Yüksek Etkileşim (Topluluk Güçlü)"
    elif max_comment_likes > 20:
        stats["comment_quality"] = "✅ Orta Seviye"
    else:
        stats["comment_quality"] = "⚠️ Düşük (Yorumlar Beğenilmiyor)"
        
    return pd.Series(stats)

def calculate_financials(row):
    """
    CPM ve RPM Hesaplama
    """
    # Verileri al
    views = row.get('avg_views', 0)
    score = row.get('Score', 5)
    
    # Eğer izlenme verisi yoksa (Video atmıyorsa) takipçiden yola çık (Fallback)
    if views == 0:
        impressions = row.get('follower_count', 0) * 0.10 # Takipçinin %10'u görür tahmini
    else:
        impressions = views # Gerçek izlenme = Impression

    if impressions == 0: impressions = 1000 # Bölme hatası olmasın diye

    # --- 1. MALİYET (AD COST) HESABI ---
    # Formül: Pazar ortalaması 1000 izlenme başına 5$ - 15$ arasıdır.
    # Kalite puanı yüksekse Influencer daha pahalıdır.
    base_cost_per_view = 0.008 # İzlenme başına 0.008$ (8$ CPM tabanı)
    cost_multiplier = 1 + (score / 20) # Puan 10 ise 1.5x çarpan
    
    estimated_ad_cost = impressions * base_cost_per_view * cost_multiplier

    # --- 2. CPM (Cost Per Mille) ---
    # Formül: (Cost / Impressions) * 1000
    cpm = (estimated_ad_cost / impressions) * 1000
    
    # --- 3. REVENUE (GELİR) TAHMİNİ ---
    # Bu reklamdan ne kadar kazanırız? 
    # ROI Faktörü: Puan * Etkileşim
    # Formül: Yatırılan para x (1.5 ile 5.0 arası getiri)
    roi_factor = (score * 0.3) + 1.2 
    estimated_revenue = estimated_ad_cost * roi_factor
    
    # --- 4. RPM (Revenue Per Mille) ---
    # Formül: (Total Revenue / Impressions) * 1000
    rpm = (estimated_revenue / impressions) * 1000

    return pd.Series([estimated_ad_cost, estimated_revenue, cpm, rpm], 
                     index=['Ad_Cost', 'Est_Revenue', 'CPM ($)', 'RPM ($)'])

# -----------------------------------------------------------------------------
# 3. ARAYÜZ
# -----------------------------------------------------------------------------

# --- GİRİŞ EKRANI ---
if not st.session_state['logged_in']:
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("<br><br><h1 style='text-align: center;'>🔒 Video Analiz Giriş</h1>", unsafe_allow_html=True)
        with st.form("login"):
            email = st.text_input("Kullanıcı Adı")
            password = st.text_input("Şifre", type="password")
            if st.form_submit_button("Giriş Yap", use_container_width=True):
                try:
                    supabase.auth.sign_in_with_password({"email": email, "password": password})
                    st.session_state['logged_in'] = True
                    st.rerun()
                except:
                    st.error("Hatalı Giriş")

# --- DASHBOARD ---
else:
    with st.sidebar:
        st.title("⚙️ Kontrol")
        if st.button("Çıkış Yap"):
            st.session_state['logged_in'] = False
            st.rerun()

    st.title("📊 Influencer Video & CPM Analizi")
    
    response = supabase.table('influencers').select("*").execute()
    
    if response.data:
        df = pd.DataFrame(response.data)
        
        # --- VERİ İŞLEME ---
        # 1. AI Puanını Ayrıştır
        def parse_ai_score(text):
            try: return int(''.join(filter(str.isdigit, str(text).split("Score:")[1])))
            except: return 5
        df['Score'] = df['ai_analysis_raw'].apply(parse_ai_score)
        
        # 2. JSON Analizi (Video İzlenmeleri & Yorumlar)
        video_stats = df.apply(analyze_posts_json, axis=1)
        df = pd.concat([df, video_stats], axis=1)
        
        # 3. Finansal Hesaplama (CPM / RPM)
        financials = df.apply(calculate_financials, axis=1)
        df = pd.concat([df, financials], axis=1)
        
        # --- SEKMELER ---
        tab1, tab2, tab3 = st.tabs(["🎥 Video Performans & CPM", "⚔️ Karşılaştırma", "🕵️ Yeni Analiz"])
        
        # TAB 1: DETAYLI VIDEO ANALİZİ
        with tab1:
            st.subheader("Profil Detayları")
            selected_user = st.selectbox("İncelenecek Influencer:", df['username'].unique())
            
            p = df[df['username'] == selected_user].iloc[0]
            
            # ÜST KARTLAR (KPI)
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Ortalama Video İzlenme", f"{p['avg_views']:,.0f}")
            c2.metric("Tahmini Maliyet (Post Başı)", f"${p['Ad_Cost']:,.0f}")
            c3.metric("CPM (1000 Gösterim Maliyeti)", f"${p['CPM ($)']:.2f}")
            c4.metric("RPM (1000 Gösterim Geliri)", f"${p['RPM ($)']:.2f}", delta=f"{((p['RPM ($)']/p['CPM ($)'])-1)*100:.0f}% Kâr")
            
            st.divider()
            
            # YORUM VE ETKİLEŞİM KALİTESİ
            col_left, col_right = st.columns([1, 2])
            
            with col_left:
                st.markdown("### 💬 Topluluk Kalitesi")
                st.info(f"Yorum Durumu: **{p['comment_quality']}**")
                st.write(f"En çok beğenilen yorum **{p['top_comment_likes']}** beğeni aldı.")
                
                if p['top_comment_likes'] > 100:
                    st.success("MÜKEMMEL: Takipçiler yorumları okuyor ve beğeniyor. Topluluk canlı.")
                else:
                    st.warning("ZAYIF: Takipçiler yorumlarla pek ilgilenmiyor.")
                    
            with col_right:
                st.markdown("### 📈 CPM vs RPM Dengesi")
                # Bar Chart: Maliyet vs Gelir
                chart_data = pd.DataFrame({
                    'Metrik': ['Maliyet (CPM)', 'Gelir (RPM)'],
                    'Değer ($)': [p['CPM ($)'], p['RPM ($)']]
                })
                fig = px.bar(chart_data, x='Metrik', y='Değer ($)', color='Metrik', text_auto='.2f')
                st.plotly_chart(fig, use_container_width=True)

        # TAB 2: KARŞILAŞTIRMA
        with tab2:
            st.subheader("Hangi Influencer Daha Kârlı?")
            
            # Scatter Plot: X=İzlenme, Y=RPM
            fig_comp = px.scatter(
                df, 
                x="avg_views", 
                y="RPM ($)", 
                size="Ad_Cost", 
                color="Score",
                hover_name="username",
                title="İzlenme vs Gelir Potansiyeli (Balon Boyutu = Maliyet)",
                labels={"avg_views": "Ortalama İzlenme", "RPM ($)": "RPM (Gelir)"}
            )
            st.plotly_chart(fig_comp, use_container_width=True)
            
            st.dataframe(
                df[['username', 'avg_views', 'CPM ($)', 'RPM ($)', 'comment_quality']], 
                use_container_width=True
            )

        # TAB 3: YENİ ANALİZ
        with tab3:
            st.subheader("Yeni Veri Çek")
            new_u = st.text_input("Kullanıcı Adı:")
            if st.button("Make.com'u Tetikle 🚀"):
                if new_u:
                    trigger_webhook(new_u)
                    st.success("Talep gönderildi. 1-2 dakika içinde 'Video Performans' sekmesine düşecek.")

    else:
        st.info("Veri yok.")
