#!/usr/bin/env python3
"""Read results_all.json and emit a self-contained index.html leaderboard page."""
import json, datetime, sys

data = json.load(open("results_all.json", encoding="utf-8"))
DATE = sys.argv[1] if len(sys.argv) > 1 else "2026-07-08"
payload = json.dumps(data, ensure_ascii=False)

HTML = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Tokenizer Fairness in 2026</title>
<style>
:root{--bg:#faf9f6;--card:#fff;--ink:#1a1a19;--mut:#6b6a65;--line:#e5e3da;--accent:#0f6e56}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.65 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,"PingFang SC","Microsoft YaHei",sans-serif}
.wrap{max-width:1080px;margin:0 auto;padding:0 20px}
header{padding:56px 0 28px;border-bottom:1px solid var(--line)}
h1{font-size:34px;font-weight:650;letter-spacing:-.02em;margin:0 0 10px}
.sub{font-size:18px;color:var(--mut);max-width:720px;margin:0}
h2{font-size:24px;font-weight:600;letter-spacing:-.01em;margin:52px 0 6px}
h3{font-size:17px;font-weight:600;margin:28px 0 8px}
p{margin:10px 0}
.lead{color:var(--mut);margin:0 0 18px}
a{color:var(--accent);text-decoration:none}a:hover{text-decoration:underline}
code{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.88em;background:#f0efe9;padding:1px 5px;border-radius:4px}
.pills{display:flex;flex-wrap:wrap;gap:8px;margin:18px 0 6px}
.pill{font-size:13px;color:var(--mut);background:var(--card);border:1px solid var(--line);border-radius:999px;padding:5px 12px}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:20px 22px;margin:16px 0}
table{border-collapse:collapse;width:100%;font-size:14px}
.lb td,.lb th{padding:9px 10px;text-align:right;border-bottom:1px solid var(--line)}
.lb th{color:var(--mut);font-weight:600;font-size:12px;text-transform:uppercase;letter-spacing:.04em;cursor:default}
.lb td:first-child,.lb th:first-child,.lb td:nth-child(2),.lb th:nth-child(2){text-align:left}
.rankn{color:var(--mut);width:26px}
.win{color:var(--accent);font-weight:600}
.bar{height:8px;border-radius:4px;background:var(--accent);display:inline-block;vertical-align:middle;margin-left:8px}
.base{color:var(--mut)}
.base td{background:#f6f5ef}
.controls{display:flex;gap:12px;align-items:center;flex-wrap:wrap;margin:14px 0}
input[type=search]{font:15px inherit;padding:8px 12px;border:1px solid var(--line);border-radius:8px;background:#fff;min-width:220px}
.scroll{overflow-x:auto;border:1px solid var(--line);border-radius:12px}
.grid{border-collapse:collapse;font-size:13px;white-space:nowrap;min-width:900px}
.grid th,.grid td{padding:6px 8px;text-align:center;border-bottom:1px solid #efeee7}
.grid th{position:sticky;top:0;background:#f6f5ef;color:var(--mut);font-weight:600;font-size:11px;cursor:pointer;user-select:none}
.grid th:hover{color:var(--ink)}
.grid td.lang{text-align:left;position:sticky;left:0;background:#fff;font-weight:500}
.grid td.code{text-align:left;color:var(--mut);font-family:ui-monospace,monospace;font-size:11px}
.legend{display:flex;flex-wrap:wrap;gap:12px;align-items:center;font-size:12px;color:var(--mut);margin:10px 0}
.sw{width:14px;height:14px;border-radius:3px;display:inline-block;vertical-align:-2px;margin-right:4px}
.foot{color:var(--mut);font-size:14px;border-top:1px solid var(--line);margin-top:48px;padding:24px 0 60px}
.up{color:#a32d2d}.down{color:#0f6e56}
</style>
</head>
<body>
<header><div class="wrap">
<h1>Tokenizer fairness in 2026</h1>
<p class="sub">The same sentence costs more tokens in some languages than others — you pay more, wait longer, and fit less context. This reproduces the NeurIPS&nbsp;2023 finding and asks: three years on, did the gap close?</p>
<div class="pills" id="pills"></div>
</div></header>

<div class="wrap">
<p class="lead" style="margin-top:22px">Following <a href="https://arxiv.org/abs/2305.15425">Petrov et&nbsp;al. (2023)</a>, the <b>premium</b> of a language is how many tokens its text needs relative to English for the same content (FLORES-200, <span id="nsent"></span> parallel sentences). Premium&nbsp;1.0 = as cheap as English; 15 = fifteen times more expensive. Lower is fairer.</p>

<h2>The 2026 leaderboard</h2>
<p class="lead">Latest tokenizer from each lab, ranked by <b>median premium</b> across <span id="nlang"></span> languages (the typical language's cost). <code>mean</code> and the tail (<code>p90</code>, worst&nbsp;10%) show how the low-resource languages fare. GPT-4's 2023 tokenizer is shown as the baseline.</p>
<div class="card" style="padding:8px 14px"><table class="lb" id="lb"></table></div>

<h2>Every language, every tokenizer</h2>
<p class="lead">Premium for all <span id="nlang2"></span> FLORES-200 languages. Click a column header to sort; type to filter. Cell colour = premium.</p>
<div class="legend" id="legend"></div>
<div class="controls"><input type="search" id="filter" placeholder="filter languages… (e.g. arab, kor, shan)"></div>
<div class="scroll"><table class="grid" id="grid"></table></div>

<h2>What the numbers say</h2>
<div class="card" id="findings"></div>

<h2>Method &amp; reproduction</h2>
<p class="lead">Every number here is reproducible. <code>premium(L) = Σ tokens(L devtest) / Σ tokens(English devtest)</code>, no special tokens, over the FLORES-200 <code>devtest</code> split.</p>
<ul>
<li><b>Data:</b> FLORES-200 (200 languages, parallel). Get it via the tarball at <code>dl.fbaipublicfiles.com/nllb/flores200_dataset.tar.gz</code> or a HuggingFace token.</li>
<li><b>Tokenizers:</b> OpenAI via <code>tiktoken</code>; the rest via each model's public <code>tokenizer.json</code> / SentencePiece / <code>tiktoken.model</code>. Repos are listed in the code.</li>
<li><b>Caveats:</b> Doubao is a closed product — its column uses ByteDance's open <b>Seed-OSS</b> tokenizer as a proxy. Gated labs (Meta, Google) use ungated mirrors of the identical tokenizer. Kimi's regex pattern is approximated. Latest OpenAI public tokenizer is <code>o200k</code>.</li>
<li><b>Code:</b> see the repository — <code>reproduce_tokenization_fairness.py</code>, <code>loaders_full.py</code>, <code>compute_all.py</code>.</li>
</ul>

<div class="foot"><div class="wrap" style="padding:0">
Reproduction &amp; extension of <a href="https://arxiv.org/abs/2305.15425">Petrov, La&nbsp;Malfa, Torr, Bibi — “Language Model Tokenizers Introduce Unfairness Between Languages” (NeurIPS 2023)</a>. Generated __DATE__. Data: FLORES-200. Not affiliated with the paper's authors or any model provider.
</div></div>
</div>

<script>
const DATA = __DATA__;
const RANKED = DATA.tokenizers.filter(t=>t.rank);
const BASE = DATA.tokenizers.filter(t=>!t.rank);
const byMedian = [...RANKED].sort((a,b)=>a.median-b.median);
const $=(id)=>document.getElementById(id);
$("nsent").textContent = DATA.n_sent.toLocaleString();
$("nlang").textContent = DATA.n_langs; $("nlang2").textContent = DATA.n_langs;

$("pills").innerHTML = [`${DATA.tokenizers.length} tokenizers`,`${DATA.n_langs} languages`,
 `${DATA.n_sent.toLocaleString()} sentences each`,"FLORES-200 devtest"].map(t=>`<span class="pill">${t}</span>`).join("");

function color(p){
  if(p<=1.05)return["#9FE1CB","#085041"];
  if(p<=1.5)return["#FAEEDA","#412402"];
  if(p<=2.5)return["#FAC775","#412402"];
  if(p<=5)return["#D85A30","#fff"];
  if(p<=9)return["#A32D2D","#fff"];
  return["#791F1F","#fff"];
}

// leaderboard
const maxMed=Math.max(...RANKED.map(t=>t.median));
let lb=`<tr><th></th><th>Tokenizer</th><th>Lab</th><th>Median</th><th>Mean</th><th>p90</th><th>Worst</th><th>≤2× share</th><th>Vocab</th></tr>`;
byMedian.forEach((t,i)=>{
  const w=Math.round(t.median/maxMed*90);
  lb+=`<tr><td class="rankn">${i+1}</td><td class="${i==0?'win':''}">${t.name}</td><td class="base">${t.lab}</td>`+
      `<td><b>${t.median.toFixed(2)}</b><span class="bar" style="width:${w}px"></span></td>`+
      `<td>${t.mean.toFixed(2)}</td><td>${t.p90.toFixed(1)}</td><td>${t.max.toFixed(1)}</td>`+
      `<td>${t.share2x.toFixed(0)}%</td><td class="base">${t.vocab.toLocaleString()}</td></tr>`;
});
BASE.forEach(t=>{
  lb+=`<tr class="base"><td>—</td><td>${t.name} <span style="font-size:11px">(2023 baseline)</span></td><td>${t.lab}</td>`+
      `<td>${t.median.toFixed(2)}</td><td>${t.mean.toFixed(2)}</td><td>${t.p90.toFixed(1)}</td><td>${t.max.toFixed(1)}</td>`+
      `<td>${t.share2x.toFixed(0)}%</td><td>${t.vocab.toLocaleString()}</td></tr>`;
});
$("lb").innerHTML=lb;

// legend
$("legend").innerHTML="premium: "+[["≤1 (≤English)","#9FE1CB"],["1–1.5","#FAEEDA"],["1.5–2.5","#FAC775"],
 ["2.5–5","#D85A30"],["5–9","#A32D2D"],[">9","#791F1F"]].map(([l,c])=>`<span><span class="sw" style="background:${c}"></span>${l}</span>`).join("");

// grid
const cols=[...byMedian,...BASE];
const rowTypical=(c)=>{const v=byMedian.map(t=>t.premiums[c]).sort((a,b)=>a-b);return v[Math.floor(v.length/2)];};
let sortKey="__typ", sortDir=-1;
function render(){
  const f=$("filter").value.trim().toLowerCase();
  let rows=DATA.codes.filter(c=>c!=="eng_Latn").map(c=>({c,name:DATA.names[c],typ:rowTypical(c)}));
  if(f)rows=rows.filter(r=>r.name.toLowerCase().includes(f)||r.c.toLowerCase().includes(f));
  rows.sort((a,b)=>{
    let x,y;
    if(sortKey==="__name"){x=a.name;y=b.name;return sortDir*(x<y?-1:x>y?1:0);}
    if(sortKey==="__typ"){x=a.typ;y=b.typ;}else{x=cols.find(t=>t.name===sortKey).premiums[a.c];y=cols.find(t=>t.name===sortKey).premiums[b.c];}
    return sortDir*(x-y);
  });
  let h=`<tr><th onclick="sortBy('__name')">Language</th><th onclick="sortBy('__name')">Code</th>`+
        `<th onclick="sortBy('__typ')">Typical</th>`+
        cols.map(t=>`<th onclick="sortBy('${t.name}')">${t.name}${t.rank?'':' ·23'}</th>`).join("")+`</tr>`;
  rows.forEach(r=>{
    const tc=color(r.typ);
    h+=`<tr><td class="lang">${r.name}</td><td class="code">${r.c}</td>`+
       `<td style="background:${tc[0]};color:${tc[1]};font-weight:600">${r.typ.toFixed(2)}</td>`+
       cols.map(t=>{const p=t.premiums[r.c],c=color(p);return `<td style="background:${c[0]};color:${c[1]}">${p.toFixed(2)}</td>`;}).join("")+`</tr>`;
  });
  $("grid").innerHTML=h;
}
window.sortBy=(k)=>{ if(sortKey===k)sortDir*=-1; else{sortKey=k;sortDir=(k==="__name")?1:-1;} render(); };
$("filter").addEventListener("input",render);
render();

// findings
const best=byMedian[0], base=BASE[0];
function prem(tname,code){return (cols.find(t=>t.name===tname)||{premiums:{}}).premiums[code];}
$("findings").innerHTML=`
<p><b>Parity is won for major languages, lost for the long tail.</b> The fairest tokenizer, <b>${best.name}</b> (${best.lab}), has a median premium of just <b>${best.median.toFixed(2)}×</b> and keeps ${best.share2x.toFixed(0)}% of languages within 2× of English — yet its worst language still costs <b>${best.max.toFixed(1)}×</b>. Every tokenizer's <code>p90</code> stays far above its median: the pain is concentrated in low-resource scripts.</p>
<p><b>The gap roughly halved since 2023.</b> GPT-4's <code>cl100k</code> baseline had a median premium of ${base.median.toFixed(2)}×; today's best sits near ${best.median.toFixed(2)}×. Chinese-lab tokenizers put Chinese at or below English cost.</p>
<p><b>Script data availability decides who gets rescued.</b> Burmese improved sharply across the board, while Shan and Dzongkha (${prem(best.name,'shn_Mymr')?prem(best.name,'shn_Mymr').toFixed(1):'—'}× and ${prem(best.name,'dzo_Tibt')?prem(best.name,'dzo_Tibt').toFixed(1):'—'}× even on the best tokenizer) remain stranded.</p>`;
</script>
</body>
</html>"""

html = HTML.replace("__DATA__", payload).replace("__DATE__", DATE)
open("index.html", "w", encoding="utf-8").write(html)
print(f"wrote index.html ({len(html)//1024} KB)")
