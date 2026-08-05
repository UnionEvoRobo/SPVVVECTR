# SPVVVECTR-1b | 8/4/2026
## `[1000,1000,1000]` vs `[982,414,-301]`
### FYI 

We let `gait_max = [1000, 1000, 1000]` and benchmark it against our optimizer found linear behaving gait, `gait_l = [982, 414, -301]`.

**Purpose**

Determining good strategies for optimal gait generation is a research question. `gait_l` was the fittest gait generated with a Bayesian Optimization experiment (15 LHS priors + 35 steps). We choose `gait_max` to be our benchmark because from empirical pretenses, it is assumed that higher frequencies induce higher displacements, albeit with higher variation. 

This experiment then shows that BO was capable of generating a gait, `gait_l`, that not only beats fitness from `gait_max` (displacement in mm), but achieved locomotion that behaves near linearly. that our optimizer inadvertently found when fitness measured as maximizing linear displacement.