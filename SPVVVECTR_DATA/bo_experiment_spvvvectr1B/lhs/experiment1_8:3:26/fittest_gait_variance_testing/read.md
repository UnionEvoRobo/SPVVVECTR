# SPVVVECTR-1b | 8/3/2026
## Variance Testing - Fittest Gait: [982, 414, -301]
### FYI 

**Test 1 (41 Trials)** 

This test was occasionally repositioned *(meaning below)*, however had an interesting behavior. 

Displacements did not seem to be noisy, they seemed to be drifting in a predictable pattern. `Trial 1-29` saw a positive drift from `119.87mm` to `295.49mm`. 

Then the biggest jump was following `trial 30`, with a displacement of `403.18mm`. This was likely a combination of the continuing drift plus the fact that batteries were replaced after `trial 29`. Unsure of how fully charged batteries can cause this big leap, however, since rpm should stay constant whether the battery is low or high. 

Also robot behavior was exciting, since this gait seemed to move the robot almost in a straight line. The next test below, dove into measuring this. 

robot was occasionally repositioned during this experiment. i.e. Only resetting position and orientation when robot was close to mocap boundaries or needed battery replacement. Otherwise, robot's start position was allowed to vary throughout the trial. We eventually felt it superior to reposition following every trial since the flooor (where we trial spvvvectr) possesses a slight incline. 

**Test 2 (10 Trials)** 

This test repositioned the robot after every angle to keep same position and orientation at the start of every trial. This truly measured variance in the gait.

Displacement was very consistent much less variation than prior test, (and also lacking the drifting behavior?). Displacements began at the plataued point of drift the previous test reached. 


