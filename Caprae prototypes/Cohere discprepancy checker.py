from flask import Flask, request, send_file, jsonify, render_template
from PyPDF2 import PdfReader
from fpdf import FPDF
import cohere

# Initialize Flask app and Cohere API
app = Flask(__name__)
COHERE_API_KEY = "yHIp5RAuiSn7wAm5elzzzTo0MWd55EPp2BQ1Hhkc"
co = cohere.Client(COHERE_API_KEY)

def load_documents(file_stream):
    """
    Load and extract text from a PDF file stream.
    """
    reader = PdfReader(file_stream)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text.strip()

def find_discrepancies(seller_text, buyer_text):
    """
    Compare seller and buyer documents for discrepancies using Cohere's Generate API.
    """
    prompt = f"""
    Compare the following two documents and identify discrepancies. Categorize them into:
    - Financial Terms
    - Legal Terms
    - Missing or Extra Clauses
    - Ambiguous or Conflicting Statements

    Seller Document:
    {seller_text[:1000]}

    Buyer Document:
    {buyer_text[:1000]}

    Provide a detailed, categorized list of discrepancies.
    """
    response = co.generate(
        model="command-xlarge-nightly",
        prompt=prompt,
        max_tokens=500,
        temperature=0.2,
    )
    return response.generations[0].text.strip()

@app.route('/')
def index():
    return render_template('index_discrepancy.html')  # Render the renamed HTML file

@app.route('/upload', methods=['POST'])
def upload_files():
    try:
        seller_file = request.files['sellerFile']
        buyer_file = request.files['buyerFile']

        seller_text = load_documents(seller_file.stream)
        buyer_text = load_documents(buyer_file.stream)

        discrepancies = find_discrepancies(seller_text, buyer_text)

        # Create a PDF report
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, discrepancies)

        output_path = "discrepancy_report.pdf"
        pdf.output(output_path)

        return send_file(output_path, as_attachment=True)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)

