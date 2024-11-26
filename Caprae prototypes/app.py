from flask import Flask, request, render_template
import numpy as np
import pickle

app = Flask(__name__)

# Load pre-trained machine learning model (trained offline)
model = pickle.load(open("valuation_model.pkl", "rb"))

@app.route('/')
def home():
    return render_template('index_discrepancy.html')

@app.route('/predict', methods=['POST'])
def predict():
    try:
        # Extract user inputs
        revenue = float(request.form['revenue'])
        expenses = float(request.form['expenses'])
        profit = float(request.form['profit'])
        growth_rate = float(request.form['growth_rate'])
        debt = float(request.form['debt'])
        assets = float(request.form['assets'])
        industry_type = int(request.form['industry_type'])  # Assume encoded as 0, 1, 2

        # Prepare input for the model
        features = np.array([[revenue, expenses, profit, growth_rate, debt, assets, industry_type]])

        # Predict valuation
        valuation = model.predict(features)[0]

        # Return the result
        return render_template('index_discrepancy.html',
                               prediction_text=f"The estimated business valuation is ${valuation:,.2f}")
    except Exception as e:
        return render_template('index_discrepancy.html',
                               prediction_text="Error in processing input. Please check your values.")

if __name__ == "__main__":
    app.run(debug=True)

