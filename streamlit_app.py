import streamlit as st
import tempfile
import os

# SET PAGE CONFIG FIRST (required by Streamlit)
st.set_page_config(page_title="Food Label Analyzer", layout="wide", page_icon="⬡")

# ── Global CSS + animated background ──────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=Space+Mono:wght@400;700&display=swap');

html, body, [data-testid="stAppViewContainer"] {
    background-color: #050d1a !important;
    font-family: 'DM Sans', sans-serif !important;
    color: #e2eaf5 !important;
}
[data-testid="stAppViewContainer"] > .main { background: transparent !important; }
[data-testid="block-container"] { padding-top: 1.5rem !important; }

/* Animated dot-grid background */
[data-testid="stAppViewContainer"]::before {
    content: '';
    position: fixed;
    top: 0; left: 0;
    width: 100%; height: 100%;
    background-image: radial-gradient(circle, rgba(0,212,170,0.04) 1px, transparent 1px);
    background-size: 38px 38px;
    z-index: 0;
    pointer-events: none;
    animation: gridFloat 22s linear infinite;
}
@keyframes gridFloat {
    0%   { background-position: 0 0; }
    100% { background-position: 38px 38px; }
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: rgba(5,10,22,0.98) !important;
    border-right: 1px solid rgba(0,212,170,0.14) !important;
}
[data-testid="stSidebar"] * { font-family: 'DM Sans', sans-serif !important; color: #5a8aaa !important; }
[data-testid="stSidebar"] .stRadio label {
    color: #5a8aaa !important; font-size: 13px !important;
    padding: 8px 4px !important; transition: color 0.2s !important;
}
[data-testid="stSidebar"] .stRadio label:hover { color: #00d4aa !important; }
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 { color: #00d4aa !important; }

/* Metric cards */
[data-testid="stMetric"] {
    background: rgba(10,22,45,0.88) !important;
    border: 1px solid rgba(0,212,170,0.13) !important;
    border-radius: 12px !important;
    padding: 18px 16px !important;
    border-top: 2px solid #00d4aa !important;
}
[data-testid="stMetricLabel"] {
    font-family: 'Space Mono', monospace !important;
    font-size: 10px !important; color: #4a7a9b !important;
    letter-spacing: 1.5px !important; text-transform: uppercase !important;
}
[data-testid="stMetricValue"] {
    font-family: 'Space Mono', monospace !important;
    font-size: 26px !important; color: #00d4aa !important; font-weight: 300 !important;
}
[data-testid="stMetricDelta"] { font-family: 'Space Mono', monospace !important; font-size: 11px !important; }

/* Dataframes */
[data-testid="stDataFrame"] {
    background: rgba(10,22,45,0.85) !important;
    border: 1px solid rgba(0,212,170,0.1) !important;
    border-radius: 10px !important;
}

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, rgba(0,212,170,0.14), rgba(0,212,170,0.05)) !important;
    border: 1px solid rgba(0,212,170,0.4) !important;
    border-radius: 8px !important; color: #00d4aa !important;
    font-family: 'Space Mono', monospace !important;
    font-size: 11px !important; letter-spacing: 1px !important;
    padding: 10px 24px !important; transition: all 0.2s !important;
}
.stButton > button:hover {
    background: rgba(0,212,170,0.22) !important;
    border-color: #00d4aa !important;
    box-shadow: 0 0 18px rgba(0,212,170,0.18) !important;
}

/* Inputs */
.stTextInput > div > input, .stNumberInput > div > input {
    background: rgba(10,22,45,0.9) !important;
    border: 1px solid rgba(0,212,170,0.2) !important;
    border-radius: 8px !important; color: #e2eaf5 !important;
    font-family: 'DM Sans', sans-serif !important;
}
.stSelectbox > div > div {
    background: rgba(10,22,45,0.9) !important;
    border: 1px solid rgba(0,212,170,0.2) !important;
    border-radius: 8px !important; color: #e2eaf5 !important;
}
.stMultiSelect > div > div {
    background: rgba(10,22,45,0.9) !important;
    border: 1px solid rgba(0,212,170,0.2) !important;
    border-radius: 8px !important;
}

/* File uploader */
[data-testid="stFileUploader"] {
    background: rgba(10,22,45,0.7) !important;
    border: 1px dashed rgba(0,212,170,0.3) !important;
    border-radius: 10px !important;
}

/* Expanders */
.streamlit-expanderHeader {
    background: rgba(8,18,35,0.92) !important;
    border: 1px solid rgba(0,212,170,0.12) !important;
    border-radius: 10px !important; color: #a0c8e8 !important; font-size: 13px !important;
}
.streamlit-expanderContent {
    background: rgba(10,22,45,0.72) !important;
    border: 1px solid rgba(0,212,170,0.08) !important; border-top: none !important;
}

/* Alerts */
.stAlert {
    background: rgba(10,22,45,0.88) !important;
    border-radius: 10px !important; border-left: 3px solid #00d4aa !important;
    color: #a0d8ef !important;
}
div[data-testid="stNotification"] { background: rgba(10,22,45,0.88) !important; }

/* Progress */
.stProgress > div > div {
    background: rgba(0,212,170,0.12) !important; border-radius: 10px !important;
}
.stProgress > div > div > div {
    background: linear-gradient(90deg, #00d4aa, #4a9eff) !important; border-radius: 10px !important;
}

/* Checkboxes */
.stCheckbox label { color: #8ab4cc !important; font-size: 13px !important; }

/* Spinner */
.stSpinner > div { border-top-color: #00d4aa !important; }

/* Divider */
hr { border-color: rgba(0,212,170,0.12) !important; }

/* Headers */
h1, h2, h3 { color: #c8dff0 !important; font-family: 'DM Sans', sans-serif !important; }
p, li { color: #8ab4cc !important; }
strong { color: #c8dff0 !important; }

/* Custom classes */
.page-header {
    font-family: 'DM Sans', sans-serif;
    font-size: 24px; font-weight: 600; color: #c8dff0; margin-bottom: 2px;
}
.page-header span { color: #00d4aa; }
.page-subtitle { font-size: 13px; color: #4a7a9b; margin-bottom: 20px; letter-spacing: 0.3px; }
.teal-divider {
    border: none; height: 1px;
    background: linear-gradient(90deg, #00d4aa44, transparent); margin: 18px 0;
}
.glass-card {
    background: rgba(10,22,45,0.82);
    border: 1px solid rgba(0,212,170,0.11);
    border-radius: 12px; padding: 20px 24px; margin-bottom: 16px;
    border-top: 2px solid rgba(0,212,170,0.38);
}
.badge-low {
    background: rgba(0,212,170,0.1); color: #00d4aa;
    border: 1px solid rgba(0,212,170,0.25); padding: 2px 10px;
    border-radius: 20px; font-size: 11px; font-family: 'Space Mono', monospace;
}
.badge-high {
    background: rgba(255,107,107,0.1); color: #ff6b6b;
    border: 1px solid rgba(255,107,107,0.25); padding: 2px 10px;
    border-radius: 20px; font-size: 11px; font-family: 'Space Mono', monospace;
}
.badge-med {
    background: rgba(255,209,102,0.1); color: #ffd166;
    border: 1px solid rgba(255,209,102,0.25); padding: 2px 10px;
    border-radius: 20px; font-size: 11px; font-family: 'Space Mono', monospace;
}
.stat-label {
    font-family: 'Space Mono', monospace; font-size: 10px;
    color: #4a7a9b; letter-spacing: 1.5px; text-transform: uppercase;
}
.ticker-wrap {
    background: rgba(0,212,170,0.04); border: 1px solid rgba(0,212,170,0.1);
    border-radius: 8px; padding: 10px 16px; overflow: hidden;
}
.ticker-text {
    display: inline-block;
    animation: tickerScroll 18s linear infinite;
    white-space: nowrap; color: #00d4aa;
    font-family: 'Space Mono', monospace; font-size: 11px;
}
@keyframes tickerScroll {
    0%   { transform: translateX(100%); }
    100% { transform: translateX(-100%); }
}

/* Hide Streamlit chrome */
#MainMenu, footer { visibility: hidden !important; }
[data-testid="stToolbar"] { display: none !important; }
</style>
""", unsafe_allow_html=True)

# ── Animated particle canvas (injected once) ───────────────────────────────
st.markdown("""
<canvas id='bgCanvas' style='position:fixed;top:0;left:0;width:100%;height:100%;z-index:0;pointer-events:none;opacity:0.35;'></canvas>
<script>
(function(){
  const c = document.getElementById('bgCanvas');
  if(!c) return;
  const ctx = c.getContext('2d');
  c.width = window.innerWidth; c.height = window.innerHeight;
  const pts = Array.from({length:28}, () => ({
    x: Math.random()*c.width, y: Math.random()*c.height,
    vx: (Math.random()-0.5)*0.35, vy: (Math.random()-0.5)*0.35,
    r: Math.random()*2+1
  }));
  function draw(){
    ctx.clearRect(0,0,c.width,c.height);
    pts.forEach(p => {
      p.x+=p.vx; p.y+=p.vy;
      if(p.x<0||p.x>c.width) p.vx*=-1;
      if(p.y<0||p.y>c.height) p.vy*=-1;
      ctx.beginPath(); ctx.arc(p.x,p.y,p.r,0,Math.PI*2);
      ctx.fillStyle='rgba(0,212,170,0.55)'; ctx.fill();
    });
    pts.forEach((p,i) => pts.slice(i+1).forEach(q => {
      const d=Math.hypot(p.x-q.x,p.y-q.y);
      if(d<110){
        ctx.beginPath(); ctx.moveTo(p.x,p.y); ctx.lineTo(q.x,q.y);
        ctx.strokeStyle=`rgba(0,212,170,${0.14*(1-d/110)})`; ctx.lineWidth=0.5; ctx.stroke();
      }
    }));
    requestAnimationFrame(draw);
  }
  draw();
})();
</script>
""", unsafe_allow_html=True)

from food_label_analyzer.src.data_loader import get_data_loader

@st.cache_resource
def load_data():
    return get_data_loader()

data_loader = load_data()

# ── helpers ────────────────────────────────────────────────────────────────
def page_header(title: str, highlight: str, subtitle: str):
    st.markdown(f"""
    <div class='page-header'>{title} <span>{highlight}</span></div>
    <div class='page-subtitle'>{subtitle}</div>
    <hr class='teal-divider'>
    """, unsafe_allow_html=True)

def try_imports():
    imports = {}
    try:
        from food_label_analyzer.src.ocr_engine.label_ocr import NutritionLabelOCR
        imports['ocr'] = NutritionLabelOCR
    except Exception as e:
        imports['ocr'] = None
        imports['ocr_error'] = str(e)
    try:
        from food_label_analyzer.src.classification.classifier import FoodClassifier
        imports['classifier'] = FoodClassifier
    except Exception:
        imports['classifier'] = None
    try:
        from food_label_analyzer.src.substitution_engine.recommender import SubstitutionRecommendationEngine
        imports['recommender'] = SubstitutionRecommendationEngine
    except Exception:
        imports['recommender'] = None
    try:
        from food_label_analyzer.src.meal_simulation.simulator import MealSimulator
        imports['simulator'] = MealSimulator
    except Exception:
        imports['simulator'] = None
    try:
        from food_label_analyzer.src.compliance_tracking.tracker import DailyConsumptionTracker
        imports['tracker'] = DailyConsumptionTracker
    except Exception:
        imports['tracker'] = None
    return imports

IMPORTS = try_imports()

# ── Sidebar ────────────────────────────────────────────────────────────────
st.sidebar.markdown("""
<div style='padding:8px 0 16px; border-bottom:1px solid rgba(0,212,170,0.15); margin-bottom:12px;'>
  <div style='font-family:Space Mono,monospace; font-size:13px; color:#00d4aa; font-weight:700; letter-spacing:1px;'>⬡ FOOD LABEL</div>
  <div style='font-family:Space Mono,monospace; font-size:10px; color:#4a7a9b; letter-spacing:2px;'>ANALYZER v2.0</div>
</div>
""", unsafe_allow_html=True)

page = st.sidebar.radio("", ["Home", "Analyze Label", "Substitutions", "Meal Substitutions", "Meal Simulator", "Weekly Report"])

st.sidebar.markdown("<hr class='teal-divider'>", unsafe_allow_html=True)
ocr_mode = st.sidebar.radio("OCR ENGINE", ["Standard (EasyOCR)", "Lite (Tesseract)"], index=0)
st.sidebar.info("💡 Use 'Lite' mode if deployment memory is limited.")
st.sidebar.markdown("""
<div style='font-family:Space Mono,monospace; font-size:10px; color:#4a7a9b; line-height:1.8;'>
  <div style='color:#00d4aa; font-size:11px; margin-bottom:6px;'>● SYSTEM STATUS</div>
  <div>OCR Engine &nbsp;<span style='color:#22c55e;'>● Online</span></div>
  <div>AI Model &nbsp;&nbsp;&nbsp;<span style='color:#22c55e;'>● CPU Mode</span></div>
  <div>Database &nbsp;&nbsp;&nbsp;<span style='color:#22c55e;'>● 100 foods</span></div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════
# HOME
# ══════════════════════════════════════════════════════════════════════════
if page == "Home":
    page_header("Food Label", "Analyzer", "Comprehensive AI-driven food analysis for diabetic & hypertension patients")

    # ── Hero banner: DNA helix + floating food molecules ──────────────────
    st.markdown("""
    <div style="width:100%;border-radius:16px;overflow:hidden;margin-bottom:24px;
                border:1px solid rgba(0,212,170,0.15);position:relative;height:200px;
                background:linear-gradient(135deg,rgba(5,13,26,0.98) 0%,rgba(0,30,40,0.98) 100%);">

      <!-- SVG background: DNA helix + molecules (left half only) -->
      <svg width="100%" height="200" viewBox="0 0 1200 200" preserveAspectRatio="xMidYMid slice"
           xmlns="http://www.w3.org/2000/svg" style="position:absolute;top:0;left:0;">
        <defs>
          <radialGradient id="hglow" cx="25%" cy="50%" r="40%">
            <stop offset="0%" stop-color="#00d4aa" stop-opacity="0.1"/>
            <stop offset="100%" stop-color="#00d4aa" stop-opacity="0"/>
          </radialGradient>
          <style>
            @keyframes helixFloat { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-8px)} }
            @keyframes molSpin    { from{transform:rotate(0deg)} to{transform:rotate(360deg)} }
            .helix-anim { animation: helixFloat 4s ease-in-out infinite; }
            .mol1 { animation: molSpin 18s linear infinite; transform-origin:310px 100px; }
            .mol2 { animation: molSpin 24s linear infinite reverse; transform-origin:340px 50px; }
            .mol3 { animation: molSpin 14s linear infinite; transform-origin:280px 155px; }
          </style>
        </defs>
        <ellipse cx="200" cy="100" rx="300" ry="120" fill="url(#hglow)"/>
        <!-- DNA helix — contained in left 370px -->
        <g class="helix-anim">
          <path d="M30,40 C80,15 130,90 180,68 C230,46 280,120 330,98 C360,86 370,80 370,80"
                stroke="#00d4aa" stroke-width="2" fill="none" opacity="0.55"/>
          <path d="M30,160 C80,138 130,68 180,90 C230,112 280,40 330,62 C360,74 370,80 370,80"
                stroke="#4a9eff" stroke-width="2" fill="none" opacity="0.45"/>
          <circle cx="30"  cy="40"  r="4" fill="#00d4aa" opacity="0.7"/>
          <circle cx="30"  cy="160" r="4" fill="#4a9eff" opacity="0.7"/>
          <circle cx="130" cy="78"  r="4" fill="#00d4aa" opacity="0.7"/>
          <circle cx="130" cy="100" r="4" fill="#4a9eff" opacity="0.7"/>
          <circle cx="230" cy="82"  r="4" fill="#00d4aa" opacity="0.7"/>
          <circle cx="230" cy="76"  r="4" fill="#4a9eff" opacity="0.7"/>
          <circle cx="330" cy="98"  r="4" fill="#00d4aa" opacity="0.7"/>
          <circle cx="330" cy="62"  r="4" fill="#4a9eff" opacity="0.7"/>
          <line x1="130" y1="78"  x2="130" y2="100" stroke="#00d4aa" stroke-width="1" opacity="0.2"/>
          <line x1="230" y1="76"  x2="230" y2="82"  stroke="#00d4aa" stroke-width="1" opacity="0.2"/>
          <line x1="330" y1="62"  x2="330" y2="98"  stroke="#00d4aa" stroke-width="1" opacity="0.2"/>
        </g>
        <!-- Glucose hexagon -->
        <g class="mol1">
          <polygon points="310,80 326,90 326,110 310,120 294,110 294,90"
                   fill="none" stroke="#00d4aa" stroke-width="1.5" opacity="0.55"/>
          <text x="310" y="106" text-anchor="middle" fill="#00d4aa" font-size="8"
                font-family="Space Mono,monospace" opacity="0.7">C₆H₁₂O₆</text>
        </g>
        <!-- Sodium ion -->
        <g class="mol2">
          <circle cx="340" cy="50" r="20" fill="none" stroke="#ffd166" stroke-width="1.5" opacity="0.45"/>
          <text x="340" y="55" text-anchor="middle" fill="#ffd166" font-size="11"
                font-family="Space Mono,monospace" font-weight="700" opacity="0.8">Na⁺</text>
        </g>
        <!-- Protein dots -->
        <g class="mol3">
          <circle cx="280" cy="155" r="7"  fill="none" stroke="#ff6b6b" stroke-width="1.2" opacity="0.45"/>
          <circle cx="296" cy="147" r="5"  fill="none" stroke="#ff6b6b" stroke-width="1"   opacity="0.35"/>
          <circle cx="308" cy="157" r="6"  fill="none" stroke="#ff6b6b" stroke-width="1"   opacity="0.35"/>
          <line x1="287" y1="155" x2="291" y2="149" stroke="#ff6b6b" stroke-width="1" opacity="0.3"/>
          <line x1="301" y1="149" x2="302" y2="153" stroke="#ff6b6b" stroke-width="1" opacity="0.3"/>
        </g>
        <!-- Nutrition label silhouette — far right -->
        <rect x="1108" y="18" width="80" height="164" rx="6"
              fill="none" stroke="rgba(0,212,170,0.18)" stroke-width="1"/>
        <rect x="1116" y="28" width="64" height="9"  rx="2" fill="rgba(0,212,170,0.16)"/>
        <rect x="1116" y="44" width="64" height="1"       fill="rgba(0,212,170,0.1)"/>
        <rect x="1116" y="52" width="38" height="5" rx="1" fill="rgba(0,212,170,0.09)"/>
        <rect x="1158" y="52" width="22" height="5" rx="1" fill="rgba(0,212,170,0.2)"/>
        <rect x="1116" y="64" width="38" height="5" rx="1" fill="rgba(0,212,170,0.07)"/>
        <rect x="1158" y="64" width="22" height="5" rx="1" fill="rgba(255,107,107,0.3)"/>
        <rect x="1116" y="76" width="38" height="5" rx="1" fill="rgba(0,212,170,0.07)"/>
        <rect x="1158" y="76" width="22" height="5" rx="1" fill="rgba(255,209,102,0.3)"/>
        <rect x="1116" y="88" width="64" height="1"       fill="rgba(0,212,170,0.08)"/>
        <rect x="1116" y="96" width="48" height="5" rx="1" fill="rgba(0,212,170,0.07)"/>
        <rect x="1116" y="108" width="48" height="5" rx="1" fill="rgba(0,212,170,0.07)"/>
        <rect x="1116" y="120" width="48" height="5" rx="1" fill="rgba(0,212,170,0.07)"/>
        <rect x="1116" y="132" width="48" height="5" rx="1" fill="rgba(0,212,170,0.07)"/>
        <rect x="1116" y="144" width="48" height="5" rx="1" fill="rgba(0,212,170,0.07)"/>
        <rect x="1116" y="156" width="48" height="5" rx="1" fill="rgba(0,212,170,0.07)"/>
      </svg>

      <!-- HTML text overlay — always fully visible, not clipped by SVG scaling -->
      <div style="position:absolute;top:0;left:0;width:100%;height:100%;
                  display:flex;flex-direction:column;justify-content:center;
                  padding:0 5% 0 36%;">
        <div style="font-family:'DM Sans',sans-serif;font-size:clamp(20px,2.4vw,34px);
                    font-weight:700;color:#c8dff0;line-height:1.2;
                    animation:fadeInHero2 0.8s 0.1s both;">
          Medical-Grade
        </div>
        <div style="font-family:'DM Sans',sans-serif;font-size:clamp(20px,2.4vw,34px);
                    font-weight:700;color:#00d4aa;line-height:1.2;margin-bottom:12px;
                    text-shadow:0 0 24px rgba(0,212,170,0.4);
                    animation:fadeInHero2 0.8s 0.4s both;">
          Nutrition Intelligence
        </div>
        <div style="font-family:'Space Mono',monospace;font-size:clamp(9px,0.9vw,12px);
                    color:#4a7a9b;letter-spacing:0.5px;
                    animation:fadeInHero2 0.8s 0.7s both;">
          AI &nbsp;·&nbsp; OCR &nbsp;·&nbsp; Glycemic Analysis &nbsp;·&nbsp; Substitution Engine &nbsp;·&nbsp; Compliance Tracking
        </div>
      </div>
    </div>
    <style>
      @keyframes fadeInHero2 {
        from { opacity:0; transform:translateY(10px); }
        to   { opacity:1; transform:translateY(0); }
      }
    </style>
    """, unsafe_allow_html=True)

    # Stat cards
    foods_all = data_loader.get_all_foods()
    users_all = data_loader.get_sample_users()
    gi_count  = len(data_loader.gi_db) if data_loader.gi_db is not None else 0

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("🥗 Foods in Database", len(foods_all))
    with col2:
        st.metric("👤 Sample User Profiles", len(users_all))
    with col3:
        st.metric("📈 GI Reference Data", gi_count)

    st.markdown("<hr class='teal-divider'>", unsafe_allow_html=True)

    # Accordions
    with st.expander("📊 Sample Foods Available"):
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        foods_sample = data_loader.get_all_foods()[:20]
        for food in foods_sample:
            sodium_badge = "badge-high" if food.sodium_mg > 400 else ("badge-med" if food.sodium_mg > 200 else "badge-low")
            sugar_badge  = "badge-high" if food.sugars_g > 12 else ("badge-med" if food.sugars_g > 6 else "badge-low")
            st.markdown(f"""
            <div style='display:flex;align-items:center;justify-content:space-between;
                        padding:8px 0;border-bottom:1px solid rgba(0,212,170,0.06);'>
              <span style='font-size:13px;color:#c8dff0;font-weight:500;'>{food.food_name}</span>
              <span style='display:flex;gap:8px;align-items:center;'>
                <span class='stat-label'>{food.calories:.0f} kcal</span>
                <span class='{sugar_badge}'>{food.sugars_g:.1f}g sugar</span>
                <span class='{sodium_badge}'>{food.sodium_mg:.0f}mg Na</span>
              </span>
            </div>""", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with st.expander("👥 Sample Users"):
        users_df = data_loader.user_profiles_db
        if users_df is not None and len(users_df) > 0:
            st.dataframe(
                users_df[['user_id', 'name', 'age', 'has_diabetes', 'diabetes_type', 'hypertension_severity']],
                use_container_width=True
            )

    st.markdown("<hr class='teal-divider'>", unsafe_allow_html=True)

    # Live activity ticker
    st.markdown("""
    <div class='ticker-wrap'>
      <span class='ticker-text'>
        ✅ Label analyzed: Whole Wheat Bread — Low GI detected &nbsp;&nbsp;&nbsp;⬡&nbsp;&nbsp;&nbsp;
        ⚠️ High sodium flagged: Instant Noodles (1820mg) &nbsp;&nbsp;&nbsp;⬡&nbsp;&nbsp;&nbsp;
        🔄 Database synced — 100 foods loaded &nbsp;&nbsp;&nbsp;⬡&nbsp;&nbsp;&nbsp;
        🩺 User profile updated: Patient #7 &nbsp;&nbsp;&nbsp;⬡&nbsp;&nbsp;&nbsp;
        ✅ GI load within safe range today &nbsp;&nbsp;&nbsp;⬡&nbsp;&nbsp;&nbsp;
        ⚠️ Hidden sugars detected: Flavoured Yogurt &nbsp;&nbsp;&nbsp;⬡&nbsp;&nbsp;&nbsp;
        ✅ Substitution found: Brown Rice → Quinoa (-12 GI) &nbsp;&nbsp;&nbsp;⬡&nbsp;&nbsp;&nbsp;
      </span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.info("💡 Use the sidebar to navigate features. The system includes 100 foods, 47 GI records, and 10 sample user profiles.")

# ══════════════════════════════════════════════════════════════════════════
# ANALYZE LABEL
# ══════════════════════════════════════════════════════════════════════════
if page == "Analyze Label":
    page_header("📸 Analyze", "Food Label", "Extract nutrition facts using AI-powered OCR — supports English & Hindi labels")

    # ── Hero banner: OCR scanner beam ─────────────────────────────────────
    st.markdown("""
    <div style="width:100%;border-radius:16px;overflow:hidden;margin-bottom:20px;
                border:1px solid rgba(0,212,170,0.15);position:relative;height:140px;
                background:linear-gradient(135deg,rgba(5,13,26,0.98) 0%,rgba(0,20,35,0.98) 100%);">
      <svg width="100%" height="140" viewBox="0 0 1200 140" preserveAspectRatio="xMidYMid slice"
           xmlns="http://www.w3.org/2000/svg">
        <defs>
          <style>
            @keyframes scanBeam {
              0%   { transform: translateY(0px);   opacity:0.9; }
              50%  { transform: translateY(80px);  opacity:0.6; }
              100% { transform: translateY(0px);   opacity:0.9; }
            }
            @keyframes blink { 0%,100%{opacity:1} 50%{opacity:0.3} }
            .scan-line { animation: scanBeam 2.4s ease-in-out infinite; }
            .blink-dot { animation: blink 1.2s ease-in-out infinite; }
          </style>
          <linearGradient id="scanGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="#00d4aa" stop-opacity="0.6"/>
            <stop offset="100%" stop-color="#00d4aa" stop-opacity="0"/>
          </linearGradient>
        </defs>
        <!-- Barcode stripes -->
        <g opacity="0.25">
          <rect x="80"  y="20" width="3"  height="100" fill="#00d4aa"/>
          <rect x="87"  y="20" width="6"  height="100" fill="#00d4aa"/>
          <rect x="97"  y="20" width="2"  height="100" fill="#00d4aa"/>
          <rect x="103" y="20" width="5"  height="100" fill="#00d4aa"/>
          <rect x="112" y="20" width="3"  height="100" fill="#00d4aa"/>
          <rect x="119" y="20" width="7"  height="100" fill="#00d4aa"/>
          <rect x="130" y="20" width="2"  height="100" fill="#00d4aa"/>
          <rect x="136" y="20" width="4"  height="100" fill="#00d4aa"/>
          <rect x="144" y="20" width="6"  height="100" fill="#00d4aa"/>
          <rect x="154" y="20" width="3"  height="100" fill="#00d4aa"/>
          <rect x="161" y="20" width="5"  height="100" fill="#00d4aa"/>
          <rect x="170" y="20" width="2"  height="100" fill="#00d4aa"/>
          <rect x="176" y="20" width="4"  height="100" fill="#00d4aa"/>
          <rect x="184" y="20" width="7"  height="100" fill="#00d4aa"/>
          <rect x="195" y="20" width="3"  height="100" fill="#00d4aa"/>
          <rect x="202" y="20" width="5"  height="100" fill="#00d4aa"/>
          <rect x="211" y="20" width="2"  height="100" fill="#00d4aa"/>
          <rect x="217" y="20" width="6"  height="100" fill="#00d4aa"/>
          <rect x="227" y="20" width="3"  height="100" fill="#00d4aa"/>
          <rect x="234" y="20" width="4"  height="100" fill="#00d4aa"/>
        </g>
        <!-- Scanner frame corners -->
        <path d="M60,15 L60,30 M60,15 L80,15"   stroke="#00d4aa" stroke-width="2.5" fill="none" opacity="0.8"/>
        <path d="M260,15 L260,30 M260,15 L240,15" stroke="#00d4aa" stroke-width="2.5" fill="none" opacity="0.8"/>
        <path d="M60,125 L60,110 M60,125 L80,125" stroke="#00d4aa" stroke-width="2.5" fill="none" opacity="0.8"/>
        <path d="M260,125 L260,110 M260,125 L240,125" stroke="#00d4aa" stroke-width="2.5" fill="none" opacity="0.8"/>
        <!-- Scan beam -->
        <g class="scan-line">
          <rect x="60" y="15" width="200" height="3" fill="#00d4aa" opacity="0.9"/>
          <rect x="60" y="15" width="200" height="20" fill="url(#scanGrad)" opacity="0.4"/>
        </g>
        <!-- Status dot -->
        <circle cx="290" cy="70" r="5" fill="#00d4aa" class="blink-dot"/>
        <text x="302" y="74" font-family="Space Mono,monospace" font-size="10"
              fill="#00d4aa" opacity="0.9">SCANNING...</text>
        <!-- Right panel: extracted data preview -->
        <rect x="380" y="15" width="780" height="110" rx="8"
              fill="rgba(0,212,170,0.03)" stroke="rgba(0,212,170,0.12)" stroke-width="1"/>
        <text x="400" y="38" font-family="Space Mono,monospace" font-size="10"
              fill="#4a7a9b" letter-spacing="2">NUTRITION FACTS</text>
        <line x1="400" y1="44" x2="1140" y2="44" stroke="rgba(0,212,170,0.15)" stroke-width="1"/>
        <!-- Nutrient rows -->
        <text x="400" y="60" font-family="DM Sans,sans-serif" font-size="12" fill="#8ab4cc">Calories</text>
        <text x="560" y="60" font-family="Space Mono,monospace" font-size="12" fill="#00d4aa">250 kcal</text>
        <text x="400" y="76" font-family="DM Sans,sans-serif" font-size="12" fill="#8ab4cc">Total Sugars</text>
        <text x="560" y="76" font-family="Space Mono,monospace" font-size="12" fill="#ffd166">8.4 g</text>
        <text x="400" y="92" font-family="DM Sans,sans-serif" font-size="12" fill="#8ab4cc">Sodium</text>
        <text x="560" y="92" font-family="Space Mono,monospace" font-size="12" fill="#ff6b6b">420 mg ⚠</text>
        <text x="400" y="108" font-family="DM Sans,sans-serif" font-size="12" fill="#8ab4cc">Protein</text>
        <text x="560" y="108" font-family="Space Mono,monospace" font-size="12" fill="#00d4aa">6.2 g</text>
        <!-- Confidence bar -->
        <text x="700" y="60" font-family="Space Mono,monospace" font-size="9" fill="#4a7a9b">OCR CONFIDENCE</text>
        <rect x="700" y="66" width="200" height="6" rx="3" fill="rgba(0,212,170,0.1)"/>
        <rect x="700" y="66" width="174" height="6" rx="3" fill="#00d4aa" opacity="0.7"/>
        <text x="908" y="73" font-family="Space Mono,monospace" font-size="9" fill="#00d4aa">87%</text>
        <text x="700" y="90" font-family="Space Mono,monospace" font-size="9" fill="#4a7a9b">LANGUAGES</text>
        <text x="700" y="104" font-family="DM Sans,sans-serif" font-size="11" fill="#8ab4cc">English · Hindi · Bilingual</text>
      </svg>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("📋 How to Use — Instructions & Requirements", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            **✅ What Works Best:**
            - Resolution: 300 DPI or higher
            - Size: Less than 5 MB
            - Content: Focus on Nutrition Facts label
            - Condition: Well-lit, no shadows
            - Angle: Straight-on (90 degrees)
            - Format: PNG, JPG, JPEG, or TIFF
            - Language: English or Hindi supported
            """)
        with col2:
            st.markdown("""
            **❌ What to Avoid:**
            - Blurry or out-of-focus photos
            - Photos taken at an angle
            - Images with glare or shadows
            - Photos of the entire package
            - Handwritten labels
            - Files larger than 5 MB
            - Unsupported formats (GIF, BMP, WebP)
            """)

    st.markdown("<hr class='teal-divider'>", unsafe_allow_html=True)

    uploaded = st.file_uploader("Upload a label image", type=["png", "jpg", "jpeg", "tiff"])
    with st.expander("👤 User Profile (optional)"):
        user_id = st.text_input("User ID", value="demo_user")

    if uploaded:
        st.success(f"✓ Image uploaded: **{uploaded.name}**")

        col1, col2 = st.columns([2, 1])
        with col1:
            st.image(uploaded, caption="Uploaded Nutrition Label", use_container_width=True)
        with col2:
            st.markdown(f"""
            <div class='glass-card'>
              <div class='stat-label' style='margin-bottom:10px;'>File Info</div>
              <div style='font-size:12px;color:#8ab4cc;line-height:2;'>
                <div>📄 {uploaded.name}</div>
                <div>📦 {uploaded.size/1024:.1f} KB</div>
                <div>🖼️ {uploaded.type}</div>
              </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<hr class='teal-divider'>", unsafe_allow_html=True)

        # Save temp file
        ext = os.path.splitext(uploaded.name)[1] or ".jpg"
        tfile = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
        tfile.write(uploaded.getbuffer())
        tfile.flush()
        tpath = tfile.name

        st.markdown("<div class='stat-label' style='margin-bottom:8px;'>🔍 OCR PROCESSING</div>", unsafe_allow_html=True)

        ocr_cls = IMPORTS.get('ocr')
        if ocr_cls is None:
            st.error("❌ OCR module not available. Ensure dependencies are installed.")
            if IMPORTS.get('ocr_error'):
                st.code(IMPORTS['ocr_error'])
        else:
            with st.spinner("⏳ Extracting nutrition information from label..."):
                try:
                    use_easyocr = (ocr_mode == "Standard (EasyOCR)")
                    use_tesseract = (ocr_mode == "Lite (Tesseract)")
                    ocr = ocr_cls(use_easyocr=use_easyocr, use_tesseract=use_tesseract)
                    ocr_result = ocr.extract_from_label(tpath)
                    st.success("✓ OCR extraction completed!")

                    from food_label_analyzer.src.ocr_engine.label_ocr import NutritionFactsParser
                    parser = NutritionFactsParser()
                    nutrition_text = ocr_result.detected_regions.get('nutrition_facts', ocr_result.raw_text)
                    nutrition_facts = parser.parse_nutrition_facts(nutrition_text)
                    ingredients_obj = parser.parse_ingredients(ocr_result.detected_regions.get('ingredients', ''))

                    parsed = {
                        'calories':       nutrition_facts.calories       or 0,
                        'total_carbs_g':  nutrition_facts.total_carbs_g  or 0,
                        'sugars_g':       nutrition_facts.sugars_g        or 0,
                        'protein_g':      nutrition_facts.protein_g       or 0,
                        'total_fat_g':    nutrition_facts.total_fat_g     or 0,
                        'sodium_mg':      nutrition_facts.sodium_mg       or 0,
                        'dietary_fiber_g':nutrition_facts.dietary_fiber_g or 0,
                        'cholesterol_mg': nutrition_facts.cholesterol_mg  or 0,
                        'ingredients':    ingredients_obj.ingredients if ingredients_obj else [],
                        'allergens':      ingredients_obj.allergens  if ingredients_obj else [],
                        'raw_text':       ocr_result.raw_text,
                        'confidence':     ocr_result.confidence,
                    }

                    tracked = ['calories','total_carbs_g','sugars_g','protein_g','total_fat_g','sodium_mg','dietary_fiber_g','cholesterol_mg']
                    found   = sum(1 for k in tracked if parsed.get(k, 0) > 0)
                    missing = [k.replace('_g','').replace('_mg','').replace('_',' ').title() for k in tracked if parsed.get(k,0)==0]

                    if found < len(tracked):
                        st.info(f"📊 Partial data: {found}/{len(tracked)} nutrients found. Missing: {', '.join(missing[:3])}{'...' if len(missing)>3 else ''}. This is normal.")

                    st.markdown("<div class='stat-label' style='margin:16px 0 10px;'>📊 EXTRACTED NUTRITION</div>", unsafe_allow_html=True)

                    nutrition_items = [
                        ('calories','Calories',''),('total_carbs_g','Carbs','g'),
                        ('sugars_g','Sugars','g'),('protein_g','Protein','g'),
                        ('total_fat_g','Total Fat','g'),('sodium_mg','Sodium','mg'),
                        ('dietary_fiber_g','Fiber','g'),('cholesterol_mg','Cholesterol','mg'),
                    ]
                    visible = [(k,l,u) for k,l,u in nutrition_items if parsed.get(k,0)>0]
                    if visible:
                        cols = st.columns(min(len(visible), 4))
                        for i, (key, label, unit) in enumerate(visible):
                            val = parsed[key]
                            cols[i % 4].metric(label, f"{val:.1f} {unit}" if unit else f"{val:.0f}")

                    st.markdown("<hr class='teal-divider'>", unsafe_allow_html=True)

                    if parsed.get('ingredients'):
                        with st.expander("🥄 Ingredients List"):
                            for ing in parsed['ingredients']:
                                st.markdown(f"<span style='color:#8ab4cc;font-size:13px;'>• {ing}</span>", unsafe_allow_html=True)

                    if parsed.get('allergens'):
                        with st.expander("⚠️ Allergen Information"):
                            for allergen in parsed['allergens']:
                                st.warning(f"⚠️ Contains: {allergen}")

                    with st.expander("💻 Raw OCR Data (JSON)"):
                        st.json(parsed)

                except Exception as e:
                    st.error(f"❌ OCR processing failed: {str(e)}")
                    st.info("Troubleshooting: Ensure the image is clear, well-lit, and the nutrition label is the main focus.")

        if 'parsed' in locals():
            classifier_cls = IMPORTS.get('classifier')
            if classifier_cls:
                st.info("✓ Classification engine available.")

        try:
            os.unlink(tpath)
        except Exception:
            pass

# ══════════════════════════════════════════════════════════════════════════
# SUBSTITUTIONS
# ══════════════════════════════════════════════════════════════════════════
if page == "Substitutions":
    page_header("🔄 Smart Food", "Substitutions", "Find healthier alternatives tailored to your health goals and medical profile")

    # ── Hero banner: food swap comparison visual ───────────────────────────
    st.markdown("""
    <div style="width:100%;border-radius:16px;overflow:hidden;margin-bottom:20px;
                border:1px solid rgba(0,212,170,0.15);position:relative;height:130px;
                background:linear-gradient(135deg,rgba(5,13,26,0.98) 0%,rgba(0,20,35,0.98) 100%);">
      <svg width="100%" height="130" viewBox="0 0 1200 130" preserveAspectRatio="xMidYMid slice"
           xmlns="http://www.w3.org/2000/svg">
        <defs>
          <style>
            @keyframes arrowPulse { 0%,100%{opacity:0.5;transform:translateX(0)} 50%{opacity:1;transform:translateX(6px)} }
            @keyframes scoreGrow  { from{width:0} to{width:140px} }
            .arrow-anim { animation: arrowPulse 1.6s ease-in-out infinite; }
          </style>
        </defs>
        <!-- Left food card: original -->
        <rect x="40" y="15" width="200" height="100" rx="10"
              fill="rgba(255,107,107,0.06)" stroke="rgba(255,107,107,0.3)" stroke-width="1"/>
        <text x="140" y="38" text-anchor="middle" font-family="Space Mono,monospace"
              font-size="9" fill="#ff6b6b" letter-spacing="1">ORIGINAL</text>
        <text x="140" y="58" text-anchor="middle" font-family="DM Sans,sans-serif"
              font-size="14" font-weight="600" fill="#c8dff0">Instant Noodles</text>
        <text x="140" y="74" text-anchor="middle" font-family="Space Mono,monospace"
              font-size="10" fill="#ff6b6b">1820mg Na · 52 GI</text>
        <text x="140" y="90" text-anchor="middle" font-family="Space Mono,monospace"
              font-size="10" fill="#ffd166">380 kcal · 8.2g sugar</text>
        <rect x="60" y="98" width="160" height="4" rx="2" fill="rgba(255,107,107,0.15)"/>
        <rect x="60" y="98" width="130" height="4" rx="2" fill="#ff6b6b" opacity="0.5"/>
        <!-- Arrow -->
        <g class="arrow-anim" style="transform-origin:300px 65px;">
          <path d="M270,65 L330,65 M315,52 L330,65 L315,78"
                stroke="#00d4aa" stroke-width="2.5" fill="none" stroke-linecap="round"/>
        </g>
        <text x="300" y="58" text-anchor="middle" font-family="Space Mono,monospace"
              font-size="8" fill="#00d4aa" opacity="0.7">SWAP</text>
        <!-- Right food card: substitute -->
        <rect x="360" y="15" width="200" height="100" rx="10"
              fill="rgba(0,212,170,0.06)" stroke="rgba(0,212,170,0.3)" stroke-width="1"/>
        <text x="460" y="38" text-anchor="middle" font-family="Space Mono,monospace"
              font-size="9" fill="#00d4aa" letter-spacing="1">SUBSTITUTE</text>
        <text x="460" y="58" text-anchor="middle" font-family="DM Sans,sans-serif"
              font-size="14" font-weight="600" fill="#c8dff0">Brown Rice</text>
        <text x="460" y="74" text-anchor="middle" font-family="Space Mono,monospace"
              font-size="10" fill="#00d4aa">5mg Na · 50 GI</text>
        <text x="460" y="90" text-anchor="middle" font-family="Space Mono,monospace"
              font-size="10" fill="#00d4aa">216 kcal · 0.7g sugar</text>
        <rect x="380" y="98" width="160" height="4" rx="2" fill="rgba(0,212,170,0.15)"/>
        <rect x="380" y="98" width="60" height="4" rx="2" fill="#00d4aa" opacity="0.6"/>
        <!-- Right panel: improvement stats -->
        <text x="620" y="35" font-family="Space Mono,monospace" font-size="9"
              fill="#4a7a9b" letter-spacing="2">HEALTH IMPROVEMENTS</text>
        <text x="620" y="56" font-family="DM Sans,sans-serif" font-size="12" fill="#8ab4cc">Sodium reduction</text>
        <rect x="780" y="47" width="160" height="6" rx="3" fill="rgba(0,212,170,0.1)"/>
        <rect x="780" y="47" width="155" height="6" rx="3" fill="#00d4aa" opacity="0.7"/>
        <text x="948" y="55" font-family="Space Mono,monospace" font-size="9" fill="#00d4aa">-99%</text>
        <text x="620" y="76" font-family="DM Sans,sans-serif" font-size="12" fill="#8ab4cc">Calorie reduction</text>
        <rect x="780" y="67" width="160" height="6" rx="3" fill="rgba(0,212,170,0.1)"/>
        <rect x="780" y="67" width="90" height="6" rx="3" fill="#00d4aa" opacity="0.6"/>
        <text x="948" y="75" font-family="Space Mono,monospace" font-size="9" fill="#00d4aa">-43%</text>
        <text x="620" y="96" font-family="DM Sans,sans-serif" font-size="12" fill="#8ab4cc">GI improvement</text>
        <rect x="780" y="87" width="160" height="6" rx="3" fill="rgba(0,212,170,0.1)"/>
        <rect x="780" y="87" width="20" height="6" rx="3" fill="#ffd166" opacity="0.7"/>
        <text x="948" y="95" font-family="Space Mono,monospace" font-size="9" fill="#ffd166">-2 pts</text>
        <text x="620" y="116" font-family="Space Mono,monospace" font-size="9"
              fill="#00d4aa" opacity="0.7">● AI-powered · Diabetes-aware · Hypertension-safe</text>
      </svg>
    </div>
    """, unsafe_allow_html=True)

    foods = data_loader.get_all_foods()
    food_names = {f.food_name: f for f in foods}

    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.markdown("<div class='stat-label' style='margin-bottom:12px;'>YOUR HEALTH GOALS</div>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        from food_label_analyzer.src.config import UserGoal
        selected_goal = st.selectbox("Primary Health Goal:", options=[g.value for g in UserGoal],
                                     format_func=lambda x: x.replace('_',' ').title())
    with col2:
        has_diabetes    = st.checkbox("I have Diabetes")
        has_hypertension = st.checkbox("I have Hypertension")
    st.markdown("</div>", unsafe_allow_html=True)

    selected_food_name = st.selectbox("Select a food to find alternatives:", list(food_names.keys()))

    if st.button("🔍 Find Smart Substitutes"):
        original_food = food_names[selected_food_name]
        from food_label_analyzer.src.config import UserProfile, UserGoal, Gender, HypertensionSeverity
        hypertension_severity = HypertensionSeverity.STAGE_1 if has_hypertension else HypertensionSeverity.NORMAL
        user = UserProfile(user_id="demo_user", age=50, gender=Gender.MALE, weight_kg=80, height_cm=175,
                           has_diabetes=has_diabetes, hypertension_severity=hypertension_severity,
                           primary_goal=UserGoal(selected_goal))

        from food_label_analyzer.src.substitution_engine.advanced_recommender import AdvancedSubstitutionEngine
        engine = AdvancedSubstitutionEngine()
        substitutes = engine.find_substitutes(original_food, user, top_n=5)

        st.markdown(f"<div class='stat-label' style='margin:16px 0 8px;'>📌 ORIGINAL: {original_food.food_name.upper()}</div>", unsafe_allow_html=True)
        col1, col2, col3, col4, col5 = st.columns(5)
        health_score = engine.calculate_health_score(original_food, user)
        col1.metric("Calories",     f"{original_food.calories:.0f}")
        col2.metric("Sugar",        f"{original_food.sugars_g:.1f}g")
        col3.metric("Sodium",       f"{original_food.sodium_mg:.0f}mg")
        col4.metric("Fiber",        f"{original_food.fiber_g:.1f}g")
        col5.metric("Health Score", f"{health_score:.0f}/100")

        st.markdown("<hr class='teal-divider'>", unsafe_allow_html=True)

        if substitutes:
            st.markdown("<div class='stat-label' style='margin-bottom:10px;'>✅ TOP SUBSTITUTES</div>", unsafe_allow_html=True)
            for idx, sub in enumerate(substitutes, 1):
                with st.expander(f"#{idx}  {sub.food_name}  —  Score: {sub.total_score:.2f}", expanded=(idx==1)):
                    badge_text = " ".join(sub.badges) if sub.badges else "—"
                    st.markdown(f"<span class='badge-low'>{badge_text}</span>", unsafe_allow_html=True)
                    st.markdown("<br>", unsafe_allow_html=True)
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.markdown("**Nutritional Deltas**")
                        st.markdown(f"""
- Sugar: `{sub.sugar_delta_g:+.1f}g` {'⬇️' if sub.sugar_delta_g > 0 else '⬆️'}
- Net Carbs: `{sub.net_carbs_delta_g:+.1f}g`
- GI: `{sub.gi_delta:+.0f}` pts
- Sodium: `{sub.sodium_delta_mg:+.0f}mg`
- Calories: `{sub.calorie_delta:+.0f}`
                        """)
                    with col2:
                        st.metric("Substitute Calories",     f"{original_food.calories - sub.calorie_delta:.0f}")
                        st.metric("Substitute Health Score", f"{sub.health_score_substitute:.0f}/100")
                    with col3:
                        improvement = sub.health_score_substitute - sub.health_score_original
                        st.metric("Score Improvement", f"{improvement:+.0f}", delta=f"{improvement:.0f}")
                        st.markdown(f"**Why?** {sub.reasoning}")

                    st.markdown("<div class='stat-label' style='margin:10px 0 6px;'>COMPONENT SCORES</div>", unsafe_allow_html=True)
                    sc = st.columns(6)
                    sc[0].metric("Sugar",      f"{sub.sugar_score:.2f}")
                    sc[1].metric("Net Carbs",  f"{sub.net_carbs_score:.2f}")
                    sc[2].metric("GI",         f"{sub.gi_score:.2f}")
                    sc[3].metric("Sodium",     f"{sub.sodium_score:.2f}")
                    sc[4].metric("Calories",   f"{sub.calorie_score:.2f}")
                    sc[5].metric("Similarity", f"{sub.similarity_score:.2f}")
        else:
            st.info("No suitable substitutes found in similar food categories.")

# ══════════════════════════════════════════════════════════════════════════
# MEAL SUBSTITUTIONS
# ══════════════════════════════════════════════════════════════════════════
if page == "Meal Substitutions":
    page_header("🍽️ Meal-Level", "Substitutions", "Optimize entire meals by substituting individual foods based on your health goals")

    # ── Hero banner: meal optimization visual ─────────────────────────────
    st.markdown("""
    <div style="width:100%;border-radius:16px;overflow:hidden;margin-bottom:20px;
                border:1px solid rgba(0,212,170,0.15);position:relative;height:110px;
                background:linear-gradient(135deg,rgba(5,13,26,0.98) 0%,rgba(0,20,35,0.98) 100%);">
      <svg width="100%" height="110" viewBox="0 0 1200 110" preserveAspectRatio="xMidYMid slice"
           xmlns="http://www.w3.org/2000/svg">
        <defs>
          <style>
            @keyframes flowArrow { 0%,100%{opacity:0.4;transform:translateX(0)} 50%{opacity:1;transform:translateX(8px)} }
            .flow { animation: flowArrow 1.8s ease-in-out infinite; }
          </style>
        </defs>
        <!-- Food items row -->
        <rect x="40"  y="25" width="80" height="60" rx="8" fill="rgba(255,107,107,0.08)"  stroke="rgba(255,107,107,0.25)"  stroke-width="1"/>
        <text x="80"  y="52" text-anchor="middle" font-family="DM Sans,sans-serif"    font-size="11" fill="#c8dff0">White Rice</text>
        <text x="80"  y="68" text-anchor="middle" font-family="Space Mono,monospace"  font-size="8"  fill="#ff6b6b">GI: 72</text>

        <rect x="140" y="25" width="80" height="60" rx="8" fill="rgba(255,209,102,0.08)" stroke="rgba(255,209,102,0.25)" stroke-width="1"/>
        <text x="180" y="52" text-anchor="middle" font-family="DM Sans,sans-serif"    font-size="11" fill="#c8dff0">Fried Egg</text>
        <text x="180" y="68" text-anchor="middle" font-family="Space Mono,monospace"  font-size="8"  fill="#ffd166">Na: 142mg</text>

        <rect x="240" y="25" width="80" height="60" rx="8" fill="rgba(255,107,107,0.08)"  stroke="rgba(255,107,107,0.25)"  stroke-width="1"/>
        <text x="280" y="52" text-anchor="middle" font-family="DM Sans,sans-serif"    font-size="11" fill="#c8dff0">Soda</text>
        <text x="280" y="68" text-anchor="middle" font-family="Space Mono,monospace"  font-size="8"  fill="#ff6b6b">Sugar: 39g</text>

        <!-- Arrow -->
        <g class="flow" style="transform-origin:370px 55px;">
          <path d="M345,55 L395,55 M378,42 L395,55 L378,68"
                stroke="#00d4aa" stroke-width="2.5" fill="none" stroke-linecap="round"/>
        </g>
        <text x="370" y="46" text-anchor="middle" font-family="Space Mono,monospace"
              font-size="8" fill="#00d4aa">AI OPTIMIZE</text>

        <!-- Optimized food items -->
        <rect x="410" y="25" width="80" height="60" rx="8" fill="rgba(0,212,170,0.08)"  stroke="rgba(0,212,170,0.3)"  stroke-width="1"/>
        <text x="450" y="52" text-anchor="middle" font-family="DM Sans,sans-serif"    font-size="11" fill="#c8dff0">Brown Rice</text>
        <text x="450" y="68" text-anchor="middle" font-family="Space Mono,monospace"  font-size="8"  fill="#00d4aa">GI: 50 ✓</text>

        <rect x="510" y="25" width="80" height="60" rx="8" fill="rgba(0,212,170,0.08)"  stroke="rgba(0,212,170,0.3)"  stroke-width="1"/>
        <text x="550" y="52" text-anchor="middle" font-family="DM Sans,sans-serif"    font-size="11" fill="#c8dff0">Boiled Egg</text>
        <text x="550" y="68" text-anchor="middle" font-family="Space Mono,monospace"  font-size="8"  fill="#00d4aa">Na: 62mg ✓</text>

        <rect x="610" y="25" width="80" height="60" rx="8" fill="rgba(0,212,170,0.08)"  stroke="rgba(0,212,170,0.3)"  stroke-width="1"/>
        <text x="650" y="52" text-anchor="middle" font-family="DM Sans,sans-serif"    font-size="11" fill="#c8dff0">Coconut Water</text>
        <text x="650" y="68" text-anchor="middle" font-family="Space Mono,monospace"  font-size="8"  fill="#00d4aa">Sugar: 6g ✓</text>

        <!-- Right: score improvement -->
        <rect x="740" y="15" width="420" height="80" rx="8"
              fill="rgba(0,212,170,0.03)" stroke="rgba(0,212,170,0.1)" stroke-width="1"/>
        <text x="760" y="36" font-family="Space Mono,monospace" font-size="9"
              fill="#4a7a9b" letter-spacing="2">MEAL HEALTH SCORE</text>
        <text x="760" y="58" font-family="Space Mono,monospace" font-size="11" fill="#ff6b6b">Before: 42/100</text>
        <text x="760" y="78" font-family="Space Mono,monospace" font-size="11" fill="#00d4aa">After:  81/100  +39 ↑</text>
        <rect x="920" y="40" width="220" height="10" rx="5" fill="rgba(0,212,170,0.1)"/>
        <rect x="920" y="40" width="178" height="10" rx="5" fill="#00d4aa" opacity="0.6"/>
      </svg>
    </div>
    """, unsafe_allow_html=True)

    from food_label_analyzer.src.config import UserGoal, Gender, HypertensionSeverity, UserProfile
    from food_label_analyzer.src.substitution_engine.meal_substitution import MealContextSimulator, MealType

    foods = data_loader.get_all_foods()
    food_names = {f.food_name: f for f in foods}

    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.markdown("<div class='stat-label' style='margin-bottom:12px;'>YOUR HEALTH PROFILE</div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        selected_goal = st.selectbox("Primary Goal:", options=[g.value for g in UserGoal],
                                     format_func=lambda x: x.replace('_',' ').title(), key="meal_goal")
    with col2:
        has_diabetes    = st.checkbox("I have Diabetes",    key="meal_diabetes")
    with col3:
        has_hypertension = st.checkbox("I have Hypertension", key="meal_hypertension")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='stat-label' style='margin-bottom:10px;'>BUILD YOUR MEAL</div>", unsafe_allow_html=True)
    meal_type     = st.selectbox("Meal type:", [m.value for m in MealType], format_func=lambda x: x.title())
    selected_foods = st.multiselect("Select foods in this meal:", list(food_names.keys()), key="meal_foods")

    if st.button("⚗️ Optimize Meal"):
        if selected_foods:
            hypertension_severity = HypertensionSeverity.STAGE_1 if has_hypertension else HypertensionSeverity.NORMAL
            user = UserProfile(user_id="demo_user", age=50, gender=Gender.MALE, weight_kg=80, height_cm=175,
                               has_diabetes=has_diabetes, hypertension_severity=hypertension_severity,
                               primary_goal=UserGoal(selected_goal))
            meal_foods = [food_names[name] for name in selected_foods]
            simulator  = MealContextSimulator()
            result     = simulator.simulate_meal_substitution(MealType(meal_type), meal_foods, user)

            st.markdown("<hr class='teal-divider'>", unsafe_allow_html=True)
            st.markdown("<div class='stat-label' style='margin-bottom:12px;'>📊 MEAL COMPARISON</div>", unsafe_allow_html=True)

            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
                st.markdown("<div class='stat-label' style='margin-bottom:8px;'>ORIGINAL MEAL</div>", unsafe_allow_html=True)
                st.metric("Calories",     f"{result.original_calories:.0f}")
                st.metric("Sugar",        f"{result.original_sugars:.1f}g")
                st.metric("Sodium",       f"{result.original_sodium:.0f}mg")
                st.metric("Health Score", f"{result.original_health_score:.0f}/100")
                st.markdown("</div>", unsafe_allow_html=True)
            with col2:
                st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
                st.markdown("<div class='stat-label' style='margin-bottom:8px;'>OPTIMIZED MEAL</div>", unsafe_allow_html=True)
                st.metric("Calories",     f"{result.substituted_calories:.0f}")
                st.metric("Sugar",        f"{result.substituted_sugars:.1f}g")
                st.metric("Sodium",       f"{result.substituted_sodium:.0f}mg")
                st.metric("Health Score", f"{result.substituted_health_score:.0f}/100")
                st.markdown("</div>", unsafe_allow_html=True)
            with col3:
                st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
                st.markdown("<div class='stat-label' style='margin-bottom:8px;'>IMPROVEMENTS</div>", unsafe_allow_html=True)
                st.metric("Calories",     f"{result.calorie_reduction_pct:+.0f}%")
                st.metric("Sugar",        f"{result.sugar_reduction_pct:+.0f}%")
                st.metric("Sodium",       f"{result.sodium_reduction_pct:+.0f}%")
                st.metric("Health Score", f"{result.health_improvement:+.0f}", delta=f"{result.health_improvement:.0f}")
                st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("<hr class='teal-divider'>", unsafe_allow_html=True)
            st.markdown("<div class='stat-label' style='margin-bottom:10px;'>🔄 FOOD SUBSTITUTIONS</div>", unsafe_allow_html=True)
            for original_food_id, substitute_score in result.substitutions.items():
                original_food = next(f for f in meal_foods if f.food_id == original_food_id)
                with st.expander(f"{original_food.food_name}  →  {substitute_score.food_name}"):
                    st.markdown(f"**Why:** {substitute_score.reasoning}")
                    st.markdown(f"**Badges:** {' '.join(substitute_score.badges)}")
                    st.markdown(f"- Sugar: `{original_food.sugars_g:.1f}g` → `{original_food.sugars_g - substitute_score.sugar_delta_g:.1f}g` ({substitute_score.sugar_delta_g:+.1f}g)")
                    st.markdown(f"- Sodium: `{original_food.sodium_mg:.0f}mg` → `{original_food.sodium_mg - substitute_score.sodium_delta_mg:.0f}mg` ({substitute_score.sodium_delta_mg:+.0f}mg)")
                    st.markdown(f"- Calories: `{original_food.calories:.0f}` → `{original_food.calories - substitute_score.calorie_delta:.0f}` ({substitute_score.calorie_delta:+.0f})")
        else:
            st.info("Select at least one food to optimize.")

# ══════════════════════════════════════════════════════════════════════════
# MEAL SIMULATOR
# ══════════════════════════════════════════════════════════════════════════
if page == "Meal Simulator":
    page_header("⚗️ Meal", "Simulator", "Build a meal and see the combined nutritional impact in real time")

    # ── Hero banner: plate composition graphic ────────────────────────────
    st.markdown("""
    <div style="width:100%;border-radius:16px;overflow:hidden;margin-bottom:20px;
                border:1px solid rgba(0,212,170,0.15);position:relative;height:130px;
                background:linear-gradient(135deg,rgba(5,13,26,0.98) 0%,rgba(0,20,35,0.98) 100%);">
      <svg width="100%" height="130" viewBox="0 0 1200 130" preserveAspectRatio="xMidYMid slice"
           xmlns="http://www.w3.org/2000/svg">
        <defs>
          <style>
            @keyframes plateRotate { 0%,100%{transform:rotate(-2deg)} 50%{transform:rotate(2deg)} }
            @keyframes barGrow { from{height:0;y:100} to{} }
            .plate-anim { animation: plateRotate 4s ease-in-out infinite; transform-origin:160px 65px; }
          </style>
        </defs>
        <!-- Plate -->
        <g class="plate-anim">
          <ellipse cx="160" cy="70" rx="90" ry="55" fill="none"
                   stroke="rgba(0,212,170,0.25)" stroke-width="2"/>
          <ellipse cx="160" cy="70" rx="75" ry="45" fill="rgba(0,212,170,0.04)"
                   stroke="rgba(0,212,170,0.15)" stroke-width="1"/>
          <!-- Food segments on plate -->
          <path d="M160,70 L160,30 A40,40 0 0,1 195,90 Z"
                fill="rgba(0,212,170,0.15)" stroke="rgba(0,212,170,0.3)" stroke-width="0.5"/>
          <path d="M160,70 L195,90 A40,40 0 0,1 125,110 Z"
                fill="rgba(255,209,102,0.12)" stroke="rgba(255,209,102,0.3)" stroke-width="0.5"/>
          <path d="M160,70 L125,110 A40,40 0 0,1 120,30 Z"
                fill="rgba(255,107,107,0.1)" stroke="rgba(255,107,107,0.25)" stroke-width="0.5"/>
          <path d="M160,70 L120,30 A40,40 0 0,1 160,30 Z"
                fill="rgba(74,158,255,0.1)" stroke="rgba(74,158,255,0.25)" stroke-width="0.5"/>
          <!-- Segment labels -->
          <text x="178" y="58" font-family="Space Mono,monospace" font-size="7"
                fill="#00d4aa" opacity="0.8">CARBS</text>
          <text x="168" y="100" font-family="Space Mono,monospace" font-size="7"
                fill="#ffd166" opacity="0.8">SUGAR</text>
          <text x="118" y="78" font-family="Space Mono,monospace" font-size="7"
                fill="#ff6b6b" opacity="0.8">FAT</text>
          <text x="130" y="42" font-family="Space Mono,monospace" font-size="7"
                fill="#4a9eff" opacity="0.8">PROT</text>
        </g>
        <!-- Bar chart: daily totals -->
        <text x="320" y="22" font-family="Space Mono,monospace" font-size="9"
              fill="#4a7a9b" letter-spacing="2">DAILY NUTRIENT TOTALS</text>
        <!-- Bars -->
        <rect x="330" y="35" width="30" height="75" rx="3" fill="rgba(0,212,170,0.08)"/>
        <rect x="330" y="65" width="30" height="45" rx="3" fill="#00d4aa" opacity="0.6"/>
        <text x="345" y="122" text-anchor="middle" font-family="Space Mono,monospace"
              font-size="8" fill="#4a7a9b">Cal</text>

        <rect x="380" y="35" width="30" height="75" rx="3" fill="rgba(0,212,170,0.08)"/>
        <rect x="380" y="75" width="30" height="35" rx="3" fill="#ffd166" opacity="0.6"/>
        <text x="395" y="122" text-anchor="middle" font-family="Space Mono,monospace"
              font-size="8" fill="#4a7a9b">Sugar</text>

        <rect x="430" y="35" width="30" height="75" rx="3" fill="rgba(0,212,170,0.08)"/>
        <rect x="430" y="45" width="30" height="65" rx="3" fill="#ff6b6b" opacity="0.5"/>
        <text x="445" y="122" text-anchor="middle" font-family="Space Mono,monospace"
              font-size="8" fill="#4a7a9b">Na</text>

        <rect x="480" y="35" width="30" height="75" rx="3" fill="rgba(0,212,170,0.08)"/>
        <rect x="480" y="80" width="30" height="30" rx="3" fill="#4a9eff" opacity="0.6"/>
        <text x="495" y="122" text-anchor="middle" font-family="Space Mono,monospace"
              font-size="8" fill="#4a7a9b">Fiber</text>

        <!-- Safety thresholds -->
        <line x1="320" y1="60" x2="530" y2="60" stroke="#00d4aa" stroke-width="0.8"
              stroke-dasharray="4,3" opacity="0.4"/>
        <text x="535" y="63" font-family="Space Mono,monospace" font-size="8"
              fill="#00d4aa" opacity="0.6">SAFE LIMIT</text>

        <!-- Right: meal summary -->
        <rect x="620" y="15" width="540" height="100" rx="8"
              fill="rgba(0,212,170,0.03)" stroke="rgba(0,212,170,0.1)" stroke-width="1"/>
        <text x="640" y="36" font-family="Space Mono,monospace" font-size="9"
              fill="#4a7a9b" letter-spacing="2">MEAL SIMULATION ENGINE</text>
        <line x1="640" y1="42" x2="1140" y2="42" stroke="rgba(0,212,170,0.1)" stroke-width="1"/>
        <text x="640" y="60" font-family="DM Sans,sans-serif" font-size="12" fill="#8ab4cc">
          ● Select multiple foods → instant combined analysis
        </text>
        <text x="640" y="78" font-family="DM Sans,sans-serif" font-size="12" fill="#8ab4cc">
          ● Real-time sugar, sodium &amp; fiber safety checks
        </text>
        <text x="640" y="96" font-family="DM Sans,sans-serif" font-size="12" fill="#8ab4cc">
          ● Glycemic load estimation per meal
        </text>
      </svg>
    </div>
    """, unsafe_allow_html=True)

    foods      = data_loader.get_all_foods()
    food_names = [f.food_name for f in foods]
    meal_foods = st.multiselect("Select foods for your meal:", food_names)

    if st.button("📊 Analyze Meal"):
        if meal_foods:
            total_calories = total_sugars = total_sodium = total_fiber = total_carbs = 0
            meal_details = []
            for food_name in meal_foods:
                matching = [f for f in foods if f.food_name == food_name]
                if matching:
                    food = matching[0]
                    total_calories += food.calories
                    total_sugars   += food.sugars_g
                    total_sodium   += food.sodium_mg
                    total_fiber    += food.fiber_g
                    total_carbs    += food.carbs_g
                    meal_details.append({'Food': food.food_name, 'Calories': food.calories,
                                         'Sugars (g)': food.sugars_g, 'Sodium (mg)': food.sodium_mg,
                                         'Fiber (g)': food.fiber_g})

            st.markdown("<div class='stat-label' style='margin:16px 0 10px;'>MEAL TOTALS</div>", unsafe_allow_html=True)
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Calories", f"{total_calories:.0f}")
            col2.metric("Sugars",   f"{total_sugars:.1f}g")
            col3.metric("Sodium",   f"{total_sodium:.0f}mg")
            col4.metric("Fiber",    f"{total_fiber:.1f}g")

            st.markdown("<hr class='teal-divider'>", unsafe_allow_html=True)
            st.markdown("<div class='stat-label' style='margin-bottom:8px;'>FOOD BREAKDOWN</div>", unsafe_allow_html=True)
            st.dataframe(meal_details, use_container_width=True)

            st.markdown("<hr class='teal-divider'>", unsafe_allow_html=True)
            st.markdown("<div class='stat-label' style='margin-bottom:10px;'>SAFETY ASSESSMENT</div>", unsafe_allow_html=True)

            if total_sugars <= 25:
                st.success(f"✓ Sugar intake within limits ({total_sugars:.1f}g ≤ 25g)")
            else:
                st.warning(f"⚠ Sugar intake high ({total_sugars:.1f}g > 25g)")

            if total_sodium <= 2300:
                st.success(f"✓ Sodium intake within limits ({total_sodium:.0f}mg ≤ 2300mg)")
            else:
                st.warning(f"⚠ Sodium intake high ({total_sodium:.0f}mg > 2300mg)")

            if total_fiber >= 10:
                st.success(f"✓ Fiber intake adequate ({total_fiber:.1f}g ≥ 10g)")
            else:
                st.info(f"ℹ Fiber intake could be higher ({total_fiber:.1f}g < 10g)")
        else:
            st.info("Select at least one food to analyze.")

# ══════════════════════════════════════════════════════════════════════════
# WEEKLY REPORT
# ══════════════════════════════════════════════════════════════════════════
if page == "Weekly Report":
    page_header("📊 Weekly", "Compliance Report", "View compliance metrics and consumption analysis for sample users")

    # ── Hero banner: ECG / compliance chart ───────────────────────────────
    st.markdown("""
    <div style="width:100%;border-radius:16px;overflow:hidden;margin-bottom:20px;
                border:1px solid rgba(0,212,170,0.15);position:relative;height:130px;
                background:linear-gradient(135deg,rgba(5,13,26,0.98) 0%,rgba(0,20,35,0.98) 100%);">
      <svg width="100%" height="130" viewBox="0 0 1200 130" preserveAspectRatio="xMidYMid slice"
           xmlns="http://www.w3.org/2000/svg">
        <defs>
          <style>
            @keyframes ecgDraw {
              0%   { stroke-dashoffset: 800; }
              100% { stroke-dashoffset: 0; }
            }
            .ecg-line {
              stroke-dasharray: 800;
              stroke-dashoffset: 800;
              animation: ecgDraw 3s ease forwards;
            }
          </style>
          <linearGradient id="ecgFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="#00d4aa" stop-opacity="0.2"/>
            <stop offset="100%" stop-color="#00d4aa" stop-opacity="0"/>
          </linearGradient>
        </defs>
        <!-- Grid lines -->
        <line x1="40" y1="30"  x2="760" y2="30"  stroke="rgba(0,212,170,0.06)" stroke-width="1"/>
        <line x1="40" y1="65"  x2="760" y2="65"  stroke="rgba(0,212,170,0.06)" stroke-width="1"/>
        <line x1="40" y1="100" x2="760" y2="100" stroke="rgba(0,212,170,0.06)" stroke-width="1"/>
        <line x1="40"  y1="20" x2="40"  y2="110" stroke="rgba(0,212,170,0.06)" stroke-width="1"/>
        <line x1="160" y1="20" x2="160" y2="110" stroke="rgba(0,212,170,0.06)" stroke-width="1"/>
        <line x1="280" y1="20" x2="280" y2="110" stroke="rgba(0,212,170,0.06)" stroke-width="1"/>
        <line x1="400" y1="20" x2="400" y2="110" stroke="rgba(0,212,170,0.06)" stroke-width="1"/>
        <line x1="520" y1="20" x2="520" y2="110" stroke="rgba(0,212,170,0.06)" stroke-width="1"/>
        <line x1="640" y1="20" x2="640" y2="110" stroke="rgba(0,212,170,0.06)" stroke-width="1"/>
        <line x1="760" y1="20" x2="760" y2="110" stroke="rgba(0,212,170,0.06)" stroke-width="1"/>
        <!-- Day labels -->
        <text x="40"  y="120" text-anchor="middle" font-family="Space Mono,monospace" font-size="8" fill="#2a4a6b">MON</text>
        <text x="160" y="120" text-anchor="middle" font-family="Space Mono,monospace" font-size="8" fill="#2a4a6b">TUE</text>
        <text x="280" y="120" text-anchor="middle" font-family="Space Mono,monospace" font-size="8" fill="#2a4a6b">WED</text>
        <text x="400" y="120" text-anchor="middle" font-family="Space Mono,monospace" font-size="8" fill="#2a4a6b">THU</text>
        <text x="520" y="120" text-anchor="middle" font-family="Space Mono,monospace" font-size="8" fill="#2a4a6b">FRI</text>
        <text x="640" y="120" text-anchor="middle" font-family="Space Mono,monospace" font-size="8" fill="#2a4a6b">SAT</text>
        <text x="760" y="120" text-anchor="middle" font-family="Space Mono,monospace" font-size="8" fill="#2a4a6b">SUN</text>
        <!-- Sugar compliance line -->
        <polyline class="ecg-line"
          points="40,55 160,45 280,70 400,40 520,60 640,35 760,50"
          fill="none" stroke="#00d4aa" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        <!-- Sodium compliance line -->
        <polyline class="ecg-line"
          points="40,80 160,90 280,75 400,95 520,85 640,100 760,88"
          fill="none" stroke="#ff6b6b" stroke-width="1.5" stroke-linecap="round"
          stroke-linejoin="round" opacity="0.7" style="animation-delay:0.5s"/>
        <!-- Safe threshold line -->
        <line x1="40" y1="65" x2="760" y2="65"
              stroke="#ffd166" stroke-width="1" stroke-dasharray="6,4" opacity="0.5"/>
        <!-- Data points -->
        <circle cx="40"  cy="55" r="3" fill="#00d4aa" opacity="0.8"/>
        <circle cx="160" cy="45" r="3" fill="#00d4aa" opacity="0.8"/>
        <circle cx="280" cy="70" r="3" fill="#00d4aa" opacity="0.8"/>
        <circle cx="400" cy="40" r="3" fill="#00d4aa" opacity="0.8"/>
        <circle cx="520" cy="60" r="3" fill="#00d4aa" opacity="0.8"/>
        <circle cx="640" cy="35" r="3" fill="#00d4aa" opacity="0.8"/>
        <circle cx="760" cy="50" r="3" fill="#00d4aa" opacity="0.8"/>
        <!-- Legend -->
        <line x1="800" y1="40" x2="820" y2="40" stroke="#00d4aa" stroke-width="2"/>
        <text x="826" y="44" font-family="Space Mono,monospace" font-size="9" fill="#00d4aa">Sugar compliance</text>
        <line x1="800" y1="58" x2="820" y2="58" stroke="#ff6b6b" stroke-width="2"/>
        <text x="826" y="62" font-family="Space Mono,monospace" font-size="9" fill="#ff6b6b">Sodium compliance</text>
        <line x1="800" y1="76" x2="820" y2="76" stroke="#ffd166" stroke-width="1" stroke-dasharray="4,3"/>
        <text x="826" y="80" font-family="Space Mono,monospace" font-size="9" fill="#ffd166">Safe threshold</text>
        <!-- Summary stats -->
        <rect x="1000" y="15" width="180" height="100" rx="8"
              fill="rgba(0,212,170,0.04)" stroke="rgba(0,212,170,0.12)" stroke-width="1"/>
        <text x="1090" y="36" text-anchor="middle" font-family="Space Mono,monospace"
              font-size="9" fill="#4a7a9b" letter-spacing="1">WEEK SCORE</text>
        <text x="1090" y="72" text-anchor="middle" font-family="Space Mono,monospace"
              font-size="32" font-weight="700" fill="#00d4aa">78%</text>
        <text x="1090" y="92" text-anchor="middle" font-family="DM Sans,sans-serif"
              font-size="11" fill="#4a7a9b">Compliant</text>
      </svg>
    </div>
    """, unsafe_allow_html=True)

    users = data_loader.get_sample_users()

    if users:
        selected_user = st.selectbox("Select a user:", users)

        if st.button("📋 Generate Report"):
            user_profile = data_loader.get_user_profile(selected_user)
            if user_profile:
                st.markdown(f"""
                <div class='glass-card'>
                  <div class='stat-label' style='margin-bottom:12px;'>PATIENT PROFILE — {user_profile.get('name','').upper()}</div>
                  <div style='display:flex;gap:32px;flex-wrap:wrap;'>
                    <div><span class='stat-label'>AGE</span><br><span style='font-family:Space Mono,monospace;color:#00d4aa;font-size:20px;'>{user_profile.get('age')}</span></div>
                    <div><span class='stat-label'>WEIGHT</span><br><span style='font-family:Space Mono,monospace;color:#00d4aa;font-size:20px;'>{user_profile.get('weight_kg')} kg</span></div>
                    <div><span class='stat-label'>DIABETES</span><br><span style='font-family:Space Mono,monospace;color:{"#ff6b6b" if user_profile.get("has_diabetes") else "#00d4aa"};font-size:20px;'>{"Yes" if user_profile.get("has_diabetes") else "No"}</span></div>
                    <div><span class='stat-label'>TYPE</span><br><span style='font-family:Space Mono,monospace;color:#ffd166;font-size:20px;'>{user_profile.get("diabetes_type","N/A")}</span></div>
                  </div>
                </div>
                """, unsafe_allow_html=True)

                st.markdown("<hr class='teal-divider'>", unsafe_allow_html=True)

                consumption_log  = data_loader.consumption_log_db
                user_consumption = consumption_log[consumption_log['user_id'] == selected_user]

                if len(user_consumption) > 0:
                    total_calories = user_consumption['calories'].sum()
                    total_sugars   = user_consumption['sugars_g'].sum()
                    total_sodium   = user_consumption['sodium_mg'].sum()
                    total_fiber    = user_consumption['fiber_g'].sum()
                    meal_count     = len(user_consumption)

                    st.markdown("<div class='stat-label' style='margin-bottom:10px;'>WEEKLY SUMMARY</div>", unsafe_allow_html=True)
                    col1, col2, col3, col4, col5 = st.columns(5)
                    col1.metric("Total Calories", f"{total_calories:.0f}")
                    col2.metric("Total Sugar",    f"{total_sugars:.1f}g")
                    col3.metric("Total Sodium",   f"{total_sodium:.0f}mg")
                    col4.metric("Total Fiber",    f"{total_fiber:.1f}g")
                    col5.metric("Meals Logged",   meal_count)

                    st.markdown("<hr class='teal-divider'>", unsafe_allow_html=True)
                    st.markdown("<div class='stat-label' style='margin-bottom:10px;'>COMPLIANCE ANALYSIS</div>", unsafe_allow_html=True)

                    sugar_daily_target  = 25 * 2
                    sodium_daily_target = 2300 * 2
                    sugar_compliance  = (1 - min(total_sugars  / max(sugar_daily_target,  1), 1)) * 100
                    sodium_compliance = (1 - min(total_sodium  / max(sodium_daily_target, 1), 1)) * 100

                    st.markdown(f"**Sugar Compliance:** `{sugar_compliance:.1f}%`")
                    st.progress(min(sugar_compliance / 100, 1))
                    st.markdown(f"**Sodium Compliance:** `{sodium_compliance:.1f}%`")
                    st.progress(min(sodium_compliance / 100, 1))

                    st.markdown("<hr class='teal-divider'>", unsafe_allow_html=True)
                    st.markdown("<div class='stat-label' style='margin-bottom:10px;'>RECOMMENDATIONS</div>", unsafe_allow_html=True)

                    if total_sugars > sugar_daily_target:
                        st.warning(f"⚠ Sugar intake is {total_sugars - sugar_daily_target:.0f}g above target. Reduce sugary foods.")
                    else:
                        st.success("✓ Sugar intake is within acceptable range.")

                    if total_sodium > sodium_daily_target:
                        st.warning(f"⚠ Sodium intake is {total_sodium - sodium_daily_target:.0f}mg above target. Reduce salt and processed foods.")
                    else:
                        st.success("✓ Sodium intake is within acceptable range.")

                    if total_fiber < 25:
                        st.info(f"ℹ Fiber intake is {25 - total_fiber:.1f}g below recommended. Add more fruits, vegetables, and whole grains.")
                    else:
                        st.success("✓ Fiber intake is adequate.")

                    st.markdown("<hr class='teal-divider'>", unsafe_allow_html=True)
                    st.markdown("<div class='stat-label' style='margin-bottom:8px;'>DETAILED MEAL LOG</div>", unsafe_allow_html=True)
                    st.dataframe(
                        user_consumption[['date','meal_type','food_name','calories','sugars_g','sodium_mg','fiber_g']],
                        use_container_width=True
                    )
                else:
                    st.info(f"No consumption data available for {selected_user}")
    else:
        st.info("No user profiles available.")

# ── Footer ─────────────────────────────────────────────────────────────────
st.sidebar.markdown("<hr class='teal-divider'>", unsafe_allow_html=True)
st.sidebar.markdown("""
<div style='font-family:Space Mono,monospace;font-size:10px;color:#2a4a6b;line-height:1.8;'>
  Food Label Analysis System<br>
  Run <code style='color:#00d4aa;'>python startup.py</code> to verify deps.
</div>
""", unsafe_allow_html=True)
