# Adobe India Hackathon 2025 – Challenge 1B: PDF Processing Solution

## Overview

This repository contains a solution for **Challenge 1A** of the Adobe India Hackathon 2025. The challenge focuses on extracting structured outlines from PDF documents and outputting them in a specified JSON format. The solution is containerized using Docker to meet specific performance and resource constraints.

---

## 🚀 Challenge Requirements

### Input

* A PDF file (up to 50 pages)

### Output

* A JSON file containing:

  * `title`: The document title
  * `outline`: An array of headings with their levels (H1, H2, H3) and corresponding page numbers([LinkedIn][1])

### JSON Format Example

```json
{
  "title": "Understanding AI",
  "outline": [
    { "level": "H1", "text": "Introduction", "page": 1 },
    { "level": "H2", "text": "What is AI?", "page": 2 },
    { "level": "H3", "text": "History of AI", "page": 3 }
  ]
}
```



### Constraints

* Execution time: ≤ 10 seconds for a 50-page PDF
* Model size: ≤ 200MB (if using ML models)
* No internet access allowed during runtime execution
* Runtime: Must run on CPU (amd64) with 8 CPUs and 16 GB RAM
* Architecture: Must work on AMD64, not ARM-specific([Unstop][2])

---

## 🧪 Solution Structure

```plaintext
Challenge_1b/
├── Collection 1/                    # Travel Planning
│   ├── PDFs/                       # South of France guides
│   ├── challenge1b_input.json      # Input configuration
│   └── challenge1b_output.json     # Analysis results
├── Collection 2/                    # Adobe Acrobat Learning
│   ├── PDFs/                       # Acrobat tutorials
│   ├── challenge1b_input.json      # Input configuration
│   └── challenge1b_output.json     # Analysis results
├── Collection 3/                    # Recipe Collection
│   ├── PDFs/                       # Cooking guides
│   ├── challenge1b_input.json      # Input configuration
│   └── challenge1b_output.json     # Analysis results
└── README.md
```



---

## ⚙️ Sample Implementation

The provided `main_1b.py` demonstrates:

* Scanning PDF files from the input directory
* Generating dummy JSON data
* Creating output files in the specified format([HackerRank][3])

**Note**: This is a placeholder implementation. A real solution would:

* Implement actual PDF text extraction
* Parse document structure and hierarchy
* Generate meaningful JSON output based on content analysis

---

## 🐳 Docker Configuration

```Dockerfile
FROM --platform=linux/amd64 python:3.10-slim

# Set working directory
WORKDIR /app

# Copy necessary files
COPY main_1b.py .
COPY requirements.txt .
COPY schema ./schema

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create input/output directories
RUN mkdir -p /app/input /app/output

# Run the main script
CMD ["python", "main_1b.py"]
```



---

## 🧪 Testing Your Solution

### Local Testing

```bash
FROM --platform=linux/amd64 python:3.10-slim

# Set working directory
WORKDIR /app

# Copy necessary files
COPY main_1b.py .
COPY requirements.txt .
COPY schema ./schema

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create input/output directories
RUN mkdir -p /app/input /app/output

# Run the main script
CMD ["python", "main_1b.py"]```



---

## ✅ Validation Checklist

* [ ] All PDFs in the input directory are processed
* [ ] JSON output files are generated for each PDF
* [ ] Output format matches the required structure
* [ ] Output conforms to the schema in `sample_dataset/schema/output_schema.json`
* [ ] Processing completes within 10 seconds for 50-page PDFs
* [ ] Solution works without internet access
* [ ] Memory usage stays within 16GB limit
* [ ] Compatible with AMD64 architecture([HackerRank][3])

---

## 📄 References

* [Adobe India Hackathon 2025 – Round 1 Challenge PDF](https://github.com/tanuj21497/Adobe_Hackathon_R1/blob/main/Round%201%20Challenge%20%281%29.pdf)
* [GitHub Repository – PDF Processing Solution](https://github.com/Harsha-47588/Adobe-India-Hackathon25/new/main/challenge_1a)
