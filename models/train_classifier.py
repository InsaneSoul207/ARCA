

import os, sys, json, pickle, random, math
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader, random_split
from sklearn.preprocessing import LabelEncoder
import nltk
from nltk.tokenize import word_tokenize

nltk.download("punkt",     quiet=True)
nltk.download("punkt_tab", quiet=True)

from config import (MAX_SEQUENCE_LEN, EMBEDDING_DIM, HIDDEN_DIM,
                    EPOCHS, LEARNING_RATE, MODEL_PATH, INTENTS_JSON)

random.seed(42)
torch.manual_seed(42)

# 
# Synonym table for augmentation
# 
SYNONYMS = {
    "oen":     ["launch", "start", "run", "bring u", "load"],
    "launch":   ["oen", "start", "run", "fire u"],
    "start":    ["oen", "launch", "begin", "initiate"],
    "check":    ["show", "dislay", "get", "reort", "tell me"],
    "show":     ["dislay", "list", "give me", "tell me"],
    "get":      ["fetch", "retrieve", "obtain", "ull u"],
    "tell":     ["show", "give", "reort"],
    "increase": ["raise", "boost", "turn u", "crank u"],
    "decrease": ["lower", "reduce", "turn down", "dro"],
    "search":   ["look u", "find", "google", "query"],
    "find":     ["search for", "look u", "locate", "discover"],
    "send":     ["write", "comose", "draft", "shoot"],
    "write":    ["comose", "draft", "create", "tye"],
    "set":      ["create", "add", "schedule", "configure"],
    "delete":   ["remove", "erase", "wie", "clear"],
    "clear":    ["delete", "erase", "wie", "remove"],
    "take":     ["cature", "grab", "sna"],
    "create":   ["make", "new", "generate", "roduce"],
    "what":     ["whats", "show me the", "give me the"],
    "how":      ["what is the", "tell me the"],
    "my":       ["the", "current"],
    "lease":   ["now", ""],
    "the":      ["my", ""],
}

# ─────────────────────────────────────────────────────────────────────────────
# Data loading + augmentation
# ─────────────────────────────────────────────────────────────────────────────
def load_intent_data() -> dict:
    with open(INTENTS_JSON, "r", encoding="utf-8") as f:
        return json.load(f)

def augment_sentence(sentence: str, n_aug: int = 2) -> list[str]:
    tokens = sentence.split()
    results = []
    for _ in range(n_aug):
        aug = tokens[:]
        method = random.choice(["dropout", "synonym"])
        if method == "dropout" and len(aug) > 3:
            idx = random.randint(1, len(aug) - 1)
            aug.pop(idx)
        elif method == "synonym":
            candidates = [(i, t) for i, t in enumerate(aug)
                          if t.lower() in SYNONYMS]
            if candidates:
                idx, token = random.choice(candidates)
                replacement = random.choice(SYNONYMS[token.lower()])
                if replacement:   
                    aug[idx] = replacement
                else:
                    aug.pop(idx)
        result = " ".join(aug).strip()
        if result and result != sentence and len(result.split()) >= 1:
            results.append(result)
    return results

def build_training_data(data: dict, augment: bool = True):
    sentences, labels = [], []
    for intent, phrases in data.items():
        for phrase in phrases:
            sentences.append(phrase)
            labels.append(intent)
            if augment:
                n = 4 if len(phrase.split()) <= 3 else 2
                for aug in augment_sentence(phrase, n_aug=n):
                    sentences.append(aug)
                    labels.append(intent)
    return sentences, labels

# ─────────────────────────────────────────────────────────────────────────────
# Vocabulary & Dataset
# ─────────────────────────────────────────────────────────────────────────────
def build_vocab(sentences: list[str]) -> dict:
    vocab = {"<PAD>": 0, "<UNK>": 1}
    for s in sentences:
        for tok in word_tokenize(s.lower()):
            if tok not in vocab:
                vocab[tok] = len(vocab)
    return vocab

