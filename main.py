import fitz
import os
import json
import unicodedata
from collections import Counter
from langdetect import detect, LangDetectException
from jsonschema import validate, ValidationError

BOLD_FLAG = 2**17

# JSON Schema for validating the output format
OUTPUT_SCHEMA = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "outline": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "level": {"type": "string"},
                    "text": {"type": "string"},
                    "page": {"type": "integer"}
                },
                "required": ["level", "text", "page"]
            }
        }
    },
    "required": ["title", "outline"]
}

def validate_json_output(result, filename=""):
    try:
        schema_path = os.path.join(os.path.dirname(__file__), "schema", "output_schema.json")
        with open(schema_path, "r", encoding="utf-8") as f:
            schema = json.load(f)
        validate(instance=result, schema=schema)
        return True
    except ValidationError as e:
        print(f"❌ JSON validation failed for {filename}: {e.message}")
        return False
    except FileNotFoundError:
        print(f"❌ Schema file not found in /schema/. Please ensure it's copied into the container.")
        return False


def clean_text(text):
    return unicodedata.normalize("NFC", text).strip()

def get_font_statistics(doc):
    sizes = []
    fonts = []
    for page in doc:
        blocks = page.get_text("dict")['blocks']
        for block in blocks:
            if block['type'] == 0:
                for line in block['lines']:
                    for span in line['spans']:
                        sizes.append(round(span['size']))
                        fonts.append(span['font'])
    if not sizes:
        return 12, "DefaultFont"
    most_common_size = Counter(sizes).most_common(1)[0][0]
    most_common_font = Counter(fonts).most_common(1)[0][0]
    return most_common_size, most_common_font

def detect_language(doc):
    full_text = ""
    min_chars = 1000
    for page in doc:
        full_text += page.get_text()
        if len(full_text) >= min_chars:
            break
    if not full_text.strip():
        return "unknown"
    try:
        lang = detect(full_text)
        if lang == "unknown" and any('\u0900' <= char <= '\u097F' for char in full_text):
            return "hi"
        return lang
    except LangDetectException:
        return "unknown"

def is_bold(span):
    if 'flags' in span and span['flags'] & BOLD_FLAG:
        return True
    font_name = span.get('font', '').lower()
    return any(x in font_name for x in ['bold', 'black', 'heavy']) or font_name.endswith(('bd', 'blk'))

def is_possible_heading(text, doc_language):
    text = text.strip()
    if not text:
        return False
    if doc_language == "ja":
        return (text.startswith(('「', '『')) and text.endswith(('」', '』'))
                or any(tok in text for tok in ['第', '章', '節']))
    elif doc_language == "hi":
        indicators = [
            "अध्याय", "अनुच्छेद", "धारा", "खंड", "प्रकरण", "भाग",
            "अनुभाग", "शीर्षक", "परिशिष्ट", "परिचय", "निष्कर्ष",
            "सारांश", "चैप्टर", "क्रमांक", "प्रारंभ", "अनुबंध", "तालिका"
        ]
        numbering_patterns = [
            text.startswith(('(', '[', '{', '१.', '२.', '३.', '४.', '५.')),
            any(text.startswith(f"{i}.") for i in range(1, 10))
        ]
        return any(indicator in text for indicator in indicators) or any(numbering_patterns)
    return False

def extract_headings(doc_path):
    try:
        doc = fitz.open(doc_path)
    except Exception as e:
        print(f"Error opening {doc_path}: {e}")
        return None

    base_size, base_font = get_font_statistics(doc)
    doc_language = detect_language(doc)

    if base_size == 0:
        print(f"Could not determine base font size for {doc_path}. Skipping.")
        return None

    candidates = []
    for page_num, page in enumerate(doc):
        blocks = page.get_text("dict", sort=True).get('blocks', [])
        for block in blocks:
            if block['type'] == 0:
                for line in block['lines']:
                    if not line['spans']:
                        continue
                    first_span = line['spans'][0]
                    text = clean_text("".join(span['text'] for span in line['spans']))
                    if not text:
                        continue

                    if (
                        text.startswith("{") and text.endswith("}") and ":" in text
                    ) or (
                        text.count('"') >= 4 and ":" in text and "level" in text and "text" in text
                    ):
                        continue

                    if doc_language == "hi":
                        hindi_chars = [ch for ch in text if '\u0900' <= ch <= '\u097F']
                        if len(hindi_chars) < 3:
                            continue

                    if sum(1 for c in text if not c.isalpha()) > len(text) * 0.6:
                        continue

                    is_heading_candidate = (
                        round(first_span['size']) > base_size or
                        (round(first_span['size']) == base_size and is_bold(first_span)) or
                        is_possible_heading(text, doc_language)
                    )
                    if is_heading_candidate:
                        candidates.append({
                            'text': text,
                            'size': round(first_span['size']),
                            'page': page_num + 1,
                            'y_pos': line['bbox'][1]
                        })

    if not candidates:
        return {"title": "", "language": doc_language, "outline": []}

    unique_candidates = []
    seen_texts = set()
    for cand in sorted(candidates, key=lambda x: (x['page'], x['y_pos'])):
        if cand['text'] not in seen_texts:
            unique_candidates.append(cand)
            seen_texts.add(cand['text'])

    heading_sizes = sorted({c['size'] for c in unique_candidates}, reverse=True)
    size_to_level = {}
    if heading_sizes:
        size_to_level[heading_sizes[0]] = "H1"
        if len(heading_sizes) > 1:
            size_to_level[heading_sizes[1]] = "H2"
        if len(heading_sizes) > 2:
            size_to_level[heading_sizes[2]] = "H3"

    outline = []
    title = ""
    found_title = False
    for cand in unique_candidates:
        if cand['size'] in size_to_level:
            level = size_to_level[cand['size']]
            outline.append({
                "level": level,
                "text": cand['text'],
                "page": cand['page']
            })
            if not found_title and level == "H1":
                title = cand['text']
                found_title = True

    if not title and outline:
        title = outline[0]['text']

    return {"title": title, "language": doc_language, "outline": outline}

def main():
    input_dir = "./input"
    output_dir = "./output"
    schema_dir = "./schema"
    
    
    if not os.path.exists(schema_dir):
        os.makedirs(schema_dir)


    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for filename in os.listdir(input_dir):
        if filename.lower().endswith(".pdf"):
            print(f"Processing {filename}...")
            pdf_path = os.path.join(input_dir, filename)
            result = extract_headings(pdf_path)
            if result and validate_json_output(result, filename):
                output_filename = os.path.splitext(filename)[0] + ".json"
                output_path = os.path.join(output_dir, output_filename)
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                print(f"✅ Successfully generated {output_filename}")
            else:
                print(f"❌ Skipping {filename} due to validation failure.")

if __name__ == "__main__":
    main()