import numpy as np

# measured deplacements (in mm)

gait_a = [170.62, 253.19, 189.43, 224.56, 433.79, 352.35, 251.50, 90.82, 336.09, 274.38] #[1000, 1000, 1000]
gait_b = [47.21, 46.37, 71.59, 66.76, 78.52, 85.75, 90.83, 89.73, 78.99, 67.79] #[-800, 400, 900]
gait_c = [41.75, 33.76, 11.71, 24.66, 37.59, 119.27, 5.38, 20.03, 3.18, 88.75] #[660, -660, 660]

# Second dataset, measured on the qtm-api-integration branch on a different
# build of the robot. Kept for reference; NOT averaged into the baseline below,
# since mixing builds would not give a meaningful noise estimate.
# qtm_gait_a = [319.58, 299.53, 164.82, 211.08, 194.07, 285.05, 118.29, 173.51, 129.26, 123.06] #[1000, 1000, 1000]
# qtm_gait_d = [200.06, 140.76, 156.22, 63.31, 137.71, 109.78, 93.78, 121.92, 62.28, 108.12] #[760, 760, 760]

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