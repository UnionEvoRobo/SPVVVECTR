import numpy as np

# Example data: Replace these with your actual measured displacements (in mm)
gait_a = [319.58, 299.53, 164.82, 211.08, 194.07, 285.05, 118.29, 173.51, 129.26, 123.06]#1000x3
gait_b = []
gait_c = []
gait_d = [200.06, 140.76, 156.22, 63.31, 137.71, 109.78, 93.78, 121.92, 62.28, 108.12] #760x3

# Calculate variance (ddof=1 calculates sample variance)
var_a = np.var(gait_a, ddof=1)
var_b = np.var(gait_b, ddof=1)
var_c = np.var(gait_c, ddof=1)
var_d = np.var(gait_d, ddof=1)

# Average the variances to get your baseline
average_variance = np.mean([var_a, var_b, var_c, var_d])

print(f"Gait A Variance: {var_a:.2f}")
print(f"Gait B Variance: {var_b:.2f}")
print(f"Gait C Variance: {var_c:.2f}")
print(f"Gait D Variance: {var_d:.2f}")
print(f"\n---> YOUR NOISE VARIANCE IS: {average_variance:.2f} <---")