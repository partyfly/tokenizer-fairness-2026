# Tokenizer fairness in 2026

**Live page → https://partyfly.github.io/tokenizer-fairness-2026/**

The same sentence costs a different number of tokens in different languages. Because APIs bill per token, context windows are fixed in tokens, and latency scales with tokens, that difference is a real tax: speakers of some languages pay more, wait longer, and fit less context for identical content.

This project **reproduces** the NeurIPS 2023 paper [*Language Model Tokenizers Introduce Unfairness Between Languages*](https://arxiv.org/abs/2305.15425) (Petrov, La Malfa, Torr, Bibi) and **extends** it to 2026-era tokenizers across ten model families and all 200 FLORES-200 languages.

## The metric

For a language *L*, its **premium** is

```
premium(L) = Σ tokens(L devtest) / Σ tokens(English devtest)
```

over the FLORES-200 `devtest` split (1,012 sentences, the same content in every language), counted without special tokens. Premium 1.0 means *L* is as cheap as English; 15 means fifteen times more expensive. Lower is fairer.

## What we find

- **Reproduction holds.** GPT-4's `cl100k` matches the paper's Table 1 to a mean absolute error of **0.038** (Shan 14.98 vs 15.05, Chinese 1.87 vs 1.91).
- **The gap split in two.** Parity is effectively won for the world's major languages (Chinese, Arabic, Korean, Japanese, and European all ≤ ~2× on current tokenizers), but the low-resource tail (Shan, Dzongkha) is still **6–9×** on every tokenizer, old and new.
- **Breadth vs. depth.** Over all 200 languages, OpenAI's large-vocab `o200k` has the lowest *median* premium, while Chinese-lab tokenizers (DeepSeek, GLM, Qwen) win specifically on Chinese (at or below English cost). Different design goals, different winners.
- **Script data availability decides who gets rescued.** Burmese improved sharply everywhere; Shan and Dzongkha, which share less-resourced scripts, did not.

See the [live page](https://partyfly.github.io/tokenizer-fairness-2026/) for the full ranked leaderboard and the per-language table.

## Tokenizers compared

| Lab | 2023 | Latest (2026) |
|---|---|---|
| OpenAI | GPT-4 `cl100k` | GPT-4o `o200k` |
| DeepSeek | `deepseek-llm-7b` | DeepSeek-V4 |
| Zhipu | ChatGLM3 | GLM-5.2 |
| Alibaba | Qwen-7B | Qwen3.5 |
| ByteDance | — | Seed-OSS (Doubao proxy) |
| Meta | — | Llama-4 |
| Mistral | — | Mistral-Small-3 |
| Google | — | Gemma-3 |
| Moonshot | — | Kimi-K2.6 |

## Reproduce

```bash
pip install tiktoken tokenizers huggingface_hub sentencepiece
# get FLORES-200 devtest (the harness auto-detects flores200_dataset/devtest/)
curl -L -o flores.tgz https://dl.fbaipublicfiles.com/nllb/flores200_dataset.tar.gz && tar xzf flores.tgz
python scripts/compute_all.py      # -> results_all.json (premiums, ranking)
python scripts/build_page.py       # -> index.html
```

`scripts/reproduce_tokenization_fairness.py` reproduces the paper's Table 1 + byte-level Table 5 and self-validates against the published numbers.

## Caveats

- **Doubao** is a closed product with no public tokenizer; its column uses ByteDance's open **Seed-OSS** tokenizer as a proxy.
- Gated labs (**Meta**, **Google**) are loaded from ungated mirrors of the *identical* tokenizer.
- **Kimi**'s pre-tokenization regex is approximated; **Mistral-Small-3** stands in for the current tekken tokenizer family.
- The latest OpenAI *public* tokenizer is `o200k` (GPT-4o); newer closed models may differ.

## Credit

A reproduction and extension of Petrov, La Malfa, Torr & Bibi (NeurIPS 2023). Not affiliated with the authors or any model provider. FLORES-200 © Meta AI, CC BY-SA 4.0.
