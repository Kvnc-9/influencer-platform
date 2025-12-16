import streamlit as st
from supabase import create_client
import pandas as pd
import requests
import json
import time
from datetime import datetime

# =============================================================================
# SAYFA YAPISI VE TASARIM
# =============================================================================
st.set_page_config(
    page_title="Influencer ROI Analizi", 
    layout="wide", 
    page_icon="🎯",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&display=swap');

    * {
        font-family: 'Inter', sans-serif;
    }

    /* ARKA PLAN */
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        background-attachment: fixed;
    }
    
    /* SIDEBAR */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }
    section[data-testid="stSidebar"] * {
        color: #e0e0e0 !important;
    }

    /* MODERN KARTLAR */
    .metric-card {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.2);
        margin-bottom: 20px;
        transition: transform 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 48px rgba(0, 0, 0, 0.15);
    }

    /* BAŞLIKLAR */
    .main-title {
        font-size: 3.5rem;
        font-weight: 800;
        color: white;
        text-align: center;
        margin-bottom: 10px;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    .subtitle {
        font-size: 1.2rem;
        font-weight: 300;
        color: rgba(255,255,255,0.9);
        text-align: center;
        margin-bottom: 40px;
    }

    /* INPUT ALANLARI */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input {
        background-color: rgba(255, 255, 255, 0.1) !important;
        border: 2px solid rgba(255, 255, 255, 0.3) !important;
        border-radius: 12px !important;
        color: white !important;
        padding: 12px 16px !important;
        font-size: 16px !important;
    }
    
    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus {
        border-color: #764ba2 !important;
        box-shadow: 0 0 0 3px rgba(118, 75, 162, 0.2) !important;
    }

    /* BUTONLAR */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 14px 32px;
        font-weight: 600;
        font-size: 16px;
        letter-spacing: 0.5px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(118, 75, 162, 0.4);
        width: 100%;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(118, 75, 162, 0.6);
    }

    /* TABLOLAR */
    .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
    }
    
    /* STEP INDICATOR */
    .step-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin: 30px 0;
        padding: 20px;
        background: rgba(255, 255, 255, 0.95);
        border-radius: 16px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
    }
    
    .step {
        flex: 1;
        text-align: center;
        position: relative;
    }
    
    .step-number {
        width: 50px;
        height: 50px;
        border-radius: 50%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto 10px;
        font-weight: 700;
        font-size: 20px;
        box-shadow: 0 4px 15px rgba(118, 75, 162, 0.4);
    }
    
    .step-number.inactive {
        background: #e0e0e0;
        box-shadow: none;
    }
    
    .step-title {
        font-weight: 600;
        color: #2d3748;
        font-size: 14px;
    }
    
    .step-line {
        position: absolute;
        top: 25px;
        left: 50%;
        width: 100%;
        height: 3px;
        background: #e0e0e0;
        z-index: -1;
    }

    /* SEÇİLİ INFLUENCER BADGE */
    .selected-badge {
        display: inline-block;
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        color: white;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        margin: 4px;
        box-shadow: 0 2px 8px rgba(17, 153, 142, 0.3);
    }
    
    /* UYARI KUTULARI */
    .stAlert {
        border-radius: 12px;
        border-left: 4px solid;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# SUPABASE BAĞLANTISI
# =============================================================================
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except:
    st.error("⚠️ Supabase bağlantı bilgileri eksik! Lütfen secrets ayarlarını kontrol edin.")
    st.stop()

@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

# =============================================================================
# SESSION STATE YÖNETİMİ
# =============================================================================
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'current_step' not in st.session_state:
    st.session_state['current_step'] = 1
if 'selected_influencers' not in st.session_state:
    st.session_state['selected_influencers'] = []
if 'budget_distribution' not in st.session_state:
    st.session_state['budget_distribution'] = {}

# =============================================================================
# YARDIMCI FONKSİYONLAR
# =============================================================================

def trigger_webhook(niche, count=10):
    """Make.com webhook'unu tetikler"""
    webhook_url = "https://hook.eu1.make.com/ixxd5cuuqkhhkpd8sqn5soiyol0a952x"
    try:
        params = {
            "niche": niche,
            "count": count
        }
        response = requests.get(webhook_url, params=params, timeout=10)
        return response.status_code == 200
    except Exception as e:
        st.error(f"Webhook hatası: {str(e)}")
        return False

def get_influencers_by_niche(niche, limit=10):
    """Supabase'den niche'e göre influencer'ları çeker"""
    try:
        response = supabase.table('influencers')\
            .select("*")\
            .ilike('niche', f'%{niche}%')\
            .limit(limit)\
            .execute()
        return response.data
    except Exception as e:
        st.error(f"Veri çekme hatası: {str(e)}")
        return []

def safe_json_parse(raw_data):
    """JSON verisini güvenli şekilde parse eder"""
    if not raw_data: 
        return []
    if isinstance(raw_data, list): 
        return raw_data
    if not isinstance(raw_data, str): 
        return []
    try:
        return json.loads(raw_data)
    except json.JSONDecodeError:
        try:
            return json.loads(f"[{raw_data}]")
        except:
            return []

def calculate_avg_views(posts_raw_data):
    """Son gönderilerin ortalama izlenme sayısını hesaplar"""
    posts = safe_json_parse(posts_raw_data)
    views_list = []
    
    if posts and isinstance(posts, list):
        for post in posts:
            views = post.get('videoViewCount') or post.get('playCount') or \
                   post.get('viewCount') or 0
            if views > 0:
                views_list.append(views)
    
    return int(sum(views_list) / len(views_list)) if views_list else 0

def calculate_metrics(avg_views, budget, product_price, ctr=0.02):
    """
    ROI metriklerini hesaplar
    
    Args:
        avg_views: Ortalama video izlenme sayısı
        budget: Influencer'a ödenecek tutar
        product_price: Ürün fiyatı
        ctr: Click-through rate (varsayılan %2)
    """
    if avg_views <= 0:
        return {
            'estimated_clicks': 0,
            'estimated_revenue': 0,
            'cpm': 0,
            'rpm': 0,
            'difference': 0,
            'roi_percent': 0,
            'is_profitable': False
        }
    
    # Tahmini tıklama sayısı (CTR * İzlenme)
    estimated_clicks = int(avg_views * ctr)
    
    # Tahmini gelir
    estimated_revenue = estimated_clicks * product_price
    
    # CPM (Cost Per Mille - 1000 izlenme başına maliyet)
    cpm = (budget / avg_views) * 1000
    
    # RPM (Revenue Per Mille - 1000 izlenme başına gelir)
    rpm = (estimated_revenue / avg_views) * 1000
    
    # Fark (RPM - CPM)
    difference = rpm - cpm
    
    # ROI % = ((Gelir - Maliyet) / Maliyet) * 100
    roi_percent = ((estimated_revenue - budget) / budget) * 100 if budget > 0 else 0
    
    return {
        'estimated_clicks': estimated_clicks,
        'estimated_revenue': estimated_revenue,
        'cpm': cpm,
        'rpm': rpm,
        'difference': difference,
        'roi_percent': roi_percent,
        'is_profitable': difference > 0
    }

def distribute_budget_optimally(influencers_data, total_budget):
    """
    Toplam bütçeyi influencer'lar arasında ROI'ye göre optimal dağıtır
    """
    # ROI'ye göre sırala (en yüksek fark önce)
    sorted_data = sorted(influencers_data, 
                        key=lambda x: x['metrics']['difference'], 
                        reverse=True)
    
    # Ağırlık hesapla (pozitif fark olanlar için)
    total_weight = sum(max(0, inf['metrics']['difference']) 
                      for inf in sorted_data)
    
    if total_weight == 0:
        # Hiç pozitif fark yoksa eşit dağıt
        budget_per_influencer = total_budget / len(sorted_data)
        for inf in sorted_data:
            inf['allocated_budget'] = budget_per_influencer
    else:
        # Ağırlıklı dağıtım
        for inf in sorted_data:
            weight = max(0, inf['metrics']['difference'])
            inf['allocated_budget'] = (weight / total_weight) * total_budget
    
    return sorted_data

# =============================================================================
# LOGIN EKRANI
# =============================================================================
if not st.session_state['logged_in']:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.markdown("""
            <div style='background: rgba(255,255,255,0.95); padding: 40px; 
                        border-radius: 20px; box-shadow: 0 8px 32px rgba(0,0,0,0.2);'>
                <h2 style='text-align: center; color: #2d3748; margin-bottom: 10px;'>
                    🎯 Influencer ROI Platform
                </h2>
                <p style='text-align: center; color: #718096; margin-bottom: 30px;'>
                    Giriş yaparak analiz sistemine erişin
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        email = st.text_input("📧 E-posta Adresi", placeholder="ornek@mail.com")
        password = st.text_input("🔒 Şifre", type="password", placeholder="••••••••")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("🚀 GİRİŞ YAP", use_container_width=True):
            if not email or not password:
                st.error("Lütfen tüm alanları doldurun!")
            else:
                with st.spinner("Giriş yapılıyor..."):
                    try:
                        user = supabase.auth.sign_in_with_password({
                            "email": email, 
                            "password": password
                        })
                        if user:
                            st.session_state['logged_in'] = True
                            st.success("✅ Giriş başarılı! Yönlendiriliyorsunuz...")
                            time.sleep(1)
                            st.rerun()
                    except Exception as e:
                        st.error("❌ Giriş bilgileri hatalı!")
    st.stop()

# =============================================================================
# ANA DASHBOARD
# =============================================================================

# SIDEBAR
with st.sidebar:
    st.markdown("### ⚙️ Ayarlar")
    st.markdown("---")
    
    if st.button("🚪 Çıkış Yap", use_container_width=True):
        st.session_state['logged_in'] = False
        st.session_state['current_step'] = 1
        st.session_state['selected_influencers'] = []
        st.rerun()
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("### 📊 İstatistikler")
    
    try:
        total_count = supabase.table('influencers').select("*", count='exact').execute()
        st.metric("Toplam Influencer", total_count.count or 0)
    except:
        st.metric("Toplam Influencer", "N/A")
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("### ℹ️ Hesaplama Mantığı")
    with st.expander("Formüller"):
        st.markdown("""
        **CPM (Cost Per Mille):**  
        `(Bütçe / İzlenme) × 1000`
        
        **RPM (Revenue Per Mille):**  
        `(Gelir / İzlenme) × 1000`
        
        **ROI (%):**  
        `((Gelir - Maliyet) / Maliyet) × 100`
        
        **Fark:**  
        `RPM - CPM`
        
        ✅ Fark > 0 → Kârlı  
        ❌ Fark < 0 → Zararlı
        """)

# ANA İÇERİK
st.markdown("<h1 class='main-title'>🎯 Influencer ROI Analizi</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>Akıllı bütçe dağılımı ve ROI tahmini</p>", unsafe_allow_html=True)

# STEP INDICATOR
steps = [
    ("1", "Kampanya Bilgileri", st.session_state['current_step'] >= 1),
    ("2", "Influencer Seçimi", st.session_state['current_step'] >= 2),
    ("3", "ROI Analizi", st.session_state['current_step'] >= 3)
]

st.markdown("<div class='step-container'>", unsafe_allow_html=True)
for i, (num, title, is_active) in enumerate(steps):
    active_class = "" if is_active else "inactive"
    st.markdown(f"""
        <div class='step'>
            <div class='step-number {active_class}'>{num}</div>
            <div class='step-title'>{title}</div>
        </div>
    """, unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# =============================================================================
# STEP 1: KAMPANYA BİLGİLERİ
# =============================================================================
if st.session_state['current_step'] == 1:
    st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
    st.markdown("### 📝 Kampanya Detayları")
    st.markdown("Lütfen kampanyanızın temel bilgilerini girin")
    st.markdown("</div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        st.markdown("#### 🎨 Niche (Kategori)")
        niche = st.text_input(
            "kategori",
            placeholder="Örn: teknoloji, moda, fitness, gaming...",
            label_visibility="collapsed"
        )
        st.caption("Ürününüzün hedef kategorisini girin")
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        st.markdown("#### 💰 Toplam Reklam Bütçesi")
        total_budget = st.number_input(
            "bütçe",
            min_value=100.0,
            value=10000.0,
            step=500.0,
            format="%.2f",
            label_visibility="collapsed"
        )
        st.caption("Influencer'lara ayıracağınız toplam bütçe ($)")
        st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
    st.markdown("#### 🏷️ Ürün Satış Fiyatı")
    product_price = st.number_input(
        "fiyat",
        min_value=1.0,
        value=50.0,
        step=5.0,
        format="%.2f",
        label_visibility="collapsed"
    )
    st.caption("Ürününüzün birim satış fiyatı ($)")
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    if st.button("🔍 INFLUENCER ARA", use_container_width=True, type="primary"):
        if not niche:
            st.error("❌ Lütfen bir niche girin!")
        else:
            with st.spinner(f"'{niche}' kategorisinde influencer'lar aranıyor..."):
                # Önce veritabanında ara
                influencers = get_influencers_by_niche(niche, 10)
                
                if not influencers or len(influencers) < 5:
                    # Yeterli veri yoksa webhook tetikle
                    st.info("Yeterli veri bulunamadı, yeni veri çekiliyor...")
                    if trigger_webhook(niche, 10):
                        st.success("Veri çekme isteği gönderildi! 30 saniye sonra tekrar deneyin.")
                        time.sleep(2)
                    else:
                        st.error("Veri çekme hatası!")
                else:
                    # Veriyi session state'e kaydet
                    st.session_state['niche'] = niche
                    st.session_state['total_budget'] = total_budget
                    st.session_state['product_price'] = product_price
                    st.session_state['influencers_raw'] = influencers
                    st.session_state['current_step'] = 2
                    st.success(f"✅ {len(influencers)} influencer bulundu!")
                    time.sleep(1)
                    st.rerun()

# =============================================================================
# STEP 2: INFLUENCER SEÇİMİ
# =============================================================================
elif st.session_state['current_step'] == 2:
    influencers = st.session_state.get('influencers_raw', [])
    
    if not influencers:
        st.warning("Influencer verisi bulunamadı!")
        if st.button("← Başa Dön"):
            st.session_state['current_step'] = 1
            st.rerun()
        st.stop()
    
    st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
    st.markdown("### 👥 Influencer Listesi")
    st.markdown(f"**Kategori:** {st.session_state.get('niche', 'N/A')} | "
                f"**Toplam Bütçe:** ${st.session_state.get('total_budget', 0):,.2f}")
    st.markdown("</div>", unsafe_allow_html=True)
    
    # DataFrame oluştur
    df_data = []
    for inf in influencers:
        avg_views = calculate_avg_views(inf.get('posts_raw_data'))
        df_data.append({
            'username': inf.get('username', 'N/A'),
            'followers': inf.get('followerCount', 0),
            'avg_views': avg_views,
            'engagement_rate': f"{(avg_views / inf.get('followerCount', 1) * 100):.2f}%" 
                              if inf.get('followerCount', 0) > 0 else "0%"
        })
    
    df = pd.DataFrame(df_data)
    
    st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
    st.dataframe(
        df.style.format({
            'followers': '{:,.0f}',
            'avg_views': '{:,.0f}'
        }),
        use_container_width=True,
        height=400
    )
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Geri", use_container_width=True):
            st.session_state['current_step'] = 1
            st.rerun()
    
    with col2:
        if st.button("ROI ANALİZİNE GEÇ →", use_container_width=True, type="primary"):
            st.session_state['current_step'] = 3
            st.rerun()

# =============================================================================
# STEP 3: ROI ANALİZİ VE BÜTÇE DAĞILIMI
# =============================================================================
elif st.session_state['current_step'] == 3:
    influencers = st.session_state.get('influencers_raw', [])
    total_budget = st.session_state.get('total_budget', 0)
    product_price = st.session_state.get('product_price', 0)
    
    if not influencers:
        st.warning("Veri bulunamadı!")
        if st.button("← Başa Dön"):
            st.session_state['current_step'] = 1
            st.rerun()
        st.stop()
    
    # CTR ayarı
    st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
    st.markdown("### ⚙️ Gelişmiş Ayarlar")
    ctr = st.slider(
        "Tahmini Tıklama Oranı (CTR %)",
        min_value=0.5,
        max_value=10.0,
        value=2.0,
        step=0.5,
        help="Video izleyicilerinin kaçının tıklayacağını tahmin eder"
    ) / 100
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Her influencer için metrikleri hesapla
    influencers_with_metrics = []
    for inf in influencers:
        avg_views = calculate_avg_views(inf.get('posts_raw_data'))
        
        if avg_views > 0:
            # Eşit bütçe payı (önce eşit dağıt, sonra optimize edilecek)
            initial_budget = total_budget / len(influencers)
            
            metrics = calculate_metrics(avg_views, initial_budget, product_price, ctr)
            
            influencers_with_metrics.append({
                'username': inf.get('username', 'N/A'),
                'followers': inf.get('followerCount', 0),
                'avg_views': avg_views,
                'metrics': metrics,
                'allocated_budget': initial_budget
            })
    
    # Bütçeyi optimal dağıt
    optimized_data = distribute_budget_optimally(influencers_with_metrics, total_budget)
    
    # Her influencer için metrikleri yeniden hesapla (optimize edilmiş bütçeyle)
    for inf_data in optimized_data:
        inf_data['metrics'] = calculate_metrics(
            inf_data['avg_views'],
            inf_data['allocated_budget'],
            product_price,
            ctr
        )
    
    # Sonuçları göster
    st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
    st.markdown("### 📊 ROI Analiz Sonuçları")
    st.markdown("Önerilen bütçe dağılımı ve karlılık tahmini")
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Özet metrikler
    col1, col2, col3, col4 = st.columns(4)
    
    total_estimated_revenue = sum(d['metrics']['estimated_revenue'] for d in optimized_data)
    total_estimated_roi = ((total_estimated_revenue - total_budget) / total_budget * 100) if total_budget > 0 else 0
    profitable_count = sum(1 for d in optimized_data if d['metrics']['is_profitable'])
    
    with col1:
        st.metric("💰 Tahmini Gelir", f"${total_estimated_revenue:,.2f}")
    with col2:
        st.metric("📈 Tahmini ROI", f"{total_estimated_roi:.2f}%")
    with col3:
        st.metric("✅ Karlı Influencer", f"{profitable_count}/{len(optimized_data)}")
    with col4:
        net_profit = total_estimated_revenue - total_budget
        st.metric("💵 Net Kâr/Zarar", f"${net_profit:,.2f}")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Detaylı tablo
    result_data = []
    for inf in optimized_data:
        result_data.append({
            'Kullanıcı Adı': f"@{inf['username']}",
            'Takipçi': inf['followers'],
            'Ort. İzlenme': inf['avg_views'],
            'Önerilen Bütçe ($)': inf['allocated_budget'],
            'Tahmini Tıklama': inf['metrics']['estimated_clicks'],
            'Tahmini Gelir ($)': inf['metrics']['estimated_revenue'],
            'CPM ($)': inf['metrics']['cpm'],
            'RPM ($)': inf['metrics']['rpm'],
            'Fark ($)': inf['metrics']['difference'],
            'ROI (%)': inf['metrics']['roi_percent']
        })
