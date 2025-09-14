# scripts/inspect_data.py
import os
import json
from collections import Counter

DATA_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'training_data.jsonl')

def main():
    if not os.path.exists(DATA_PATH):
        print("Training data file not found:", DATA_PATH)
        return

    counts = Counter()
    total_length = 0
    total_docs = 0

    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            data = json.loads(line)
            label = data.get('label', 'Unknown')
            text = data.get('text', '')
            counts[label] += 1
            total_length += len(text)
            total_docs += 1

    print("Labeled Data Statistics:")
    print("========================")
    print(f"Total documents: {total_docs}")
    if total_docs > 0:
        print(f"Average document length (characters): {total_length // total_docs}")
    print("\nDocument count per category:")
    for category, count in counts.items():
        print(f"  {category}: {count}")

if __name__ == '__main__':
    main()
