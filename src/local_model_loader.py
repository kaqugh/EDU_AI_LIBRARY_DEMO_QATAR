
import os
from gpt4all import GPT4All

MODELS_DIR = os.path.join(os.path.expanduser("~"), "Edu_AI_Library", "models")
os.makedirs(MODELS_DIR, exist_ok=True)

MODEL_NAME = "mistral-7b-instruct.Q4_0.gguf"

_model = None
def get_model():
    global _model
    if _model is None:
        _model = GPT4All(model_name=MODEL_NAME, model_path=MODELS_DIR)
    return _model

def local_generate(prompt: str, max_tokens: int = 220, temp: float = 0.2) -> str:
    model = get_model()
    return model.generate(prompt, max_tokens=max_tokens, temp=temp).strip()
