from bayes_opt import BayesianOptimization, acquisition
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import gridspec



def black_box_function(x):
    """our hidden function that optimizer predicts; just for testing purposes since irl, we don't know the blackbox function"""
    return x ** 2

# visualizing blackbox function (nothing being optimized)
# .linespace generates arr of 10,000 elements between 1 and 4 orderly
#.reshape translates the arr into a 10,000x1 matrix (use -1 for row-nums to tell computer to figure it out instead of manuelly typing)
x = np.linspace(-4, 4, 10000).reshape(-1, 1)
y = black_box_function(x)

plt.plot(x, y)
plt.xlabel("x-axis")
plt.ylabel("y-axis")
plt.title("Blackbox Function (That optimizer doesn't know)")
plt.show()

# pbounds is boundaries for input that our optimizer will attempt to observe 
# pbounds = {'x': (-4, 4)}
# acq = acquisition.UpperConfidenceBound(kappa=2.5) # kappa is a dial s.t. higher kappa means higher unknwon/less-safe point to acquire next 

# optimizer = BayesianOptimization(
#     f=black_box_function,
#     pbounds=pbounds,
#     acquisition_function=acq, # optional param - default is UCB
#     verbose=2, #verbose=0 (silent); verbose=1 (only new max print); verbose=2 (print table row at every new step)
#     random_state=1 #every time u run program, it will pick same 'random points' during 
# )

# optimizer.maximize(
#     init_points=2, # num of random points to observe
#     n_iter=3 # num of acquisitioned points to observe
# )











