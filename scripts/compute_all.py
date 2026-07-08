#!/usr/bin/env python3
"""对全部 200 种 FLORES-200 语言、全部 tokenizer 计算 premium,产出排行榜 JSON。
premium(lang) = Σtokens(lang devtest) / Σtokens(English)。"""
import os, glob, json
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
from loaders_full import SPECS

FL = "flores200_dataset/devtest"
files = sorted(glob.glob(os.path.join(FL, "*.devtest")))
codes = [os.path.basename(f).replace(".devtest", "") for f in files]
assert "eng_Latn" in codes

def load(code):
    with open(os.path.join(FL, code + ".devtest"), encoding="utf-8") as f:
        return [ln.rstrip("\n") for ln in f]

sents = {c: load(c) for c in codes}
n_sent = len(sents["eng_Latn"])
codes = [c for c in codes if len(sents[c]) == n_sent]   # 只保留对齐的
print(f"{len(codes)} 语言 × {n_sent} 句")

NAMES = {
 "eng_Latn":"English","fra_Latn":"French","spa_Latn":"Spanish","deu_Latn":"German","ita_Latn":"Italian",
 "por_Latn":"Portuguese","nld_Latn":"Dutch","swe_Latn":"Swedish","dan_Latn":"Danish","nob_Latn":"Norwegian",
 "fin_Latn":"Finnish","isl_Latn":"Icelandic","rus_Cyrl":"Russian","ukr_Cyrl":"Ukrainian","pol_Latn":"Polish",
 "ces_Latn":"Czech","slk_Latn":"Slovak","ron_Latn":"Romanian","bul_Cyrl":"Bulgarian","srp_Cyrl":"Serbian",
 "hrv_Latn":"Croatian","slv_Latn":"Slovenian","ell_Grek":"Greek","hun_Latn":"Hungarian","est_Latn":"Estonian",
 "lvs_Latn":"Latvian","lit_Latn":"Lithuanian","tur_Latn":"Turkish","azj_Latn":"Azerbaijani","kaz_Cyrl":"Kazakh",
 "uzn_Latn":"Uzbek","arb_Arab":"Arabic (MSA)","arz_Arab":"Egyptian Arabic","heb_Hebr":"Hebrew","pes_Arab":"Persian",
 "urd_Arab":"Urdu","pbt_Arab":"Pashto","ckb_Arab":"Kurdish (Sorani)","hin_Deva":"Hindi","ben_Beng":"Bengali",
 "tam_Taml":"Tamil","tel_Telu":"Telugu","kan_Knda":"Kannada","mal_Mlym":"Malayalam","mar_Deva":"Marathi",
 "guj_Gujr":"Gujarati","pan_Guru":"Punjabi","ory_Orya":"Odia","asm_Beng":"Assamese","sin_Sinh":"Sinhala",
 "npi_Deva":"Nepali","zho_Hans":"Chinese (Simpl.)","zho_Hant":"Chinese (Trad.)","yue_Hant":"Cantonese",
 "jpn_Jpan":"Japanese","kor_Hang":"Korean","vie_Latn":"Vietnamese","tha_Thai":"Thai","ind_Latn":"Indonesian",
 "zsm_Latn":"Malay","tgl_Latn":"Tagalog","ceb_Latn":"Cebuano","jav_Latn":"Javanese","sun_Latn":"Sundanese",
 "mya_Mymr":"Burmese","khm_Khmr":"Khmer","lao_Laoo":"Lao","shn_Mymr":"Shan","dzo_Tibt":"Dzongkha",
 "bod_Tibt":"Tibetan","amh_Ethi":"Amharic","tir_Ethi":"Tigrinya","som_Latn":"Somali","swh_Latn":"Swahili",
 "yor_Latn":"Yoruba","ibo_Latn":"Igbo","hau_Latn":"Hausa","zul_Latn":"Zulu","xho_Latn":"Xhosa",
 "sna_Latn":"Shona","nso_Latn":"Sepedi","afr_Latn":"Afrikaans","lug_Latn":"Ganda","kin_Latn":"Kinyarwanda",
 "mlg_Latn":"Malagasy","cat_Latn":"Catalan","eus_Latn":"Basque","glg_Latn":"Galician","cym_Latn":"Welsh",
 "gle_Latn":"Irish","mlt_Latn":"Maltese","kat_Geor":"Georgian","hye_Armn":"Armenian","mon_Cyrl":"Mongolian",
 "khk_Cyrl":"Mongolian","tgk_Cyrl":"Tajik","kir_Cyrl":"Kyrgyz","bel_Cyrl":"Belarusian","mkd_Cyrl":"Macedonian",
 "sqi_Latn":"Albanian","bak_Cyrl":"Bashkir","tat_Cyrl":"Tatar","san_Deva":"Sanskrit","lij_Latn":"Ligurian",
}

def pct(sorted_vals, p):
    if not sorted_vals: return 0.0
    k = (len(sorted_vals) - 1) * p
    lo = int(k); hi = min(lo + 1, len(sorted_vals) - 1)
    return sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * (k - lo)

toks_out = []
for name, lab, era, rank, mk in SPECS:
    try:
        fn, vocab = mk()
    except Exception as e:
        print(f"  ⊘ {name:<18} skipped ({type(e).__name__}: {str(e)[:40]}) — not downloaded yet")
        continue
    eng = fn(sents["eng_Latn"])
    prem = {c: round(fn(sents[c]) / eng, 3) for c in codes}
    vals = sorted(v for c, v in prem.items() if c != "eng_Latn")
    share2 = round(100 * sum(1 for v in vals if v <= 2.0) / len(vals), 1)
    toks_out.append({
        "name": name, "lab": lab, "era": era, "rank": rank, "vocab": vocab,
        "median": round(pct(vals, 0.5), 3), "mean": round(sum(vals) / len(vals), 3),
        "p90": round(pct(vals, 0.9), 3), "max": round(vals[-1], 3), "share2x": share2,
        "premiums": prem,
    })
    print(f"  ✓ {name:<18} median={toks_out[-1]['median']:.2f} mean={toks_out[-1]['mean']:.2f} "
          f"p90={toks_out[-1]['p90']:.2f} ≤2x={share2:.0f}%")

out = {"n_langs": len(codes), "n_sent": n_sent, "codes": codes,
       "names": {c: NAMES.get(c, c) for c in codes}, "tokenizers": toks_out}
json.dump(out, open("results_all.json", "w"), ensure_ascii=False)
print("\n写出 results_all.json")
print("\n2026 排行榜(按 median premium 升序,越低越公平):")
for t in sorted([t for t in toks_out if t["rank"]], key=lambda t: t["median"]):
    print(f"  {t['name']:<18}{t['lab']:<11} median={t['median']:.2f}  mean={t['mean']:.2f}  ≤2x={t['share2x']:.0f}%")
