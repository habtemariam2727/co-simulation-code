import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Load the original profiles
input_file = 'profile_generator/practicum-5/combined_profiles_one_year_original.csv'
df = pd.read_csv(input_file)

# Introduce noise to simulate forecasted profiles
std_dev = 0.6  # 60% noise

customer_columns = df.columns[1:]
df_forecasted = df.copy()

# Use absolute mean to avoid negative scale
noise_scale = std_dev * df[customer_columns].mean().abs()
df_forecasted[customer_columns] += np.random.normal(0, noise_scale.values, size=df[customer_columns].shape)

output_file = 'profile_generator/practicum-5/combined_active_power_forecasted.csv'
output_file2 = 'data/combined_active_power_forecasted.csv'
df_forecasted.to_csv(output_file, index=False)
df_forecasted.to_csv(output_file2, index=False)

print(f"Forecasted profiles with noise saved to {output_file} and {output_file2}")



# Plot original vs forecasted for one selected customer
customer_to_plot = df.columns[30]  # select a customer column to plot
plt.figure(figsize=(12, 6))
plt.plot(df[customer_to_plot], label='Original')
plt.plot(df_forecasted[customer_to_plot], label='Forecasted (Noisy)')
plt.xlabel('Snapshots')
plt.ylabel('Power (kW)')
plt.title(f'Original vs Forecasted Profile for {customer_to_plot}')
plt.legend()
plt.tight_layout()
plt.show()
