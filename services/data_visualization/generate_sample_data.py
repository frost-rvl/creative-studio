import pandas as pd
import numpy as np

np.random.seed(42)  # reproducible

# Date range: one year, hourly
dates = pd.date_range('2023-01-01', periods=1000, freq='h')

cities = ['Paris', 'London', 'New York', 'Tokyo', 'Sydney']

# Base values
temperature_base = 15 + 10 * np.sin(2 * np.pi * (dates.dayofyear / 365))  # seasonal
humidity_base = 60 + 15 * np.sin(2 * np.pi * (dates.dayofyear / 365) + 0.5)

df = pd.DataFrame({
    'Date_Time': dates,
    'Temperature_C': temperature_base + np.random.normal(0, 5, len(dates)),
    'Humidity_pct': np.clip(humidity_base + np.random.normal(0, 10, len(dates)), 0, 100),
    'Wind_Speed_kmh': np.random.exponential(10, len(dates)),
    'Precipitation_mm': np.random.exponential(2, len(dates)),
    'Pressure_hPa': 1013 + np.random.normal(0, 10, len(dates)),
    'City': np.random.choice(cities, len(dates))
})

# Round to 2 decimals
df = df.round(2)

df.to_csv('sample_data.csv', index=False)
print("✅ sample_data.csv created with 1000 rows.")