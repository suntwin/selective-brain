"""Live exam-style countdown with a pace marker (client-side JS, re-rendered each rerun)."""
from __future__ import annotations

import json

import streamlit.components.v1 as components


def countdown(start_ms: int, limit_s: int, done: int, total: int, pace_s: int, label="Time left"):
    cfg = json.dumps({"start": start_ms, "limit": limit_s, "done": done, "total": total,
                      "pace": pace_s, "label": label})
    components.html(
        """
<div id="t">
  <div class="row">
    <div class="clock"><span id="ico">⏳</span> <span id="mm">--:--</span></div>
    <div class="right"><div id="lbl"></div><div id="pace"></div></div>
  </div>
  <div class="bar"><span id="fill"></span><i id="me"></i></div>
</div>
<style>
@import url('https://fonts.googleapis.com/css2?family=Fredoka:wght@600;700&family=Nunito:wght@700;800&display=swap');
body{margin:0;font-family:Nunito,sans-serif;background:transparent}
#t{background:linear-gradient(135deg,#ffffffee,#fff4fbee);border:2px solid #f1d9ff;border-radius:22px;padding:10px 16px 12px;
   box-shadow:0 10px 26px -16px #9b7bff99}
.row{display:flex;align-items:center;justify-content:space-between;gap:12px}
.clock{font-family:Fredoka,sans-serif;font-size:38px;font-weight:700;color:#3b2257;letter-spacing:1px}
.right{text-align:right;font-weight:800;color:#6c5785;font-size:14px}
#pace{font-size:15px;margin-top:2px}
.bar{position:relative;height:14px;border-radius:999px;background:#f3e9ff;margin-top:8px;overflow:visible}
.bar span{display:block;height:100%;border-radius:999px;background:linear-gradient(90deg,#38d9c9,#9b7bff,#ff4fa0);transition:width .9s linear}
.bar i{position:absolute;top:-7px;font-style:normal;font-size:20px;transform:translateX(-50%);transition:left .4s}
.low .clock{color:#ff4fa0;animation:pulse 1s infinite}
@keyframes pulse{50%{transform:scale(1.04)}}
</style>
<script>
const c = """ + cfg + """;
const $ = id => document.getElementById(id);
function fmt(s){s=Math.max(0,Math.floor(s));return String(Math.floor(s/60)).padStart(2,'0')+':'+String(s%60).padStart(2,'0')}
function tick(){
  const el=(Date.now()-c.start)/1000, left=c.limit-el;
  $('lbl').textContent = c.label + ' · Q ' + Math.min(c.done+1,c.total) + ' of ' + c.total;
  if(left>=0){ $('mm').textContent=fmt(left); $('ico').textContent= left<120?'🔥':'⏳'; }
  else { $('mm').textContent='+'+fmt(-left); $('ico').textContent='🌙'; }
  document.getElementById('t').classList.toggle('low', left<120 && left>=0);
  $('fill').style.width = Math.min(100, Math.max(0, left/c.limit*100)) + '%';
  $('me').style.left = Math.min(100, c.done/c.total*100) + '%';
  $('me').textContent='🦄';
  const expected = Math.min(c.total, el / c.pace);
  const diff = c.done - expected;
  let msg;
  if(left<0) msg='Overtime — keep going, you\\'ve got this 💪';
  else if(diff >= 1) msg='✨ Ahead of exam pace by ' + Math.floor(diff) + (Math.floor(diff)==1?' question':' questions');
  else if(diff > -1) msg='💖 Right on exam pace';
  else msg='🐢 ' + Math.ceil(-diff) + ' behind exam pace — skip & come back?';
  $('pace').textContent = msg;
}
tick(); setInterval(tick, 1000);
</script>
""",
        height=118,
    )
