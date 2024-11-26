import csv
import os
from flask import Flask, render_template, request, send_file
from datetime import datetime
import cohere
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# Initialize Flask app
app = Flask(__name__)

# Cohere API Key
COHERE_API_KEY = "yHIp5RAuiSn7wAm5elzzzTo0MWd55EPp2BQ1Hhkc"
co = cohere.Client(COHERE_API_KEY)

# Path to the CSV file
CSV_FILE = "signed_ndas.csv"

# Initialize CSV file with headers if it doesn't exist
if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["User Name", "Company", "Date Signed", "Timestamp"])

# Generate NDA using Cohere's API
def generate_nda(company_name):
    prompt = f"""
    Write a professional Non-Disclosure Agreement (NDA) for a company called {company_name}. 
    Include the following:
    - A confidentiality clause.
    - A term length of 5 years.
    - A section prohibiting the sharing of proprietary information without prior written consent.
    - The purpose of the agreement is to protect financial and operational information.
    """
    response = co.generate(
        model="command-xlarge-nightly",
        prompt=prompt,
        max_tokens=500,
        temperature=0.7,
        k=0,
        p=0.75
    )
    return response.generations[0].text.strip()

# Generate NDA as a PDF
def generate_pdf(user_name, company_name, nda_text):
    filename = f"nda_{company_name}_{user_name}.pdf"
    filepath = os.path.join("generated_ndas", filename)
    os.makedirs("generated_ndas", exist_ok=True)

    c = canvas.Canvas(filepath, pagesize=letter)
    c.setFont("Helvetica", 12)
    width, height = letter

    # Title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, height - 50, f"Non-Disclosure Agreement (NDA) for {company_name}")

    # NDA Text
    c.setFont("Helvetica", 12)
    y = height - 100
    for line in nda_text.split("\n"):
        c.drawString(50, y, line.strip())
        y -= 15

    # Signature
    y -= 30
    c.drawString(50, y, f"Signed by: {user_name}")
    c.drawString(50, y - 15, f"Date: {datetime.now().date()}")

    c.save()
    return filepath

@app.route('/')
def index():
    companies = ["Test Company 1", "Test Company 2", "Test Company 3"]
    return render_template("index_nda.html", companies=companies)

@app.route('/nda/<company>', methods=['GET', 'POST'])
def show_nda(company):
    if request.method == 'POST':
        user_name = request.form.get("user_name")
        if not user_name.strip():
            error = "Please enter your name to sign the NDA."
            return render_template("nda.html", company=company, nda_text=generate_nda(company), error=error)

        # Log the signed NDA
        with open(CSV_FILE, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            timestamp = datetime.now()
            writer.writerow([user_name, company, timestamp.date(), timestamp.time()])

        # Generate and provide a downloadable PDF
        nda_text = generate_nda(company)
        pdf_path = generate_pdf(user_name, company, nda_text)
        return send_file(pdf_path, as_attachment=True)

    # Show NDA text
    nda_text = generate_nda(company)
    return render_template("nda.html", company=company, nda_text=nda_text)

@app.route('/log')
def view_log():
    # Display the CSV content as an HTML table
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, mode='r', encoding='utf-8') as file:
            csv_content = list(csv.reader(file))
        return render_template("log.html", csv_content=csv_content)
    return "No signatures recorded yet.", 404

if __name__ == "__main__":
    app.run(debug=True)


