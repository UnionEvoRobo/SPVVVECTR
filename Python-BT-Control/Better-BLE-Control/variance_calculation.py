import numpy as np

# Example data: Replace these with your actual measured displacements (in mm)
gait_a = [140.2, 145.5, 138.9, 150.1, 142.3, 144.0, 139.5, 148.2, 141.8, 143.5]
gait_b = [85.1, 88.3, 82.5, 90.0, 84.2, 86.7, 81.9, 89.1, 83.4, 85.8]
gait_c = [45.2, 42.1, 48.5, 44.0, 46.8, 43.5, 47.2, 41.9, 45.9, 44.4]

# Calculate variance (ddof=1 calculates sample variance)
var_a = np.var(gait_a, ddof=1)
var_b = np.var(gait_b, ddof=1)
var_c = np.var(gait_c, ddof=1)

# Average the variances to get your baseline
average_variance = np.mean([var_a, var_b, var_c])

print(f"Gait A Variance: {var_a:.2f}")
print(f"Gait B Variance: {var_b:.2f}")
print(f"Gait C Variance: {var_c:.2f}")
print(f"\n---> YOUR NOISE VARIANCE IS: {average_variance:.2f} <---")