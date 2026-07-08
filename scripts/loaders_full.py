#!/usr/bin/env python3
"""完整 tokenizer 集合(2026 排行榜 + 2023 基线)。
每个 maker() 返回 (count_fn, vocab_size);count_fn(list[str]) -> token 总数。"""
import os, base64
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
import tiktoken
from huggingface_hub import hf_hub_download
from tokenizers import Tokenizer

def tt(name):
    enc = tiktoken.get_encoding(name)
    return (lambda ss: sum(len(x) for x in enc.encode_ordinary_batch(ss)), enc.n_vocab)

def hf_json(repo):
    tok = Tokenizer.from_file(hf_hub_download(repo, "tokenizer.json"))
    return (lambda ss: sum(len(e.ids) for e in tok.encode_batch(ss, add_special_tokens=False)),
            tok.get_vocab_size())

# .model 文件自动判别:tiktoken 文本格式(base64 rank/行) vs SentencePiece 二进制
def smart_model(repo, fname, pat="o200k_base"):
    path = hf_hub_download(repo, fname)
    with open(path, "rb") as f:
        head = f.read(256)
    is_text = all(c in (9, 10, 13) or 32 <= c < 127 for c in head)
    if is_text:
        ranks = {}
        with open(path) as f:
            for line in f:
                parts = line.split()
                if len(parts) == 2:
                    try:
                        ranks[base64.b64decode(parts[0])] = int(parts[1])
                    except Exception:
                        pass
        if len(ranks) > 1000:
            enc = tiktoken.Encoding(name=fname, pat_str=tiktoken.get_encoding(pat)._pat_str,
                                    mergeable_ranks=ranks, special_tokens={})
            return (lambda ss: sum(len(enc.encode_ordinary(s)) for s in ss), len(ranks))
    import sentencepiece as spm
    sp = spm.SentencePieceProcessor(); sp.Load(path)
    return (lambda ss: sum(len(x) for x in sp.EncodeAsIds(ss)), sp.GetPieceSize())

# (显示名, 机构, 发布, 是否算入 2026 排行榜, maker)
SPECS = [
    ("GPT-4 (cl100k)",    "OpenAI",    "2023-03", False, lambda: tt("cl100k_base")),
    ("GPT-4o (o200k)",    "OpenAI",    "2024-05", True,  lambda: tt("o200k_base")),
    ("DeepSeek-V4",       "DeepSeek",  "2026-06", True,  lambda: hf_json("deepseek-ai/DeepSeek-V4-Pro-DSpark")),
    ("GLM-5.2",           "Zhipu AI",  "2026-06", True,  lambda: hf_json("zai-org/GLM-5.2")),
    ("Qwen3.5",           "Alibaba",   "2026",    True,  lambda: hf_json("Qwen/Qwen3.5-9B")),
    ("Seed-OSS (Doubao)", "ByteDance", "2025-08", True,  lambda: hf_json("ByteDance-Seed/Seed-OSS-36B-Instruct")),
    ("Llama-4",           "Meta",      "2025-04", True,  lambda: smart_model("unsloth/Llama-4-Scout-17B-16E-Instruct", "tokenizer.model")),
    ("Mistral-Small-3",   "Mistral AI","2025-01", True,  lambda: hf_json("unsloth/Mistral-Small-24B-Instruct-2501")),
    ("Gemma-3",           "Google",    "2025-03", True,  lambda: smart_model("unsloth/gemma-3-27b-it", "tokenizer.model")),
    ("Kimi-K2.6",         "Moonshot",  "2026-04", True,  lambda: smart_model("moonshotai/Kimi-K2.6", "tiktoken.model")),
]

if __name__ == "__main__":
    test = ["The quick brown fox.", "快速的棕色狐狸。", "الثعلب البني السريع.", "빠른 갈색 여우."]
    for name, lab, era, rank, mk in SPECS:
        try:
            fn, vocab = mk()
            print(f"  ✓ {name:<18}{lab:<11}vocab={vocab:>7}  en/zh/ar/ko={[fn([t]) for t in test]}")
        except Exception as e:
            print(f"  ✗ {name:<18}{type(e).__name__}: {str(e)[:60]}")
