import streamlit as st
import requests
import time
import json
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional
import threading

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Odds Alert Monitor",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# CUSTOM CSS — dark trading terminal aesthetic
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;600;700&family=Bebas+Neue&display=swap');

/* Base */
html, body, [class*="css"] {
    font-family: 'JetBrains Mono', monospace;
    background-color: #0a0c10;
    color: #c8d3e0;
}
.stApp { background-color: #0a0c10; }

/* Sidebar */
[data-testid="stSidebar"] {
    background-color: #0e1118;
    border-right: 1px solid #1e2530;
}
[data-testid="stSidebar"] * { font-family: 'JetBrains Mono', monospace !important; }

/* Inputs */
.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stSelectbox > div > div {
    background-color: #111520 !important;
    border: 1px solid #1e2d45 !important;
    border-radius: 4px !important;
    color: #7ec8e3 !important;
    font-family: 'JetBrains Mono', monospace !important;
}
.stTextInput > label, .stNumberInput > label, .stSelectbox > label {
    color: #4a6080 !important;
    font-size: 0.72rem !important;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, #0d3349, #0a1e35) !important;
    color: #7ec8e3 !important;
    border: 1px solid #1e4060 !important;
    border-radius: 4px !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-weight: 600;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    font-size: 0.75rem;
    padding: 0.5rem 1.2rem;
    transition: all 0.2s;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #113d5a, #0d2a47) !important;
    border-color: #7ec8e3 !important;
    box-shadow: 0 0 12px rgba(126, 200, 227, 0.15);
}

/* Metric cards */
.metric-card {
    background: #0e1320;
    border: 1px solid #1a2535;
    border-radius: 6px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.5rem;
}
.metric-label {
    font-size: 0.65rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #3a5070;
    margin-bottom: 0.2rem;
}
.metric-value {
    font-size: 1.8rem;
    font-weight: 700;
    font-family: 'Bebas Neue', sans-serif;
    letter-spacing: 0.05em;
}
.metric-delta {
    font-size: 0.72rem;
    color: #4a6080;
    margin-top: 0.1rem;
}

/* Alert banners */
.alert-back {
    background: linear-gradient(135deg, #0a2a14, #082010);
    border: 1px solid #1a5a2a;
    border-left: 4px solid #22c55e;
    border-radius: 4px;
    padding: 1rem 1.4rem;
    margin: 0.5rem 0;
}
.alert-lay {
    background: linear-gradient(135deg, #2a0a0a, #200808);
    border: 1px solid #5a1a1a;
    border-left: 4px solid #ef4444;
    border-radius: 4px;
    padding: 1rem 1.4rem;
    margin: 0.5rem 0;
}
.alert-title {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 1.3rem;
    letter-spacing: 0.1em;
    margin-bottom: 0.3rem;
}
.alert-back .alert-title { color: #22c55e; }
.alert-lay .alert-title { color: #ef4444; }
.alert-body { font-size: 0.75rem; color: #8a9ab0; line-height: 1.6; }

/* Log table */
.log-entry {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 0.5rem 0.8rem;
    border-bottom: 1px solid #111820;
    font-size: 0.72rem;
}
.log-entry:hover { background: #0e1520; }
.log-time { color: #2a4060; min-width: 80px; }
.log-type-back { color: #22c55e; font-weight: 600; min-width: 80px; }
.log-type-lay { color: #ef4444; font-weight: 600; min-width: 80px; }
.log-msg { color: #6a8aaa; }

/* Status dot */
.status-dot {
    display: inline-block;
    width: 8px; height: 8px;
    border-radius: 50%;
    margin-right: 6px;
    animation: pulse 2s infinite;
}
.status-live { background: #22c55e; }
.status-idle { background: #4a6080; animation: none; }
@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.3; }
}

/* Section headers */
.section-header {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 0.9rem;
    letter-spacing: 0.2em;
    color: #2a4060;
    text-transform: uppercase;
    margin: 1.2rem 0 0.6rem 0;
    border-bottom: 1px solid #111820;
    padding-bottom: 0.3rem;
}

/* Divider */
hr { border-color: #111820 !important; }

/* Toggle switch colors */
.stCheckbox > div { color: #4a6080 !important; font-size: 0.8rem; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# STATE
# ─────────────────────────────────────────────
def init_state():
    defaults = {
        "monitoring": False,
        "alert_log": [],
        "last_odds": {"home": None, "ah_minus": None, "ah_plus": None},
        "alert_count": {"back": 0, "lay": 0},
        "last_check": None,
        "telegram_bot_token": "",
        "odds_api_key": "",
        "telegram_chat_id": "",
        "tick_threshold": 0.10,
        "refresh_interval": 30,
        "match_id": "",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()


# ─────────────────────────────────────────────
# ODDS FETCHER (placeholder — swap for real API)
# ─────────────────────────────────────────────
def fetch_odds(match_id: str, api_key: str) -> dict:
    """
    Replace this function body with your real API call.
    Expected return format:
        {
            "home": 1.85,
            "ah_minus_05": 1.72,
            "ah_plus_05": 2.10
        }
    """
    # ── EXAMPLE: The Odds API (https://the-odds-api.com) ──
    # Uncomment and adapt when you have your key:
    #
    # url = f"https://api.the-odds-api.com/v4/sports/soccer/events/{match_id}/odds"
    # params = {
    #     "apiKey": api_key,
    #     "markets": "h2h,asian_handicap",
    #     "regions": "eu",
    #     "oddsFormat": "decimal"
    # }
    # response = requests.get(url, params=params, timeout=10)
    # data = response.json()
    # Parse data → extract home, ah_minus_05, ah_plus_05
    # return {"home": ..., "ah_minus_05": ..., "ah_plus_05": ...}

    # ── SIMULATION MODE (remove when using real API) ──
    import random
    base = round(random.uniform(1.70, 2.20), 2)
    return {
        "home":        round(base, 2),
        "ah_minus_05": round(base - random.uniform(0.00, 0.20), 2),
        "ah_plus_05":  round(base + random.uniform(0.00, 0.20), 2),
    }


# ─────────────────────────────────────────────
# INSTAGRAM ALERT SENDER
# ─────────────────────────────────────────────
def send_telegram_alert(alert_type: str, odds: dict, bot_token: str, chat_id: str):
    """
    Envia alerta via Telegram Bot API.
    Passos para configurar:
      1. Crie um bot no Telegram via @BotFather → obtenha o Bot Token
      2. Inicie uma conversa com o bot e acesse:
         https://api.telegram.org/bot<TOKEN>/getUpdates
         para descobrir seu Chat ID
      3. Insira Bot Token e Chat ID no sidebar do app
    """
    if not bot_token or not chat_id:
        return False, "Telegram Bot Token ou Chat ID não configurado."

    if alert_type == "BACK HOME":
        msg = (
            f"🟢 *BACK HOME ALERT*\n"
            f"`Odd Home : {odds['home']}`\n"
            f"`AH -0.5  : {odds['ah_minus_05']}`\n"
            f"`Diff     : +{round(odds['home'] - odds['ah_minus_05'], 2)}`\n"
            f"⏰ {datetime.now().strftime('%H:%M:%S')}"
        )
    else:
        msg = (
            f"🔴 *LAY HOME ALERT*\n"
            f"`Odd Home : {odds['home']}`\n"
            f"`AH +0.5  : {odds['ah_plus_05']}`\n"
            f"`AH -0.5  : {odds['ah_minus_05']}`\n"
            f"`Diff H/+ : +{round(odds['home'] - odds['ah_plus_05'], 2)}`\n"
            f"⏰ {datetime.now().strftime('%H:%M:%S')}"
        )

    # ── Telegram Bot API — sendMessage ──
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": msg,
        "parse_mode": "Markdown",
    }
    try:
        r = requests.post(url, json=payload, timeout=10)
        return r.ok, r.text
    except Exception as e:
        return False, str(e)


# ─────────────────────────────────────────────
# ALERT LOGIC
# ─────────────────────────────────────────────
def check_alerts(odds: dict, threshold: float) -> list[str]:
    alerts = []
    home      = odds["home"]
    ah_minus  = odds["ah_minus_05"]
    ah_plus   = odds["ah_plus_05"]

    # BACK HOME: Home odd ≥ AH -0.5 + threshold
    if home - ah_minus >= threshold:
        alerts.append("BACK HOME")

    # LAY HOME: Home odd ≥ AH +0.5 + threshold  AND  AH +0.5 > AH -0.5
    if (home - ah_plus >= threshold) and (ah_plus > ah_minus):
        alerts.append("LAY HOME")

    return alerts


# ─────────────────────────────────────────────
# SIDEBAR — CONFIGURATION
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="section-header">⚙ Configuration</div>', unsafe_allow_html=True)

    st.session_state.match_id = st.text_input(
        "Match ID / Event ID",
        value=st.session_state.match_id,
        placeholder="e.g. 1234567",
        help="ID do evento na sua API de odds"
    )

    st.markdown('<div class="section-header">🔑 API Keys</div>', unsafe_allow_html=True)

    st.session_state.odds_api_key = st.text_input(
        "Odds API Key",
        value=st.session_state.odds_api_key,
        type="password",
        placeholder="sua_chave_aqui"
    )
    st.session_state.telegram_bot_token = st.text_input(
        "Telegram Bot Token",
        value=st.session_state.telegram_bot_token,
        type="password",
        placeholder="123456789:AAF..."
    )
    st.session_state.telegram_chat_id = st.text_input(
        "Chat ID Telegram",
        value=st.session_state.telegram_chat_id,
        placeholder="ex: -100123456789"
    )

    st.markdown('<div class="section-header">📐 Parameters</div>', unsafe_allow_html=True)

    st.session_state.tick_threshold = st.number_input(
        "Tick Threshold (ticks)",
        min_value=0.01,
        max_value=1.00,
        value=st.session_state.tick_threshold,
        step=0.01,
        format="%.2f",
        help="Diferença mínima para disparar alerta (padrão: 0.10 = 10 ticks)"
    )
    st.session_state.refresh_interval = st.number_input(
        "Refresh Interval (seconds)",
        min_value=5,
        max_value=300,
        value=st.session_state.refresh_interval,
        step=5,
        help="Intervalo entre consultas à API"
    )

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("▶ START", use_container_width=True):
            st.session_state.monitoring = True
    with col2:
        if st.button("■ STOP", use_container_width=True):
            st.session_state.monitoring = False

    st.markdown("---")
    if st.button("🗑 Clear Log", use_container_width=True):
        st.session_state.alert_log = []
        st.session_state.alert_count = {"back": 0, "lay": 0}


# ─────────────────────────────────────────────
# MAIN PANEL
# ─────────────────────────────────────────────

# Header
st.markdown("""
<div style="display:flex; align-items:baseline; gap:1rem; margin-bottom:0.2rem;">
    <span style="font-family:'Bebas Neue',sans-serif; font-size:2.2rem; letter-spacing:0.1em; color:#7ec8e3;">
        ODDS MONITOR
    </span>
    <span style="font-size:0.7rem; color:#2a4060; letter-spacing:0.15em; text-transform:uppercase;">
        Asian Handicap Arbitrage Alerts
    </span>
</div>
<hr style="margin-top:0; margin-bottom:1.2rem;">
""", unsafe_allow_html=True)

# Status bar
status_cls  = "status-live" if st.session_state.monitoring else "status-idle"
status_text = "MONITORING" if st.session_state.monitoring else "IDLE"
last_check  = st.session_state.last_check or "—"
st.markdown(
    f'<span class="status-dot {status_cls}"></span>'
    f'<span style="font-size:0.72rem; text-transform:uppercase; letter-spacing:0.1em; color:#4a6080;">'
    f'{status_text} &nbsp;|&nbsp; Last check: {last_check}'
    f'</span>',
    unsafe_allow_html=True
)
st.markdown("<br>", unsafe_allow_html=True)

# ── Odds display ──
col1, col2, col3, col4 = st.columns(4)

def odd_color(val):
    if val is None: return "#3a5070"
    return "#7ec8e3"

odds = st.session_state.last_odds

with col1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Back Home</div>
        <div class="metric-value" style="color:{odd_color(odds['home'])}">
            {odds['home'] if odds['home'] else '—'}
        </div>
        <div class="metric-delta">Mercado principal</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    val = odds['ah_minus']
    diff = round(odds['home'] - val, 2) if val and odds['home'] else None
    diff_str = f"Δ {diff:+.2f}" if diff is not None else ""
    col_diff = "#22c55e" if diff is not None and diff >= st.session_state.tick_threshold else "#3a5070"
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">AH −0.5</div>
        <div class="metric-value" style="color:{odd_color(val)}">{val if val else '—'}</div>
        <div class="metric-delta" style="color:{col_diff}">{diff_str}</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    val = odds['ah_plus']
    diff = round(odds['home'] - val, 2) if val and odds['home'] else None
    diff_str = f"Δ {diff:+.2f}" if diff is not None else ""
    col_diff = "#ef4444" if diff is not None and diff >= st.session_state.tick_threshold else "#3a5070"
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">AH +0.5</div>
        <div class="metric-value" style="color:{odd_color(val)}">{val if val else '—'}</div>
        <div class="metric-delta" style="color:{col_diff}">{diff_str}</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    total_alerts = st.session_state.alert_count["back"] + st.session_state.alert_count["lay"]
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Alerts Fired</div>
        <div class="metric-value" style="color:#7ec8e3">{total_alerts}</div>
        <div class="metric-delta">
            <span style="color:#22c55e">▲ {st.session_state.alert_count['back']} BACK</span>
            &nbsp;
            <span style="color:#ef4444">▼ {st.session_state.alert_count['lay']} LAY</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ── Alert rules reference ──
st.markdown('<div class="section-header">📋 Alert Rules</div>', unsafe_allow_html=True)
rc1, rc2 = st.columns(2)
with rc1:
    st.markdown(f"""
    <div class="alert-back" style="opacity:0.7;">
        <div class="alert-title">🟢 BACK HOME</div>
        <div class="alert-body">
            Odd Home − AH −0.5 ≥ <b style="color:#c8d3e0">{st.session_state.tick_threshold:.2f}</b><br>
            <i>Home favorito subvalorizado no handicap negativo</i>
        </div>
    </div>
    """, unsafe_allow_html=True)
with rc2:
    st.markdown(f"""
    <div class="alert-lay" style="opacity:0.7;">
        <div class="alert-title">🔴 LAY HOME</div>
        <div class="alert-body">
            Odd Home − AH +0.5 ≥ <b style="color:#c8d3e0">{st.session_state.tick_threshold:.2f}</b><br>
            E &nbsp;AH +0.5 &gt; AH −0.5<br>
            <i>Home sobrevalorizado — oportunidade de lay</i>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ── Alert log ──
st.markdown('<div class="section-header">📡 Alert Log</div>', unsafe_allow_html=True)

if not st.session_state.alert_log:
    st.markdown(
        '<div style="color:#2a4060; font-size:0.75rem; padding:0.8rem;">Nenhum alerta disparado ainda. Inicie o monitoramento.</div>',
        unsafe_allow_html=True
    )
else:
    log_html = ""
    for entry in reversed(st.session_state.alert_log[-50:]):
        type_cls = "log-type-back" if entry["type"] == "BACK HOME" else "log-type-lay"
        icon = "🟢" if entry["type"] == "BACK HOME" else "🔴"
        log_html += f"""
        <div class="log-entry">
            <span class="log-time">{entry['time']}</span>
            <span class="{type_cls}">{icon} {entry['type']}</span>
            <span class="log-msg">{entry['msg']}</span>
        </div>
        """
    st.markdown(f'<div style="border:1px solid #111820; border-radius:4px;">{log_html}</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────
# MONITORING LOOP (on page refresh)
# ─────────────────────────────────────────────
if st.session_state.monitoring:
    # Fetch odds
    try:
        raw = fetch_odds(
            match_id=st.session_state.match_id,
            api_key=st.session_state.odds_api_key,
        )
        st.session_state.last_odds = {
            "home":     raw["home"],
            "ah_minus": raw["ah_minus_05"],
            "ah_plus":  raw["ah_plus_05"],
        }
        st.session_state.last_check = datetime.now().strftime("%H:%M:%S")

        # Check alert conditions
        triggered = check_alerts(raw, st.session_state.tick_threshold)

        for alert_type in triggered:
            ok, response = send_telegram_alert(
                alert_type=alert_type,
                odds=raw,
                bot_token=st.session_state.telegram_bot_token,
                chat_id=st.session_state.telegram_chat_id,
            )

            log_entry = {
                "time": datetime.now().strftime("%H:%M:%S"),
                "type": alert_type,
                "msg":  (
                    f"H={raw['home']} | AH−={raw['ah_minus_05']} | AH+={raw['ah_plus_05']} "
                    f"| {'✓ Telegram sent' if ok else '✗ Telegram fail'}"
                ),
            }
            st.session_state.alert_log.append(log_entry)

            if alert_type == "BACK HOME":
                st.session_state.alert_count["back"] += 1
            else:
                st.session_state.alert_count["lay"] += 1

    except Exception as e:
        st.error(f"Erro ao buscar odds: {e}")

    # Auto-refresh
    time.sleep(st.session_state.refresh_interval)
    st.rerun()
