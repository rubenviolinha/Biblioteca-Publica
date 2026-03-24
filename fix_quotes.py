import json
import os
import re

# Directory containing the book folders
BOOKS_DIR = './data/books'

def smarten_quotes(text):
    if not isinstance(text, str):
        return text
    
    # 1. Replace double quotes
    # Opening quotes: start of string, after space, after opening parenthesis/bracket/brace, or after em-dash
    text = re.sub(r'(^|[\s\(\[\{—])"', r'\1“', text)
    # Closing quotes: everything else
    text = re.sub(r'"', r'”', text)
    
    # 2. Replace single quotes (apostrophes vs quotes)
    # Opening single quotes
    text = re.sub(r"(^|[\s\(\[\{—])'", r"\1‘", text)
    # Closing single quotes / apostrophes
    text = re.sub(r"'", r"’", text)
    
    return text

def process_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        modified = False
        
        # Recursively process strings in the JSON object
        def traverse(obj):
            nonlocal modified
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if isinstance(v, str):
                        new_val = smarten_quotes(v)
                        if new_val != v:
                            obj[k] = new_val
                            modified = True
                    elif isinstance(v, (dict, list)):
                        traverse(v)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    if isinstance(item, str):
                        new_val = smarten_quotes(item)
                        if new_val != item:
                            obj[i] = new_val
                            modified = True
                    elif isinstance(item, (dict, list)):
                        traverse(item)

        traverse(data)
        
        if modified:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"✅ Updated quotes in: {os.path.basename(filepath)}")
        else:
            print(f"No changes needed for: {os.path.basename(filepath)}")
            
    except json.JSONDecodeError:
        print(f"❌ Error: {os.path.basename(filepath)} is invalid JSON. Cannot process.")
    except Exception as e:
        print(f"❌ Error processing {os.path.basename(filepath)}: {str(e)}")

# Run for all JSON files in the books tree (excluding generated compiled.json)
print("Starting smart quote conversion...")
if not os.path.exists(BOOKS_DIR):
    print(f"Directory {BOOKS_DIR} not found.")
else:
    for root, _, files in os.walk(BOOKS_DIR):
        for filename in files:
            if not filename.endswith('.json'):
                continue
            if filename == 'compiled.json':
                continue
            process_file(os.path.join(root, filename))
print("Done!")
