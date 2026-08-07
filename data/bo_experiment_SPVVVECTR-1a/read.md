# SPVVVECTR-1a | 7/28/2026
## - 15 Random/LHS Priors + 35 opt steps | 50 opt steps (no priors)
### FYI 

For *No Priors*, the implementation likely does not correspond to no priors. Instead, there likely are several random priors tested before going into optimization steps as a default approach in the python implementation when prior parameter is left blank.

Also, robot was occasionally repositioned during all of these experiments. i.e. Only resetting position and orientation when robot was close to mocap boundaries or needed battery replacement. Otherwise, robot's start position was allowed to vary throughout the trial. We eventually felt it superior to reposition following every trial since the flooor (where we trial spvvvectr) possesses a slight incline. 