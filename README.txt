
PDF Outline Extractor - Adobe Hackathon Submission

How to Use:
1. Place all PDF files into /app/input (or input folder in host machine).
2. Build Docker image:
   docker build --platform linux/amd64 -t mysolution:uniqueid .
3. Run container:
   docker run --rm -v $(pwd)/input:/app/input -v $(pwd)/output:/app/output -network none mysolution:uniqueid
4. Output .json will appear in /app/output.

Ensure your input/output folders are present locally before running.
