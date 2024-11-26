import os
import pandas as pd
import matplotlib.pyplot as plt
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from fpdf import FPDF
from PyPDF2 import PdfReader
import cohere

# Flask app initialization
app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'output'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Initialize Cohere client
COHERE_API_KEY = 'yHIp5RAuiSn7wAm5elzzzTo0MWd55EPp2BQ1Hhkc'
co = cohere.Client(COHERE_API_KEY)

# PDF class
class CustomPDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Confidential Information Memorandum (CIM)', 0, 1, 'C')

    def chapter_title(self, title):
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, title, 0, 1, 'L')
        self.ln(5)

    def chapter_body(self, body):
        self.set_font('Arial', '', 12)
        self.multi_cell(0, 10, body)
        self.ln()

    def add_graph(self, graph_path):
        self.image(graph_path, x=10, y=None, w=180)
        self.ln(10)

# Extract content from files, skipping corrupted ones
def extract_text_from_file(file_path):
    """
    Extract text from files, handling errors gracefully.
    """
    try:
        if file_path.endswith('.pdf'):
            # Process PDF files
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
            return text
        elif file_path.endswith('.csv'):
            # Process CSV files
            df = pd.read_csv(file_path, on_bad_lines='skip')
            return df.to_string(index=False)
        elif file_path.endswith('.txt'):
            # Process TXT files
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        else:
            return f"Unsupported file type for {file_path}"
    except Exception as e:
        # Log the error and skip the file
        print(f"Error processing file {file_path}: {e}")
        return ""

# Fetch additional information with Cohere
def fetch_additional_info(company_query):
    try:
        response = co.chat(
            message=f"Provide detailed and up-to-date information about {company_query}.",
            connectors=[{"id": "web-search"}]
        )
        return response.text
    except Exception as e:
        return f"Error fetching additional information: {e}"

# Generate CIM, skipping corrupted files
def generate_cim(file_paths, company_query, output_pdf_path):
    combined_content = ""

    # Process each file and skip corrupted ones
    for file_path in file_paths:
        file_content = extract_text_from_file(file_path)
        if file_content:  # Skip files that returned empty or error messages
            combined_content += file_content + "\n\n"
        else:
            print(f"Skipping corrupted or unreadable file: {file_path}")

    # Fetch additional information online
    additional_info = fetch_additional_info(company_query)

    # Combine the content and additional information
    full_content = combined_content + additional_info

    # Split combined content into manageable chunks
    words = full_content.split()
    chunk_size_limit = 2500  # Smaller chunk size to fit within Cohere's token limit
    chunks = [" ".join(words[i:i + chunk_size_limit]) for i in range(0, len(words), chunk_size_limit)]

    pdf = CustomPDF()
    pdf.add_page()

    for i, chunk in enumerate(chunks):
        try:
            response = co.generate(
                model='command-xlarge',
                prompt=f"""
                Generate a section of an in-depth Confidential Information Memorandum (CIM) based on the following data:
                {chunk}

                Include detailed paragraphs, bullet points, and tables where applicable. Ensure professional formatting.
                """,
                max_tokens=1500,
                temperature=0.7,
            )
            cim_content = response.generations[0].text
            sections = cim_content.split("\n\n")

            for section in sections:
                parts = section.split("\n", 1)
                if len(parts) == 2:
                    title, body = parts
                else:
                    title = f"Additional Notes - Part {i+1}"
                    body = parts[0]

                pdf.chapter_title(title.strip())
                pdf.chapter_body(body.strip())

        except cohere.errors.BadRequestError as e:
            print(f"Error processing chunk {i+1}: {e}")
            pdf.chapter_title(f"Error in Chunk {i+1}")
            pdf.chapter_body("Could not process this section due to size constraints.")

    # Add graphs
    graph_path = generate_financial_graph()
    pdf.add_graph(graph_path)

    # Save the PDF
    pdf.output(output_pdf_path)

# Generate financial graph
def generate_financial_graph():
    years = [2019, 2020, 2021, 2022, 2023]
    revenue = [150, 170, 200, 230, 250]

    plt.figure(figsize=(10, 6))
    plt.plot(years, revenue, marker='o')
    plt.title("Revenue Growth Over Years")
    plt.xlabel("Year")
    plt.ylabel("Revenue ($M)")
    plt.grid(True)
    graph_path = os.path.join(app.config['OUTPUT_FOLDER'], 'revenue_growth.png')
    plt.savefig(graph_path)
    plt.close()
    return graph_path

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    files = request.files.getlist('files')
    company_query = request.form.get('companyQuery', '').strip()

    if not files or len(files) == 0:
        return jsonify({"message": "No files uploaded"}), 400

    if not company_query:
        return jsonify({"message": "No company query provided"}), 400

    file_paths = []
    for file in files:
        if file.filename == '':
            continue
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        file_paths.append(file_path)

    if not file_paths:
        return jsonify({"message": "No valid files uploaded"}), 400

    pdf_output_path = os.path.join(app.config['OUTPUT_FOLDER'], 'CIM_Document.pdf')
    generate_cim(file_paths, company_query, pdf_output_path)

    return jsonify({"message": "CIM generated successfully!", "cim_path": f"/output/{os.path.basename(pdf_output_path)}"}), 200

@app.route('/output/<filename>')
def serve_file(filename):
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)

