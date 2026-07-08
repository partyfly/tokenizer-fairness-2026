#!/usr/bin/env python3
"""复现 Petrov et al. (2023) "Language Model Tokenizers Introduce Unfairness
Between Languages" (NeurIPS 2023, arXiv:2305.15425) 的两个最具代表性实验,
并扩展到 2026 年的分词器,回答"不公平性有没有随新分词器缩小"。

实验 1 (论文 Table 1): 子词分词器的 language premium
    premium(L) = Σ tokens(L 的 devtest) / Σ tokens(英文 devtest)
    premium≈1 公平;越大越吃亏。论文用 ChatGPT/GPT-4 的 cl100k,Shan 高达 15×。

实验 2 (论文 Table 5): 字节级模型也不公平
    ByT5  premium(L) = Σ len(utf-8 bytes) / 英文       (UTF-8)
    CANINE premium(L) = Σ len(unicode 码点) / 英文       (UTF-32)
    不需要任何模型,纯计算即可。

数据: FLORES-200 devtest,1012 句/语言,逐行对齐。
获取方式(二选一,见下方 load_flores):
  A) 有 HuggingFace token: huggingface-cli login,然后用 facebook/flores(gated,
     token 免费,秒级下载)。
  B) 无 token: 下载原始 tarball(慢,但不需要账号):
     curl -L -o flores.tgz https://dl.fbaipublicfiles.com/nllb/flores200_dataset.tar.gz
     tar xzf flores.tgz   # 得到 flores200_dataset/devtest/{code}.devtest
"""
import os, glob, sys
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
import tiktoken
from huggingface_hub import hf_hub_download
from tokenizers import Tokenizer

# 语言名, FLORES-200 代码, 论文 Table 1 中 cl100k(ChatGPT/GPT-4)的 premium(校验基准)
LANGS = [
    ("English",        "eng_Latn",  1.00),
    ("Portuguese",     "por_Latn",  1.48),
    ("Spanish",        "spa_Latn",  1.55),
    ("German",         "deu_Latn",  1.58),
    ("French",         "fra_Latn",  1.60),
    ("Italian",        "ita_Latn",  1.64),
    ("Chinese (Simp)", "zho_Hans",  1.91),
    ("Japanese",       "jpn_Jpan",  2.30),
    ("Vietnamese",     "vie_Latn",  2.45),
    ("Bulgarian",      "bul_Cyrl",  2.64),
    ("Burmese",        "mya_Mymr", 11.70),
    ("Dzongkha",       "dzo_Tibt", 12.33),
    ("Shan",           "shn_Mymr", 15.05),
]

# ---- 数据加载:优先本地 tarball 目录,其次用 HF token ----
def load_flores():
    # A) 本地已解压的 tarball
    for base in ("flores200_dataset", "flores", "."):
        d = os.path.join(base, "devtest")
        if glob.glob(os.path.join(d, "eng_Latn*")):
            def rd(code):
                with open(glob.glob(os.path.join(d, code + "*"))[0], encoding="utf-8") as f:
                    return [ln.rstrip("\n") for ln in f]
            return {n: rd(c) for n, c, _ in LANGS}, f"本地 {d}"
    # B) HF token(facebook/flores 为 gated,需 huggingface-cli login)
    if os.environ.get("HF_TOKEN") or os.path.exists(os.path.expanduser("~/.cache/huggingface/token")):
        import pyarrow.parquet as pq  # 需 pip install pyarrow
        def rd(code):
            p = hf_hub_download("facebook/flores",
                                f"data/language/{code}/devtest-00000-of-00001.parquet",
                                repo_type="dataset")
            return pq.read_table(p).column("text").to_pylist()
        return {n: rd(c) for n, c, _ in LANGS}, "HF facebook/flores"
    sys.exit("找不到数据。请解压 FLORES tarball,或 huggingface-cli login 后重跑。")

sents, src = load_flores()
n = len(sents["English"])
for name in sents:
    assert len(sents[name]) == n, f"{name} 未对齐 ({len(sents[name])}≠{n})"
print(f"数据来源: {src} | {n} 句/语言 × {len(LANGS)} 语言\n")

# ---- 实验 1:子词分词器 ----
def tt(enc_name):
    enc = tiktoken.get_encoding(enc_name)
    return lambda ss: sum(len(x) for x in enc.encode_ordinary_batch(ss))
def hf(repo):
    tok = Tokenizer.from_file(hf_hub_download(repo, "tokenizer.json"))
    return lambda ss: sum(len(e.ids) for e in tok.encode_batch(ss, add_special_tokens=False))

SUBWORD = [
    ("cl100k(论文)",  tt("cl100k_base")),        # 复现论文那一列
    ("o200k(GPT-4o)", tt("o200k_base")),         # 新一代 OpenAI
    ("DeepSeek-V4",   hf("deepseek-ai/DeepSeek-V4-Pro-DSpark")),
    ("GLM-5.2",       hf("zai-org/GLM-5.2")),
    # 想加更多就照抄:("Qwen3", hf("Qwen/Qwen3-8B")), ("Llama-3", hf("meta-llama/Llama-3.1-8B")) ...
]

# ---- 实验 2:字节级(无需模型)----
def byt5(ss):   return sum(len(s.encode("utf-8")) for s in ss)   # UTF-8 字节
def canine(ss): return sum(len(s) for s in ss)                    # Unicode 码点(UTF-32)
BYTE = [("ByT5(UTF-8)", byt5), ("CANINE(UTF-32)", canine)]

ALL = SUBWORD + BYTE
totals = {}
for tname, fn in ALL:
    totals[tname] = {name: fn(sents[name]) for name, _, _ in LANGS}
    print(f"  ✓ {tname}")
print()

hdr = f"{'语言':<15}{'论文':>6}" + "".join(f"{t:>15}" for t, _ in ALL)
print(hdr); print("-" * len(hdr))
err = []
for name, code, paper in LANGS:
    row = f"{name:<15}{paper:>6.2f}"
    for tname, _ in ALL:
        prem = totals[tname][name] / totals[tname]["English"]
        row += f"{prem:>15.2f}"
        if tname == "cl100k(论文)" and name != "English":
            err.append(abs(prem - paper))
    print(row)
print("-" * len(hdr))
print(f"\n校验: 复现 cl100k 与论文 Table 1 的平均绝对误差 = {sum(err)/len(err):.3f} (≈0 即成功复现)")
