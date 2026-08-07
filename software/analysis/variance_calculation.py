import numpy as np

# measured deplacements (in mm)

gait_a = [170.62, 253.19, 189.43, 224.56, 433.79, 352.35, 251.50, 90.82, 336.09, 274.38] #[1000, 1000, 1000]
gait_b = [47.21, 46.37, 71.59, 66.76, 78.52, 85.75, 90.83, 89.73, 78.99, 67.79] #[-800, 400, 900]
gait_c = [41.75, 33.76, 11.71, 24.66, 37.59, 119.27, 5.38, 20.03, 3.18, 88.75] #[660, -660, 660]

# Calculate variance (ddof=1 calculates sample variance)
var_a = np.var(gait_a, ddof=1)
var_b = np.var(gait_b, ddof=1)
var_c = np.var(gait_c, ddof=1)

# Average the variances to get your baseline
average_variance = np.mean([var_a, var_b, var_c])

print(f"Gait A Variance: {var_a:.2f}")
print(f"Gait B Variance: {var_b:.2f}")
print(f"Gait C Variance: {var_c:.2f}")
print(f"NOISE VARIANCE IS: {average_variance:.2f} <---")