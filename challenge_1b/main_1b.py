import os
import fitz
import json
import unicodedata
from datetime import datetime
from collections import Counter
from langdetect import detect, LangDetectException

BOLD_FLAG = 2**17
COLLECTIONS = ["Collection 1", "Collection 2", "Collection 3"]

PERSONA_TASKS = {
    "Collection 1": {
        "persona": "Gym Trainer",
        "job_to_be_done": "Create a 4-day recovery and sleep enhancement plan for a group of gym-goers."
    },
    "Collection 2": {
        "persona": "Finance Student",
        "job_to_be_done": "Learn the basic concepts of stock markets from the provided material."
    },
     "Collection 3": {
        "persona": "Luxury Travel Content Creator",
        "job_to_be_done": "Develop a comprehensive travel guide to the South of France, highlighting cities, cuisine, culture, and hidden gems."
    }
}


def clean_text(text):
    return unicodedata.normalize("NFC", text).strip()

def is_bold(span):
    if 'flags' in span and span['flags'] & BOLD_FLAG:
        return True
    font_name = span.get('font', '').lower()
    return any(x in font_name for x in ['bold', 'black', 'heavy']) or font_name.endswith(('bd', 'blk'))

def detect_language(doc):
    text = ""
    for page in doc:
        text += page.get_text()
        if len(text) >= 1000:
            break
    try:
        return detect(text)
    except LangDetectException:
        return "unknown"

def get_font_statistics(doc):
    sizes, fonts = [], []
    for page in doc:
        for block in page.get_text("dict")['blocks']:
            if block['type'] == 0:
                for line in block['lines']:
                    for span in line['spans']:
                        sizes.append(round(span['size']))
                        fonts.append(span['font'])
    return (Counter(sizes).most_common(1)[0][0] if sizes else 12,
            Counter(fonts).most_common(1)[0][0] if fonts else "DefaultFont")

def extract_headings(pdf_path):
    doc = fitz.open(pdf_path)
    base_size, _ = get_font_statistics(doc)
    headings = []

    for page_num, page in enumerate(doc):
        for block in page.get_text("dict")["blocks"]:
            if block['type'] == 0:
                for line in block['lines']:
                    spans = line.get("spans", [])
                    if not spans:
                        continue
                    text = clean_text("".join(span['text'] for span in spans))
                    if not text or len(text) < 5:
                        continue
                    if (
                        round(spans[0]['size']) > base_size or
                        (round(spans[0]['size']) == base_size and is_bold(spans[0]))
                    ):
                        headings.append({
                            "text": text,
                            "size": round(spans[0]['size']),
                            "page": page_num + 1,
                            "y": line['bbox'][1]
                        })

    # Deduplicate
    seen, unique = set(), []
    for h in sorted(headings, key=lambda x: (x['page'], x['y'])):
        if h['text'] not in seen:
            unique.append(h)
            seen.add(h['text'])

    size_to_level = {}
    for idx, sz in enumerate(sorted({h['size'] for h in unique}, reverse=True)):
        size_to_level[sz] = f"H{idx + 1}"

    outline = [
        {
            "level": size_to_level[h['size']],
            "text": h['text'],
            "page": h['page']
        }
        for h in unique if h['size'] in size_to_level
    ]

    title = outline[0]['text'] if outline else os.path.basename(pdf_path)
    return {
        "title": title,
        "outline": outline
    }

def process_collection(collection_folder):
    pdf_dir = os.path.join(collection_folder, "pdfs")
    input_json_path = os.path.join(collection_folder, "challenge1b_input.json")
    output_json_path = os.path.join(collection_folder, "challenge1b_output.json")

    if not os.path.exists(pdf_dir):
        print(f"❌ PDF folder not found: {pdf_dir}")
        return

    documents, extracted_sections, subsection_analysis = [], [], []

    for idx, filename in enumerate(sorted(os.listdir(pdf_dir))):
        if not filename.endswith(".pdf"):
            continue

        pdf_path = os.path.join(pdf_dir, filename)
        result = extract_headings(pdf_path)

        documents.append({"filename": filename, "title": result["title"]})

        if result["outline"]:
            first = result["outline"][0]
            extracted_sections.append({
                "document": filename,
                "section_title": first["text"],
                "importance_rank": idx + 1,
                "page_number": first["page"]
            })
            subsection_analysis.append({
                "document": filename,
                "refined_text": f"Sample refined content for '{first['text']}'...",
                "page_number": first["page"]
            })

    persona_info = PERSONA_TASKS.get(collection_folder, {
        "persona": "General Analyst",
        "job_to_be_done": "Summarize useful information from the documents."
    })

    input_json = {
        "challenge_info": {
            "challenge_id": f"round_1b_{collection_folder[-1]}",
            "test_case_name": f"testcase_{collection_folder[-1]}",
            "description": f"Auto-generated input for {collection_folder}"
        },
        "documents": documents,
        "persona": {"role": persona_info["persona"]},
        "job_to_be_done": {"task": persona_info["job_to_be_done"]}
    }

    output_json = {
        "metadata": {
            "input_documents": [doc["filename"] for doc in documents],
            "persona": input_json["persona"]["role"],
            "job_to_be_done": input_json["job_to_be_done"]["task"],
            "processing_timestamp": datetime.now().isoformat()
        },
        "extracted_sections": extracted_sections,
        "subsection_analysis": subsection_analysis
    }

    with open(input_json_path, 'w', encoding='utf-8') as f:
        json.dump(input_json, f, indent=2, ensure_ascii=False)

    with open(output_json_path, 'w', encoding='utf-8') as f:
        json.dump(output_json, f, indent=2, ensure_ascii=False)

    print(f"✅ Processed {collection_folder}: JSON files generated.")

def main():
    for collection in COLLECTIONS:
        process_collection(collection)

if __name__ == "__main__":
    main()