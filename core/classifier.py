import os, sys, pickle
import torch
import torch.nn as nn
import torch.nn.functional as F
import nltk
from nltk.tokenize import word_tokenize

nltk.download("punkt",     quiet=True)
nltk.download("punkt_tab", quiet=True)

from config import MODEL_PATH, MAX_SEQUENCE_LEN, EMBEDDING_DIM, HIDDEN_DIM
from core.logger import log


# ─────────────────────────────────────────────────────────────────────────────
# Model definition — must match train_classifier.py exactly
# ─────────────────────────────────────────────────────────────────────────────

class SelfAttention(nn.Module):
    def __init__(self, hidden_dim):
        super().__init__()
        self.attn = nn.Linear(hidden_dim, 1)

    def forward(self, lstm_out, mask=None):
        scores = self.attn(lstm_out).squeeze(-1)
        if mask is not None:
            scores = scores.masked_fill(mask == 0, -1e9)
        weights = torch.softmax(scores, dim=1)
        context = (weights.unsqueeze(-1) * lstm_out).sum(dim=1)
        return context, weights


class BiLSTMAttentionClassifier(nn.Module):
    def __init__(self, vocab_size, embed_dim, hidden_dim, num_classes, dropout=0.4):
        super().__init__()
        self.embed = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
        self.lstm  = nn.LSTM(
            input_size=embed_dim, hidden_size=hidden_dim,
            num_layers=2, batch_first=True,
            bidirectional=True, dropout=0.35,
        )
        bilstm_out          = hidden_dim * 2
        self.attention      = SelfAttention(bilstm_out)
        self.layer_norm     = nn.LayerNorm(bilstm_out)
        self.residual_proj  = nn.Linear(bilstm_out + bilstm_out, bilstm_out)
        self.drop           = nn.Dropout(dropout)
        self.fc1            = nn.Linear(bilstm_out, hidden_dim)
        self.fc2            = nn.Linear(hidden_dim, num_classes)
        self.act            = nn.GELU()

    def forward(self, x):
        mask = (x != 0).float()
        emb  = self.embed(x)
        lstm_out, (h, _) = self.lstm(emb)
        ctx, _ = self.attention(lstm_out, mask)
        fwd    = h[-2]; bwd = h[-1]
        last_h = torch.cat([fwd, bwd], dim=1)
        combined = torch.cat([ctx, last_h], dim=1)
        fused    = self.act(self.residual_proj(combined))
        fused    = self.layer_norm(fused)
        out      = self.drop(fused)
        out      = self.act(self.fc1(out))
        out      = self.drop(out)
        return self.fc2(out)


# ─────────────────────────────────────────────────────────────────────────────
# Classifier wrapper
# ─────────────────────────────────────────────────────────────────────────────

class IntentClassifier:
    def __init__(self):
        self.model = self.vocab = self.le = None
        self._load()

    def _load(self):
        if not os.path.exists("models\intent_model.pkl"):
            log("No model found — triggering auto-train", "WARN")
            self._train_fresh()
            return
        with open("models\intent_model.pkl", "rb") as f:
            data = pickle.load(f)

        arch = data.get("arch", "lstm_v1")
        self.vocab = data["vocab"]
        self.le    = data["le"]
        n          = len(self.le.classes_)

        if arch == "bilstm_attention_v2":
            self.model = BiLSTMAttentionClassifier(
                data["vocab_size"], EMBEDDING_DIM, HIDDEN_DIM, n)
        else:
            # Legacy v1 model — auto-retrain with new architecture
            log("Old model architecture detected — retraining with BiLSTM+Attention", "WARN")
            self._train_fresh()
            return

        self.model.load_state_dict(data["model_state"])
        self.model.eval()
        log(f"BiLSTM+Attention classifier loaded — {n} intents")

    def _train_fresh(self):
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
        from models.train_classifier import train
        self.model, self.vocab, self.le = train()
        self.model.eval()

    def _encode(self, text: str):
        tokens = word_tokenize(text.lower())
        ids    = [self.vocab.get(t, 1) for t in tokens][:MAX_SEQUENCE_LEN]
        ids   += [0] * (MAX_SEQUENCE_LEN - len(ids))
        return torch.tensor([ids], dtype=torch.long)

    def predict(self, text: str) -> tuple[str, float]:
        if self.model is None:
            return "unknown", 0.0
        with torch.no_grad():
            logits = self.model(self._encode(text))
            probs  = torch.softmax(logits, dim=1)
            conf, idx = probs.max(dim=1)
        intent     = self.le.inverse_transform([idx.item()])[0]
        confidence = conf.item()
        log(f'Classified → "{intent}" ({confidence:.0%})')
        return intent, confidence

    def predict_top3(self, text: str) -> list[tuple[str, float]]:
        """Return top-3 intents with confidences — useful for debugging."""
        if self.model is None:
            return [("unknown", 0.0)]
        with torch.no_grad():
            logits = self.model(self._encode(text))
            probs  = torch.softmax(logits, dim=1)[0]
        top3   = probs.topk(3)
        return [(self.le.inverse_transform([i.item()])[0], p.item())
                for p, i in zip(top3.values, top3.indices)]