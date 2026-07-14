"""Helper for loading the seq2seq generation model and tokenizer."""
from __future__ import annotations

from transformers import AutoModelForSeq2SeqLM, AutoTokenizer


class ModelLoader:
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.model = None
        self.tokenizer = None

    def load_model(self):
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name)
        self.model.eval()
        return self.model, self.tokenizer

    def get_model(self):
        return self.model

    def get_tokenizer(self):
        return self.tokenizer
