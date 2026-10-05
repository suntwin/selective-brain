"""Sparkly theme: CSS + small HTML helpers."""
from __future__ import annotations

import html as _html

import streamlit as st

CSS = r"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fredoka:wght@400;500;600;700&family=Nunito:wght@400;600;700;800&display=swap');

:root{
  --pink:#ff4fa0; --pink2:#ff8cc6; --lav:#9b7bff; --lav2:#c9b6ff; --aqua:#38d9c9;
  --gold:#ffc63d; --ink:#3b2257; --ink2:#6c5785; --card:#ffffffcc; --line:#f1d9ff;
  --ok:#22c08a; --bad:#ff5b7a; --amber:#ffb23d;
}
html, body, [class*="css"], .stApp, .stMarkdown, button, input, textarea, select{
  font-family:'Nunito', system-ui, sans-serif !important; color:var(--ink);
}
h1,h2,h3,h4,.sb-title{font-family:'Fredoka', 'Nunito', sans-serif !important; color:var(--ink); letter-spacing:.2px}
.stApp{
  background:
    radial-gradient(1200px 600px at 10% -10%, #ffe1f1 0%, transparent 60%),
    radial-gradient(900px 600px at 110% 10%, #e3dcff 0%, transparent 55%),
    radial-gradient(900px 700px at 50% 120%, #d6fbf5 0%, transparent 60%),
    linear-gradient(160deg,#fff4fb 0%,#f6f0ff 50%,#effcff 100%) !important;
}
/* twinkling glitter layer */
.stApp::before, .stApp::after{
  content:""; position:fixed; inset:0; pointer-events:none; z-index:0;
  background-image:
    radial-gradient(2px 2px at 20px 30px,#ff8cc6 50%,transparent 51%),
    radial-gradient(1.5px 1.5px at 120px 80px,#9b7bff 50%,transparent 51%),
    radial-gradient(2px 2px at 220px 160px,#ffc63d 50%,transparent 51%),
    radial-gradient(1.5px 1.5px at 300px 40px,#38d9c9 50%,transparent 51%),
    radial-gradient(2.5px 2.5px at 380px 220px,#ffffff 50%,transparent 51%),
    radial-gradient(1.5px 1.5px at 60px 260px,#ff4fa0 50%,transparent 51%);
  background-size:420px 300px; opacity:.55; animation:twinkle 4s ease-in-out infinite alternate;
}
.stApp::after{background-size:300px 380px; background-position:150px 90px; animation-delay:2s; opacity:.4}
@keyframes twinkle{0%{opacity:.15}100%{opacity:.65}}
[data-testid="stAppViewContainer"] > .main, section.main, [data-testid="stMain"]{position:relative; z-index:1}
[data-testid="stHeader"]{background:transparent}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#ffe6f3 0%,#efe7ff 100%) !important; border-right:2px solid var(--line)}
.block-container{padding-top:1.6rem; max-width:1100px}

/* buttons: default (secondary) = sparkly gradient, tertiary = white pill */
.stButton>button, .stFormSubmitButton>button, .stDownloadButton>button{
  border-radius:18px !important; font-weight:800 !important; min-height:2.9rem;
  position:relative; overflow:hidden; transition:transform .12s ease, box-shadow .12s ease;
}
button[data-testid="stBaseButton-secondary"], button[data-testid="stBaseButton-primary"],
button[data-testid="stBaseButton-secondaryFormSubmit"], button[data-testid="stBaseButton-primaryFormSubmit"]{
  border:0 !important; color:#fff !important; padding:.6rem 1.1rem !important;
  background:linear-gradient(135deg,var(--pink) 0%,var(--lav) 100%) !important;
  box-shadow:0 6px 18px -6px #ff4fa088, inset 0 -3px 0 #0000001a !important;
}
button[data-testid^="stBaseButton-secondary"] p, button[data-testid^="stBaseButton-primary"] p{color:#fff !important; font-weight:800 !important; font-size:1.02rem}
button[data-testid^="stBaseButton-secondary"]:hover, button[data-testid^="stBaseButton-primary"]:hover{transform:translateY(-2px) scale(1.01); box-shadow:0 10px 24px -6px #9b7bff99 !important}
button[data-testid^="stBaseButton-secondary"]::after, button[data-testid^="stBaseButton-primary"]::after{
  content:""; position:absolute; top:-50%; left:-60%; width:40%; height:200%;
  background:linear-gradient(100deg,transparent,#ffffff88,transparent); transform:rotate(18deg);
  animation:shine 3.2s ease-in-out infinite; pointer-events:none;
}
@keyframes shine{0%{left:-60%}55%{left:130%}100%{left:130%}}
button[data-testid="stBaseButton-tertiary"]{
  background:#fff !important; border:2px solid var(--lav2) !important; color:var(--ink) !important;
  padding:.6rem 1.1rem !important; box-shadow:0 4px 12px -6px #9b7bff55 !important;
}
button[data-testid="stBaseButton-tertiary"] p{color:var(--ink) !important; font-weight:800 !important; font-size:1.02rem}
button[data-testid="stBaseButton-tertiary"]:hover{border-color:var(--pink) !important; background:#fff5fb !important; transform:translateY(-1px)}
/* answer option buttons: bigger, left-aligned */
[class*="st-key-opt_"] button[data-testid="stBaseButton-tertiary"]{min-height:3.6rem; justify-content:flex-start}
[class*="st-key-opt_"] button[data-testid="stBaseButton-tertiary"] p{font-size:1.2rem !important}
/* inputs */
.stTextInput input, .stTextArea textarea, .stNumberInput input{border-radius:14px !important; border:2px solid var(--line) !important; background:#fff !important}
[data-baseweb="select"]>div{border-radius:14px !important}
[data-testid="stExpander"]{border-radius:18px; border:2px solid var(--line); background:#ffffffaa}
div[data-testid="stTabs"] button p{font-family:'Fredoka',sans-serif; font-size:1.05rem}
[data-testid="stMetric"]{background:var(--card); border:2px solid var(--line); border-radius:18px; padding:.7rem .9rem}
[data-testid="stProgress"] > div > div > div > div{background:linear-gradient(90deg,var(--pink),var(--lav),var(--aqua)) !important}

/* cards */
.sb-card{background:var(--card); backdrop-filter:blur(6px); border:2px solid var(--line);
  border-radius:24px; padding:1.1rem 1.25rem; box-shadow:0 10px 30px -18px #9b7bff88; margin-bottom:.9rem}
.sb-hero{background:linear-gradient(135deg,#ff7ab8 0%,#a98bff 55%,#62e3d4 100%); color:#fff;
  border-radius:28px; padding:1.3rem 1.5rem; position:relative; overflow:hidden;
  box-shadow:0 18px 40px -20px #9b7bffaa; margin-bottom:1rem}
.sb-hero *{color:#fff !important}
.sb-hero::after{content:"✦ ✧ ✦ ✧ ✦"; position:absolute; right:18px; top:10px; font-size:22px; opacity:.7; letter-spacing:6px; animation:twinkle 1.8s infinite alternate}
.sb-hero h1{margin:0; font-size:2.0rem}
.sb-sub{opacity:.95; font-weight:700}
.sb-pill{display:inline-block; padding:.22rem .7rem; border-radius:999px; font-weight:800; font-size:.82rem;
  background:#fff; color:var(--ink); border:2px solid var(--line); margin:0 .3rem .3rem 0}
.sb-pill.pink{background:#ffe3f1; border-color:#ffc2df}
.sb-pill.lav{background:#efe8ff; border-color:#d9cbff}
.sb-pill.aqua{background:#dcfbf7; border-color:#a9efe6}
.sb-pill.gold{background:#fff4d6; border-color:#ffe099}
.sb-stat{display:flex; gap:.8rem; flex-wrap:wrap}
.sb-stat .box{flex:1 1 140px; background:#ffffffd9; border:2px solid var(--line); border-radius:22px; padding:.8rem 1rem; text-align:center}
.sb-stat .big{font-family:'Fredoka',sans-serif; font-size:2rem; font-weight:700; line-height:1.1}
.sb-stat .lbl{font-weight:800; color:var(--ink2); font-size:.85rem}
.sb-bar{height:16px; border-radius:999px; background:#f3e9ff; overflow:hidden; border:2px solid #fff}
.sb-bar>span{display:block; height:100%; border-radius:999px; background:linear-gradient(90deg,var(--pink),var(--lav),var(--aqua)); background-size:200% 100%; animation:flow 3s linear infinite}
@keyframes flow{0%{background-position:0 0}100%{background-position:200% 0}}
.sb-q{font-size:1.25rem; font-weight:700; line-height:1.55; white-space:pre-wrap}
.sb-ok{background:#e4fff3; border:2px solid #9ff0cc; border-radius:20px; padding:.8rem 1rem; font-weight:800}
.sb-bad{background:#fff0f3; border:2px solid #ffc1cd; border-radius:20px; padding:.8rem 1rem; font-weight:800}
.sb-tip{background:#fff9e6; border:2px dashed #ffd76a; border-radius:18px; padding:.7rem 1rem}
.sb-badge{display:inline-flex; flex-direction:column; align-items:center; justify-content:center; width:112px; height:118px;
  margin:.3rem; border-radius:24px; background:linear-gradient(160deg,#fff 0%,#fff3fa 100%); border:2px solid var(--line);
  text-align:center; font-weight:800; font-size:.78rem; vertical-align:top; padding:.4rem}
.sb-badge .ic{font-size:2.1rem; line-height:1.2}
.sb-badge.locked{filter:grayscale(1); opacity:.38}
.sb-badge.new{animation:pop .8s ease; border-color:var(--gold); box-shadow:0 0 0 4px #ffe58a88}
@keyframes pop{0%{transform:scale(.5)}70%{transform:scale(1.12)}100%{transform:scale(1)}}
.sb-topic{display:inline-block; margin:.25rem; padding:.5rem .8rem; border-radius:16px; font-weight:800; font-size:.85rem; border:2px solid #fff}
.sb-topic.green{background:#d9fbe9; color:#11734f}
.sb-topic.amber{background:#fff1d1; color:#8a5a00}
.sb-topic.red{background:#ffe0e6; color:#a3203d}
.sb-topic.grey{background:#f2eef7; color:#8d7fa3}
.sb-small{font-size:.85rem; color:var(--ink2); font-weight:600}
.sb-scroll{overflow-x:auto; padding:.4rem .6rem}
.sb-table{width:100%; border-collapse:collapse; font-size:.92rem; min-width:820px}
.sb-table th, .sb-table td{border:0 !important; border-bottom:1px solid var(--line) !important}
.sb-table th{font-family:'Fredoka',sans-serif; font-weight:600; text-align:left; color:var(--ink2); padding:.55rem .5rem; border-bottom:2px solid var(--line); white-space:nowrap}
.sb-table td{padding:.6rem .5rem; border-bottom:1px solid var(--line); vertical-align:top}
.sb-table tr:last-child td{border-bottom:0 !important}
.sb-table .nw{white-space:nowrap}
.sb-table td.why{min-width:300px}
.sb-table .sb-pill{white-space:nowrap}
.sb-table .n{text-align:right; font-weight:800; font-variant-numeric:tabular-nums; white-space:nowrap}
@media (max-width: 640px){
  .sb-hero h1{font-size:1.45rem} .sb-hero{padding:1rem 1.1rem} .sb-hero::after{display:none}
  .sb-stat .box{flex:1 1 42%} .sb-stat .big{font-size:1.5rem} .sb-q{font-size:1.08rem}
  .sb-badge{width:96px; height:108px}
}
</style>
"""


def apply():
    st.markdown(CSS, unsafe_allow_html=True)


def md(s) -> str:
    """Escape $ so Streamlit markdown doesn't treat money as LaTeX."""
    return str(s or "").replace("$", "\\$")


def esc(s) -> str:
    return _html.escape(str(s) if s is not None else "")


def img(src, max_w=460) -> str:
    """Question diagram: a data: URI (embedded in the drill JSON) or an https URL."""
    if not src:
        return ""
    src = str(src)
    if not (src.startswith("data:image/") or src.startswith("https://")):
        return ""
    return (f'<div style="margin-top:10px"><img src="{esc(src)}" style="max-width:min(100%,{max_w}px);'
            f'border-radius:14px;border:2px solid #f1d9ff;background:#fff"/></div>')


def card(body_html: str, cls: str = "sb-card"):
    st.markdown(f'<div class="{cls}">{body_html}</div>', unsafe_allow_html=True)


def bar(pct: float) -> str:
    return f'<div class="sb-bar"><span style="width:{max(0, min(1, pct)) * 100:.1f}%"></span></div>'


def pill(text, color="lav") -> str:
    return f'<span class="sb-pill {color}">{esc(text)}</span>'


def stars(n: int, out_of: int = 3) -> str:
    return "⭐" * n + "☆" * (out_of - n)


def xp_toasts():
    for amount, reason in st.session_state.pop("xp_toasts", []):
        st.toast(f"+{amount} XP · {reason}", icon="✨")


def sparkle_burst(key: str = "x"):
    """Confetti of stars & hearts (pure CSS/JS in an iframe-free overlay)."""
    st.markdown(
        """
<div class="sb-burst">""" + "".join(
            f'<span style="left:{(i * 37) % 100}%;animation-delay:{(i % 7) * 0.12:.2f}s;font-size:{18 + (i * 7) % 18}px">'
            f'{"✨💖⭐🌟💫🦄🌈💜"[i % 8]}</span>' for i in range(28)) + """</div>
<style>
.sb-burst{position:fixed; inset:0; pointer-events:none; z-index:9999; overflow:hidden}
.sb-burst span{position:absolute; top:-40px; animation:fall 2.6s ease-in forwards}
@keyframes fall{0%{transform:translateY(0) rotate(0); opacity:1}100%{transform:translateY(110vh) rotate(540deg); opacity:0}}
</style>""",
        unsafe_allow_html=True,
    )
