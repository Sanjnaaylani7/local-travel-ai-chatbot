"""Optionally quantise the seq2seq model to int8 for faster CPU inference.

Usage:
    python quantize.py --model google/flan-t5-small --out ./models/flan-t5-small-int8
"""
from __future__ import annotations

import argparse

import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer


def quantize_model(model_name: str, output_dir: str) -> None:
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
    tokenizer = AutoTokenizer.from_pretrained(model_name)

    quantized = torch.quantization.quantize_dynamic(
        model, {torch.nn.Linear}, dtype=torch.qint8
    )
    quantized.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
    print(f"Saved quantised model -> {output_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="google/flan-t5-small")
    parser.add_argument("--out", default="./models/quantized")
    args = parser.parse_args()
    quantize_model(args.model, args.out)