def encode(sentence: str, vocab: dict, max_len: int) -> list[int]:
    ids  = [vocab.get(t, 1) for t in word_tokenize(sentence.lower())][:max_len]
    ids += [0] * (max_len - len(ids))
    return ids

class IntentDataset(Dataset):
    def __init__(self, X, y):
        self.X = torch.tensor(X, dtype=torch.long)
        self.y = torch.tensor(y, dtype=torch.long)
    def __len__(self): return len(self.X)
    def __getitem__(self, i): return self.X[i], self.y[i]

# ─────────────────────────────────────────────────────────────────────────────
# Model  —  BiLSTM + Self-Attention
# ─────────────────────────────────────────────────────────────────────────────
class SelfAttention(nn.Module):
    def __init__(self, hidden_dim: int):
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
    # 🚨 UPDATED: Base dropout increased from 0.4 to 0.5
    def __init__(self, vocab_size: int, embed_dim: int,
                 hidden_dim: int, num_classes: int, dropout: float = 0.5):
        super().__init__()
        self.embed = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
        
        # 🚨 UPDATED: LSTM dropout increased to 0.5
        self.lstm = nn.LSTM(
            input_size=embed_dim,
            hidden_size=hidden_dim,
            num_layers=2,
            batch_first=True,
            bidirectional=True,
            dropout=0.5, 
        )

        bilstm_out = hidden_dim * 2   
        self.attention  = SelfAttention(bilstm_out)
        self.layer_norm = nn.LayerNorm(bilstm_out)
        self.residual_proj = nn.Linear(bilstm_out + bilstm_out, bilstm_out)

        self.drop = nn.Dropout(dropout)
        self.fc1  = nn.Linear(bilstm_out, hidden_dim)
        self.fc2  = nn.Linear(hidden_dim, num_classes)
        self.act  = nn.GELU()

    def forward(self, x):
        mask = (x != 0).float()                        
        emb = self.embed(x)                            
        lstm_out, (h, _) = self.lstm(emb)              
        ctx, _ = self.attention(lstm_out, mask)        
        
        fwd = h[-2]   
        bwd = h[-1]   
        last_h = torch.cat([fwd, bwd], dim=1)          
        
        combined = torch.cat([ctx, last_h], dim=1)     
        fused = self.act(self.residual_proj(combined))  
        fused = self.layer_norm(fused)

        out = self.drop(fused)
        out = self.act(self.fc1(out))
        out = self.drop(out)
        return self.fc2(out)

# ─────────────────────────────────────────────────────────────────────────────
# Focal Loss & Scheduler
# ─────────────────────────────────────────────────────────────────────────────
class FocalLoss(nn.Module):
    def __init__(self, gamma: float = 2.0, label_smoothing: float = 0.05):
        super().__init__()
        self.gamma           = gamma
        self.label_smoothing = label_smoothing

    def forward(self, logits, targets):
        ce_loss = F.cross_entropy(logits, targets, label_smoothing=self.label_smoothing, reduction="none")
        pt      = torch.exp(-ce_loss)
        focal   = ((1 - pt) ** self.gamma) * ce_loss
        return focal.mean()

class WarmupCosineScheduler:
    def __init__(self, optimizer, warmup_epochs: int,
                 total_epochs: int, base_lr: float, min_lr: float = 1e-5):
        self.opt           = optimizer
        self.warmup        = warmup_epochs
        self.total         = total_epochs
        self.base_lr       = base_lr
        self.min_lr        = min_lr
        self._epoch        = 0

    def step(self):
        self._epoch += 1
        e = self._epoch
        if e <= self.warmup:
            lr = self.base_lr * (e / self.warmup)
        else:
            progress = (e - self.warmup) / (self.total - self.warmup)
            lr = self.min_lr + 0.5 * (self.base_lr - self.min_lr) * (1 + math.cos(math.pi * progress))
        for pg in self.opt.param_groups:
            pg["lr"] = lr
        return lr

