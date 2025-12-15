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

# CSS TASARIMI (Aynı Kaldı)
st.markdown("""
<style>
    /* ARKA PLAN */
    .stApp {
        background: linear-gradient(135deg, #240b36 0%, #c31432 100%);
        background-attachment: fixed;
        color: white;
    }
    /* SIDEBAR */
    section[data-testid="stSidebar"] {
        background-color: rgba(0, 0, 0, 0.2);
        backdrop-filter: blur(20px);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }
    /* KUTULAR */
    .metric-container {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 15px;
        padding: 25px;
        margin-bottom: 20px;
        border: 1px solid rgba(255, 255, 255, 0.2);
        backdrop-filter: blur(10px);
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
    }
    /* TABLO */
    .stDataFrame {
        background-color: rgba(0, 0, 0, 0.3);
        border-radius: 10px;
        padding: 10px;
    }
    /* METİNLER */
    h1, h2, h3 { color: white !important; font-family: 'Helvetica Neue', sans-serif; font-weight: 700; }
    label { color: #e0e0e0 !important; font-weight: bold; }
    /* INPUT */
    div[data-baseweb="input"] {
        background-color: rgba(0, 0, 0, 0.3) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important; 
        color: white !important;
    }
    input { color: white !important; }
    /* KAZANAN KARTI */
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

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# -----------------------------------------------------------------------------
# 2. FONKSİYONLAR
# -----------------------------------------------------------------------------

def trigger_webhook(username):
    webhook_url = "https://hook.eu1.make.com/ixxd5cuuqkhhkpd8sqn5soiyol0a952x"
    try:
        requests.get(f"{webhook_url}?username={username}")
        return True
    except:
        return False

def clear_database():
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

def calculate_roi_metrics(row, ad_cost, base_clicks, product_price, global_avg_views):
    """
    DÜZELTİLMİŞ HESAPLAMA MANTIĞI (CPM & RPM & NICHE Odaklı):
    Artık herkesin kârı aynı çıkmayacak. İzlenme sayısına ve Kategoriye göre değişecek.
    """
    views = row.get('avg_views', 0)
    niche = row.get('Niche', 'Genel')
    
    if views <= 0:
        return pd.Series([0, 0, 0, 0, 0], index=['CPM ($)', 'RPM ($)', 'Net Kâr ($)', 'ROI (x)', 'Brand Score'])

    # --- 1. NICHE (KATEGORİ) ÇARPANLARI ---
    # Bazı kategoriler daha değerlidir (Daha yüksek dönüşüm/tıklama getirir)
    niche_weights = {
        'Tech': 1.3,       # Teknoloji izleyicisi daha çok tıklar
        'Business': 1.3,
        'Finance': 1.4,
        'Fashion': 1.2,
        'Beauty': 1.2,
        'Gaming': 1.1,
        'Travel': 1.0,
        'Food': 0.9,
        'General': 0.8,    # Genel mizah sayfalarının dönüşümü düşüktür
        'Comedy': 0.8
    }
    # Eğer kategori listede yoksa varsayılan 1.0 al
    niche_multiplier = niche_weights.get(niche, 1.0)

    # --- 2. DİNAMİK TIKLAMA TAHMİNİ ---
    # Kullanıcının girdiği "Beklenen Tıklama" (base_clicks) ortalama bir hesap içindir.
    # Bunu şu anki Influencer'ın izlenmesine göre oranlıyoruz (Scale ediyoruz).
    # Formül: (Kendi İzlenmesi / Ortamala İzlenme) * Baz Tıklama * Niche Gücü
    view_performance_ratio = views / global_avg_views if global_avg_views > 0 else 1
    
    estimated_clicks = base_clicks * view_performance_ratio * niche_multiplier
    
    # --- 3. METRİKLER ---
    
    # CPM (Cost Per Mille): 1000 izlenme maliyeti
    # İzlenmesi yüksek olanın CPM'i düşük çıkar (İyi bir şey)
    cpm = (ad_cost / views) * 1000
    
    # Tahmini Gelir (Revenue)
    estimated_revenue = estimated_clicks * product_price
    
    # RPM (Revenue Per Mille): 1000 izlenme başına kazanç
    rpm = (estimated_revenue / views) * 1000
    
    # Net Kâr
    net_profit = estimated_revenue - ad_cost
    
    # ROI Çarpanı
    roi_x = estimated_revenue / ad_cost if ad_cost > 0 else 0
    
    # Brand Score (Marka Puanı)
    # ROI ve Niche Kalitesine göre 0-100 arası puan
    # Niche çarpanı yüksekse puanı artırır.
    raw_score = (roi_x * 20) + (niche_multiplier * 20)
    brand_score = min(99, max(1, int(raw_score)))
    
    return pd.Series([cpm, rpm, net_profit, roi_x, brand_score], 
                     index=['CPM ($)', 'RPM ($)', 'Net Kâr ($)', 'ROI (x)', 'Brand Score'])

# -----------------------------------------------------------------------------
# 3. ARAYÜZ
# -----------------------------------------------------------------------------

if not st.session_state['logged_in']:
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown("<br><br><h1 style='text-align: center;'>🔐 GİRİŞ</h1>", unsafe_allow_html=True)
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

    st.title("📈 Influencer ROI Simülatörü")
    st.markdown("Yapay Zeka Destekli Finansal Analiz Aracı")
    
    with st.container():
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("### 💸 Maliyet")
            ad_cost = st.number_input("Influencer Bütçesi ($)", value=1000, step=100)
        with c2:
            st.markdown("### 🖱️ Ort. Tıklama")
            exp_clicks = st.number_input("Beklenen Tıklama (Ortalama)", value=500, step=50, help="Ortalama bir influencer için beklenen tıklama.")
        with c3:
            st.markdown("### 🏷️ Ürün")
            prod_price = st.number_input("Ürün Fiyatı ($)", value=30.0, step=5.0)
        st.markdown('</div>', unsafe_allow_html=True)

    response = supabase.table('influencers').select("*").execute()
    
    if response.data:
        df = pd.DataFrame(response.data)
        
        if 'Niche' not in df.columns:
            if 'niche' in df.columns: df['Niche'] = df['niche']
            else: df['Niche'] = "Genel"
        df['Niche'] = df['Niche'].fillna("Genel").replace("", "Genel")

        # 1. İzlenmeleri Hesapla
        df['avg_views'] = df.apply(get_avg_views_from_json, axis=1)
        
        # 2. Tüm listenin ortalama izlenmesini bul (Karşılaştırma için)
        global_avg_views = df[df['avg_views'] > 0]['avg_views'].mean()
        if pd.isna(global_avg_views) or global_avg_views == 0:
            global_avg_views = 1  # 0'a bölme hatasını önle

        # 3. Metrikleri Hesapla (Artık global_avg_views parametresi gönderiyoruz)
        metrics = df.apply(calculate_roi_metrics, args=(ad_cost, exp_clicks, prod_price, global_avg_views), axis=1)
        df = pd.concat([df, metrics], axis=1)
        
        df_valid = df[df['avg_views'] > 0].copy()
        
        if not df_valid.empty:
            df_valid = df_valid.sort_values(by="Net Kâr ($)", ascending=False)
            
            # --- 🏆 KAZANAN ---
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
                st.error("⚠️ Bu bütçeyle kârlı bir seçenek bulunamadı. Beklenen tıklamayı artırın veya bütçeyi düşürün.")

            # --- TABLO ---
            st.subheader("📋 Detaylı Finansal Tablo")
            
            cols = ['username', 'Niche', 'avg_views', 'Brand Score', 'CPM ($)', 'RPM ($)', 'ROI (x)', 'Net Kâr ($)']
            
            # HATA VERMEYEN GÜVENLİ RENKLENDİRME (Matplotlib'siz)
            def safe_highlight(val):
                try:
                    # Sayısal değer değilse renklendirme
                    if isinstance(val, str): return ''
                    color = '#d4edda' if val > 0 else '#f8d7da'
                    return f'background-color: {color}; color: black;'
                except:
                    return ''

            st.dataframe(
                df_valid[cols].style.format({
                    "avg_views": "{:,.0f}",
                    "Brand Score": "{:.0f}",
                    "CPM ($)": "${:.2f}",
                    "RPM ($)": "${:.2f}",
                    "ROI (x)": "{:.2f}x",
                    "Net Kâr ($)": "${:+.2f}"
                }).applymap(safe_highlight, subset=['Net Kâr ($)']),
                use_container_width=True,
                height=400
            )
            
            # --- GRAFİK ---
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
                title="Maliyet vs Gelir Analizi (Sağ Üst = En İyi)",
                labels={"CPM ($)": "Maliyet (CPM)", "RPM ($)": "Gelir (RPM)"},
                height=600,
                template="plotly_dark"
            )
            
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color="white")
            )
            fig.update_traces(textposition='top center')
            
            # Çizgiyi dinamik ayarla
            max_x = df_valid['CPM ($)'].max()
            max_y = df_valid['RPM ($)'].max()
            limit = max(max_x, max_y) * 1.1 if max_x and max_y else 100
            
            fig.add_shape(
                type="line", line=dict(dash='dash', color="gray"),
                x0=0, y0=0, x1=limit, y1=limit
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
        else:
            st.warning("Veri var ama videolu gönderi bulunamadı.")
    else:
        st.info("Listeniz boş. Sol menüden analiz başlatın.")
