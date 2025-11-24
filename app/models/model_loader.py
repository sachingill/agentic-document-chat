from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

class ModelLoader:
    model = None
    tokenizer = None


    # The following decorator defines a class method, meaning that the method 'load'
    # will receive the class itself ('cls') as the first argument instead of an instance.
    # This allows the method to manage state (model, tokenizer) at the class level and
    # implement a singleton-like pattern for loading and sharing the model and tokenizer.
    @classmethod
    def load(cls):
        if cls.model is None:
            print("Loading model...")
            model_name = "distilbert-base-uncased-finetuned-sst-2-english"

            cls.tokenizer = AutoTokenizer.from_pretrained(model_name)
            cls.model = AutoModelForSequenceClassification.from_pretrained(model_name)
            cls.model.eval()
        return cls.model, cls.tokenizer