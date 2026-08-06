"""Translation Service for Japanese to Vietnamese."""
import time
from typing import Optional, Dict
from app.core.config import config
from app.utils.logger import log_error, log_warning

class TranslationService:
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.is_loaded = False
        self._init_fallback_dict()

    def _init_fallback_dict(self):
        """Seed dictionary for common Japanese conversational phrases."""
        self.dict_ja_vi: Dict[str, str] = {
            "こんにちは": "Xin chào",
            "おはようございます": "Chào buổi sáng",
            "こんばんは": "Chào buổi tối",
            "ありがとうございます": "Cảm ơn bạn rất nhiều",
            "ありがとう": "Cảm ơn",
            "すみません": "Xin lỗi / Cho tôi hỏi",
            "ごめんなさい": "Tôi xin lỗi",
            "はい": "Vâng / Có",
            "いいえ": "Không",
            "さようなら": "Tạm biệt",
            "お元気ですか": "Bạn có khỏe không?",
            "はじめまして": "Rất hân hạnh được gặp bạn",
            "よろしくお願いします": "Rất mong được giúp đỡ / Rất hân hạnh",
            "分かりました": "Tôi hiểu rồi",
            "分かりません": "Tôi không hiểu",
            "大丈夫です": "Không sao đâu / Ổn rồi",
            "何ですか": "Cái gì vậy?",
            "助けて": "Cứu tôi với",
            "日本": "Nhật Bản",
            "ベトナム": "Việt Nam",
            "リアルタイム翻訳": "Dịch thuật theo thời gian thực",
        }

    def load_model(self):
        """Lazy load Helsinki-NLP/opus-mt-ja-vi or PyTorch model."""
        if self.is_loaded:
            return True
        try:
            from transformers import MarianMTModel, MarianTokenizer
            model_name = config.mt_model_name
            self.tokenizer = MarianTokenizer.from_pretrained(model_name)
            self.model = MarianMTModel.from_pretrained(model_name)
            if config.mt_device == "mps":
                import torch
                if torch.backends.mps.is_available():
                    self.model.to("mps")
            self.is_loaded = True
            return True
        except Exception as e:
            log_warning(f"Could not load HuggingFace MT model '{config.mt_model_name}': {e}. Using fallback translator.")
            self.is_loaded = False
            return False

    def translate(self, text: str) -> str:
        """Translate Japanese text to Vietnamese."""
        text = text.strip()
        if not text:
            return ""

        # Check fallback dictionary for exact match
        if text in self.dict_ja_vi:
            return self.dict_ja_vi[text]

        # Try Hugging Face MarianMT if available or loadable
        if not self.is_loaded:
            self.load_model()

        if self.is_loaded and self.model and self.tokenizer:
            try:
                inputs = self.tokenizer(text, return_tensors="pt", padding=True)
                if config.mt_device == "mps":
                    inputs = {k: v.to("mps") for k, v in inputs.items()}
                translated = self.model.generate(**inputs)
                result = self.tokenizer.decode(translated[0], skip_special_tokens=True)
                return result.strip()
            except Exception as e:
                log_error(f"MarianMT translate error for '{text}': {e}")

        # Heuristic fallback matching for demo / dev when offline
        translated_parts = []
        words = text.split()
        for w in words:
            translated_parts.append(self.dict_ja_vi.get(w, w))
            
        res = " ".join(translated_parts)
        if res == text:
            # Add prefix indicator if phrase wasn't in dictionary and model not loaded yet
            return f"[Dịch: {text}]"
        return res

translation_service = TranslationService()
