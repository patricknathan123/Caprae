import os
from flask import Flask, request, jsonify, render_template
import pandas as pd
import cohere
from sklearn.ensemble import RandomForestRegressor
import numpy as np

# Initialize Flask app
app = Flask(__name__)

# Cohere API Key
COHERE_API_KEY = "yHIp5RAuiSn7wAm5elzzzTo0MWd55EPp2BQ1Hhkc"
co = cohere.Client(COHERE_API_KEY)

def extract_financial_data_with_cohere(data):
    """
    Use the Cohere API to intelligently extract financial data from a CSV DataFrame.
    """
    try:
        # Convert the entire DataFrame to a string for Cohere to process
        csv_content = data.to_csv(index=False)

        # Prompt to Cohere
        prompt = f"""
        You are an AI financial analyst. Below is a CSV file of a company's financial data:

        {csv_content}

        Identify and extract the following metrics for the current year:
        - Revenue
        - Cost of Goods Sold (COGS)
        - SG&A
        - EBITDA
        - Enterprise Value

        If any metric is missing, set its value to 0. Format your output as JSON with the keys: "Revenue", "COGS", "SG&A", "EBITDA", "Enterprise Value".
        """

        # Call Cohere API to extract data
        response = co.generate(
            model="command-xlarge-nightly",
            prompt=prompt,
            max_tokens=300,
            temperature=0.5,
        )

        # Parse the Cohere output into a Python dictionary
        extracted_data = eval(response.generations[0].text.strip())

        # Ensure all values are floats
        for key in extracted_data:
            try:
                extracted_data[key] = float(
                    str(extracted_data[key]).replace("$", "").replace(",", "").strip()
                )
            except ValueError:
                extracted_data[key] = 0.0  # Default to 0.0 if conversion fails

        return extracted_data

    except Exception as e:
        print(f"Error with Cohere API: {e}")
        return {
            "Revenue": 0.0,
            "COGS": 0.0,
            "SG&A": 0.0,
            "EBITDA": 0.0,
            "Enterprise Value": 0.0,
        }

def calculate_optimized_price(extracted_data):
    """
    Use a regression model to calculate the optimized selling price based on extracted financial data.
    """
    # Sample training data
    sample_data = pd.DataFrame({
        "Revenue": [10000000, 12000000, 14000000, 16000000, 18000000],
        "Expenses": [8000000, 9000000, 11000000, 12000000, 14000000],
        "Profit": [2000000, 3000000, 3000000, 4000000, 4000000],
        "Selling Price": [5000000, 6000000, 7000000, 8000000, 9000000]
    })

    # Define features (X) and target (y)
    X = sample_data[["Revenue", "Expenses", "Profit"]]
    y = sample_data["Selling Price"]

    # Train a Random Forest Regressor
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X, y)

    # Calculate additional metrics for the given company
    revenue = extracted_data.get("Revenue", 0.0)
    cogs = extracted_data.get("COGS", 0.0)
    sga = extracted_data.get("SG&A", 0.0)
    expenses = cogs + sga
    profit = revenue - expenses

    # Predict selling price using the model
    company_features = np.array([[revenue, expenses, profit]])
    predicted_price = model.predict(company_features)[0]

    return round(predicted_price, 2)


@app.route('/')
def index():
    return render_template('upload_financial_data.html')

@app.route('/optimize_price', methods=['POST'])
def optimize_price():
    try:
        # Get the uploaded file
        file = request.files['financialData']
        file_path = os.path.join("uploads", file.filename)

        # Ensure the "uploads" directory exists
        os.makedirs("uploads", exist_ok=True)

        # Save the uploaded file
        file.save(file_path)

        # Load the CSV file into a DataFrame
        data = pd.read_csv(file_path)

        # Extract financial data using Cohere
        extracted_data = extract_financial_data_with_cohere(data)

        # Calculate the optimized selling price
        optimized_price = calculate_optimized_price(extracted_data)

        # Return the extracted data and optimized price
        return jsonify({"extractedData": extracted_data, "optimizedPrice": optimized_price})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)







