
import os, sys, tkinter as tk

ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from config import MODEL_PATH, BASE_DIR

INTENTS_JSON = os.path.join(BASE_DIR, "models", "intents.json")

def _model_is_stale() -> bool:
    if not os.path.exists(MODEL_PATH):
        return True   
    if not os.path.exists(INTENTS_JSON):
        return False  
    return os.path.getmtime(INTENTS_JSON) > os.path.getmtime(MODEL_PATH)

if _model_is_stale():
    reason = "first run" if not os.path.exists(MODEL_PATH) else "intents.json was updated"
    print(f"[ARCA] Training model ({reason}) — this takes ~60 seconds…")
    print(f"[ARCA] Progress will print every 10 epochs.\n")
    from models.train_classifier import train
    train()
    print()

from ui.app_window import Alpha2App

if __name__ == "__main__":
    root = tk.Tk()
    app  = Alpha2App(root)
    root.mainloop()