# ─────────────────────────────────────────────────────────────────────────────
# Training routine
# ─────────────────────────────────────────────────────────────────────────────
def train(progress_cb=None):
    data = load_intent_data()
    sentences, labels = build_training_data(data, augment=True)
    
    print(f"[Train] {len(set(labels))} intents  |  "
          f"{len(data[list(data.keys())[0]])*len(data)} base phrases  |  "
          f"{len(sentences)} after augmentation")

    le    = LabelEncoder()
    y_all = le.fit_transform(labels)
    vocab = build_vocab(sentences)
    X_all = [encode(s, vocab, MAX_SEQUENCE_LEN) for s in sentences]

    dataset = IntentDataset(X_all, y_all)
    n_val   = max(1, int(len(dataset) * 0.10))
    n_train = len(dataset) - n_val
    train_ds, val_ds = random_split(
        dataset, [n_train, n_val],
        generator=torch.Generator().manual_seed(42)
    )

    train_loader = DataLoader(train_ds, batch_size=64, shuffle=True,  drop_last=False)
    val_loader   = DataLoader(val_ds,   batch_size=64, shuffle=False, drop_last=False)

    num_classes = len(le.classes_)
    model       = BiLSTMAttentionClassifier(
        vocab_size  = len(vocab),
        embed_dim   = EMBEDDING_DIM,
        hidden_dim  = HIDDEN_DIM,
        num_classes = num_classes,
        dropout     = 0.5, 
    )

    total_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"[Train] Model: BiLSTM+Attention  |  params={total_params:,}  |  vocab={len(vocab):,}  |  classes={num_classes}")

    opt   = torch.optim.AdamW(model.parameters(), lr=LEARNING_RATE, weight_decay=1e-3)
    loss_fn = FocalLoss(gamma=2.0, label_smoothing=0.05)
    sched   = WarmupCosineScheduler(opt, warmup_epochs=10, total_epochs=EPOCHS, base_lr=LEARNING_RATE, min_lr=1e-5)

    best_val_loss  = float("inf")
    best_state     = None
    
    patience       = 8         
    min_delta      = 0.001     
    no_improve     = 0

    for epoch in range(EPOCHS):
        model.train()
        train_loss = 0.0
        for xb, yb in train_loader:
            opt.zero_grad()
            loss = loss_fn(model(xb), yb)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            train_loss += loss.item()
        train_loss /= len(train_loader)
        lr = sched.step()

        model.eval()
        val_loss = 0.0
        correct  = 0
        total    = 0
        with torch.no_grad():
            for xb, yb in val_loader:
                logits   = model(xb)
                val_loss += loss_fn(logits, yb).item()
                preds     = logits.argmax(dim=1)
                correct  += (preds == yb).sum().item()
                total    += len(yb)
        val_loss /= len(val_loader)
        val_acc   = correct / total if total else 0

        # 🚨 UPDATED: Only reset patience if the improvement beats min_delta
        if val_loss < best_val_loss - min_delta:
            best_val_loss = val_loss
            best_state    = {k: v.clone() for k, v in model.state_dict().items()}
            no_improve    = 0
        else:
            no_improve += 1

        if progress_cb:
            progress_cb(epoch + 1, EPOCHS, train_loss, val_loss)
        elif (epoch + 1) % 10 == 0 or no_improve == 0:
            print(f"  epoch {epoch+1:>3}/{EPOCHS}  "
                  f"train={train_loss:.4f}  val={val_loss:.4f}  "
                  f"val_acc={val_acc:.1%}  lr={lr:.6f}"
                  + ("  ✓ best" if no_improve == 0 else ""))

        if no_improve >= patience:
            print(f"\n[Train] Early stopping triggered at epoch {epoch+1} (Loss plateaued).")
            break

    model.load_state_dict(best_state)
    model.eval()

    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    with open(MODEL_PATH, "wb") as f:
        pickle.dump({
            "model_state": model.state_dict(),
            "vocab":       vocab,
            "vocab_size":  len(vocab),
            "le":          le,
            "arch":        "bilstm_attention_v2",
        }, f)

    print(f"[Train] ✓ Saved → {MODEL_PATH}  (best val_loss={best_val_loss:.4f})")
    return model, vocab, le

if __name__ == "__main__":
    train()