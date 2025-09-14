import os
from transformers import AutoTokenizer, AutoModelForSequenceClassification, Trainer, TrainingArguments
import torch
from torch.utils.data import Dataset
import numpy as np

LABEL_LIST = ['Invoice', 'Resume', 'Contract', 'Technical Manual']
LABEL2ID = {label: i for i, label in enumerate(LABEL_LIST)}

class TextDataset(Dataset):
    def __init__(self, texts, labels, tokenizer):
        self.texts = texts
        self.labels = [LABEL2ID[label] for label in labels]
        self.tokenizer = tokenizer

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        encoding = self.tokenizer(self.texts[idx], truncation=True, padding='max_length', max_length=512, return_tensors='pt')
        item = {key: val.squeeze(0) for key, val in encoding.items()}
        item['labels'] = torch.tensor(self.labels[idx])
        return item

def classify_text(text, tokenizer, model):
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=512)
    outputs = model(**inputs)
    logits = outputs.logits
    probabilities = torch.nn.functional.softmax(logits, dim=1)
    pred_label_id = torch.argmax(probabilities).item()
    pred_label = LABEL_LIST[pred_label_id]
    confidence = probabilities[0][pred_label_id].item()
    return pred_label, confidence

def train_new_data(tokenizer, model, texts, labels, output_dir, epochs=3):
    dataset = TextDataset(texts, labels, tokenizer)
    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=epochs,
        per_device_train_batch_size=4,
        logging_steps=10,
        save_strategy="epoch",
        evaluation_strategy="no",
        disable_tqdm=False,
        seed=42
    )
    trainer = Trainer(model=model, args=training_args, train_dataset=dataset)
    trainer.train()
    trainer.save_model(output_dir)
    tokenizer.save_pretrained(output_dir)

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    model_dir = os.path.join(script_dir, '..', 'models', 'finetuned_classifier')

    tokenizer = AutoTokenizer.from_pretrained(model_dir)
    model = AutoModelForSequenceClassification.from_pretrained(model_dir)

    model.train()  # Set model to training mode

    # Example: add new data samples for training
    new_texts = [
        "Sample invoice text here...",
        "New resume text example...",
        "A freshly added contract text.",
        "Updated technical manual content."
    ]
    new_labels = ['Invoice', 'Resume', 'Contract', 'Technical Manual']

    train_new_data(tokenizer, model, new_texts, new_labels, model_dir, epochs=3)

    model.eval()  # Switch back to eval mode for inference

    print("Enter text to classify (or 'quit' to exit):")
    while True:
        text = input("\n> ")
        if text.lower() == 'quit':
            break
        label, conf = classify_text(text, tokenizer, model)
        print(f"Predicted category: {label} (Confidence: {conf:.2f})")



