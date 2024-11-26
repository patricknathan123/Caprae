import pandas as pd
from sklearn.ensemble import RandomForestRegressor
import pickle

# Sample data with new features
data = {
    "Revenue": [1000000, 2000000, 3000000, 4000000, 5000000],
    "Expenses": [600000, 1200000, 1800000, 2400000, 3000000],
    "Profit": [400000, 800000, 1200000, 1600000, 2000000],
    "Growth_Rate": [5, 7, 10, 8, 6],  # Growth rate in %
    "Debt": [50000, 100000, 150000, 200000, 250000],
    "Assets": [2000000, 4000000, 6000000, 8000000, 10000000],
    "Industry_Type": [0, 1, 2, 0, 1],  # Encoded: 0=Tech, 1=Healthcare, 2=Retail
    "Valuation": [4000000, 6000000, 8000000, 10000000, 12000000]
}

# Create a DataFrame
df = pd.DataFrame(data)

# Features and target
X = df[["Revenue", "Expenses", "Profit", "Growth_Rate", "Debt", "Assets", "Industry_Type"]]
y = df["Valuation"]

# Train a Random Forest model
model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X, y)

# Save the model
pickle.dump(model, open("valuation_model.pkl", "wb"))
