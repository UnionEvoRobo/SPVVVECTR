# SPVVVECTR-1b | 8/4/2026
### FYI

Repositioning after every trial to maintain starting position and orientation as a constant. 

**Steps**

1. benchmark variance testing w/ max gait `[1000,1000,1000]`
    * 10 trials w/ constant starting point and orientation
    * 10 trials with minimal interference (only for camera bounds)

2. Bayesian Optimization 
    
    * 15 lhs; 35 opt steps 

3. variances testing w/ fittest 3 gaits 




**purpose**

From empirical testing, it is a consensus that higher frequency gaits tend to lead to higher displacements. A common gait is, thus, the gait that maximizes RPM for all 3 motors, `[1000,1000,1000]`. 

This experiment displays Bayesian Optimization's efficacy in producing high displacement gaits, using the maximum gait as a benchmark for improvement. 