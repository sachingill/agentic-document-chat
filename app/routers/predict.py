from fastapi import APIRouter
from pydantic import BaseModel
from app.models.model_loader import ModelLoader
import torch

router = APIRouter(prefix="/predict", tags=["Predict"])

class Input(BaseModel):
    text: str



@router.post("/")
async def predict(input: Input):
    model, tokenizer = ModelLoader.load()
    inputs = tokenizer(input.text, return_tensors="pt")
    with torch.no_grad():
        outputs = model(**inputs)
    
    probs = outputs.logits.softmax(dim=1)
    pred = torch.argmax(probs, dim=1)
    
    confidence = probs[0, pred.item()].item()

    label = "positive" if pred.item() == 1 else "negative"
    return {
        "text": input.text,
        "label": label,
        "confidence": round(confidence, 4)
    }