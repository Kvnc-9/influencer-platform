import streamlit as st
from supabase import create_client
import pandas as pd
import plotly.express as px
import time
import requests
import json

# -----------------------------------------------------------------------------
# 1. AYARLAR VE GÜVENLİK
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Influencer CPM/RPM Pro", layout="wide", page_icon="📊")

# CSS: Kartlar
st.markdown("""
<style>
    .metric-card {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 15px;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
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
# 2. ANALİZ MOTORU
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
    """JSON paketini açar, video izlenmelerini analiz eder."""
    raw_data = row.get('posts_raw_data')
    stats = {"avg_views": 0, "total_likes": 0, "comment_quality": "Veri Yok", "top_comment_likes": 0}
    
    if not raw_data: return pd.Series(stats)
    
    try:
        posts = json.loads(raw_data) if isinstance(raw_data, str) else raw_data
    except:
        return pd.Series(stats)

    views_list = []
    max_comment_likes = 0
    total_likes = 0
    
    if isinstance(posts, list):
        for post in posts:
            # Video İzlenmesi
            views = post.get('videoViewCount') or post.get('playCount') or 0
            if views > 0: views_list.append(views)
            
            total_likes += post.get('likesCount', 0)
            
            # Yorum Analizi
            comments = post.get('previewComments', []) or post.get('latestComments', [])
            if isinstance(comments, list):
                for c in comments:
                    c_likes = c.get('likesCount', 0)
                    if c_likes > max_comment_likes: max_comment_likes = c_likes

    if views_list:
        stats["avg_views"] = int(sum(views_list) / len(views_list))
    
    stats["total_likes"] = total_likes
    stats["top_comment_likes"] = max_comment_likes
    
    if max_comment_likes >= 100: stats["comment_quality"] = "🔥 Yüksek"
    elif max_comment_likes > 20: stats["comment_quality"] = "✅ Orta"
    else: stats["comment_quality"] = "⚠️ Düşük"
        
    return pd.Series(stats)

def calculate_financials(row, base_cpm_input, platform_fee_percent):
    """
    DİNAMİK HESAPLAMA: Kullanıcının girdiği CPM değerlerine göre hesaplar.
    """
    # 1. İzlenme Verisi (Yoksa Takipçinin %5'i varsay)
    views = row.get('avg_views', 0)
    if views == 0:
        views = row.get('follower_count', 0) * 0.05
    
    if views <= 0: return pd.Series([0, 0, 0, 0], index=['Ad_Cost', 'Est_Revenue', 'CPM', 'RPM'])

    score = row.get('Score', 5)

    # --- CPM HESABI (Cost Per Mille) ---
    # Kullanıcının girdiği Taban CPM * Kalite Çarpanı
    # Örn: Kullanıcı 5$ girdi, Puan 10 ise CPM 7.5$ olur.
    quality_multiplier = 1 + (score / 20) 
    final_cpm = base_cpm_input * quality_multiplier
    
    # Toplam Maliyet = (İzlenme / 1000) * CPM
    estimated_ad_cost = (views / 1000) * final_cpm

    # --- RPM HESABI (Revenue Per Mille) ---
    # Markanın ödediği paradan (CPM), platform kesintisi çıktıktan sonra kalan.
    # Örn: %30 ajans/platform payı varsa, Influencer %70 alır.
    creator_share = 1 - (platform_fee_percent / 100)
    final_rpm = final_cpm * creator_share
    
    estimated_revenue = (views / 1000) * final_rpm

    return pd.Series([estimated_ad_cost, estimated_revenue, final_cpm, final_rpm], 
                     index=['Ad_Cost', 'Est_Revenue', 'CPM', 'RPM'])

# -----------------------------------------------------------------------------
# 3. ARAYÜZ
# -----------------------------------------------------------------------------

# --- GİRİŞ EKRANI ---
if not st.session_state['logged_in']:
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("<br><h1 style='text-align: center;'>🔒 B2B Giriş</h1>", unsafe_allow_html=True)
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
        st.title("⚙️ Pazar Parametreleri")
        st.info("Hesaplamalar buradaki değerlere göre anlık güncellenir.")
        
        # KULLANICI GİRDİLERİ (INPUTS)
        base_cpm_input = st.number_input("Sektör Taban CPM ($)", value=5.0, min_value=0.1, step=0.5, help="1000 izlenme başına ortalama pazar fiyatı.")
        platform_fee = st.slider("Ajans/Platform Kesintisi (%)", 0, 50, 20)
        
        st.markdown("---")
        st.subheader("Yeni Analiz")
        new_u = st.text_input("Kullanıcı Adı:")
        if st.button("Analiz Et 🚀"):
            if new_u:
                trigger_webhook(new_u)
                st.success("İstek Gönderildi!")
        
        st.markdown("---")
        if st.button("Çıkış Yap"):
            st.session_state['logged_in'] = False
            st.rerun()

    # --- ANA EKRAN ---
    st.title("📊 Influencer CPM/RPM Paneli")
    
    response = supabase.table('influencers').select("*").execute()
    
    if response.data:
        df = pd.DataFrame(response.data)
        
        # 1. Veri Temizliği (Hata önleyici)
        df['follower_count'] = pd.to_numeric(df['follower_count'], errors='coerce').fillna(0)
        
        # 2. AI Puanını Al
        def parse_score(text):
            try: return int(''.join(filter(str.isdigit, str(text).split("Score:")[1])))
            except: return 5
        df['Score'] = df['ai_analysis_raw'].apply(parse_score)
        
        # 3. Video Analizi
        video_stats = df.apply(analyze_posts_json, axis=1)
        df = pd.concat([df, video_stats], axis=1)
        
        # 4. Finansal Hesaplama (Kullanıcı girdisine göre)
        # apply içinde args kullanarak sidebar değerlerini gönderiyoruz
        financials = df.apply(calculate_financials, args=(base_cpm_input, platform_fee), axis=1)
        df = pd.concat([df, financials], axis=1)
        
        # --- SEKMELER ---
        tab1, tab2 = st.tabs(["📈 Genel Tablo", "🎥 Detaylı Video Analizi"])
        
        with tab1:
            # KPI Kartları
            c1, c2, c3 = st.columns(3)
            c1.metric("Taban CPM", f"${base_cpm_input}")
            c2.metric("Ortalama RPM", f"${df['RPM'].mean():.2f}")
            c3.metric("Toplam Tahmini Ciro", f"${df['Est_Revenue'].sum():,.0f}")
            
            # Ana Tablo
            st.dataframe(
                df[['username', 'avg_views', 'CPM', 'RPM', 'Ad_Cost', 'Est_Revenue']].style.format({
                    "CPM": "${:.2f}", 
                    "RPM": "${:.2f}",
                    "Ad_Cost": "${:,.0f}",
                    "Est_Revenue": "${:,.0f}",
                    "avg_views": "{:,.0f}"
                }), 
                use_container_width=True
            )
            
            # Grafik (HATA DÜZELTİLDİ: Sadece verisi olanları çiz)
            df_chart = df[(df['Ad_Cost'] > 0) & (df['avg_views'] > 0)]
            
            if not df_chart.empty:
                st.subheader("Maliyet vs Gelir Analizi")
                fig = px.scatter(
                    df_chart, 
                    x="avg_views", 
                    y="RPM", 
                    size="Ad_Cost", # Balon boyutu maliyet
                    color="Score",
                    hover_name="username",
                    title="İzlenme Arttıkça RPM Nasıl Değişiyor?",
                    labels={"avg_views": "Ortalama İzlenme", "RPM": "RPM (Gelir)"}
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Grafik için yeterli video verisi yok.")

        with tab2:
            user_sel = st.selectbox("Detaylı İncele:", df['username'].unique())
            p = df[df['username'] == user_sel].iloc[0]
            
            c1, c2 = st.columns(2)
            with c1:
                st.success(f"💰 **Tahmini Video Maliyeti:** ${p['Ad_Cost']:,.2f}")
                st.info(f"💵 **Tahmini Kazanç (RPM):** ${p['Est_Revenue']:,.2f}")
            with c2:
                st.write(f"**Ortalama İzlenme:** {p['avg_views']:,.0f}")
                st.write(f"**Yorum Kalitesi:** {p['comment_quality']}")
                st.progress(p['Score']/10, f"AI Kalite Puanı: {p['Score']}/10")

    else:
        st.info("Veri yok.")
