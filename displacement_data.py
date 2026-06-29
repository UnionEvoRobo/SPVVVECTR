import glob 
import os
import pandas as pd
import numpy as np
import math

# TODO: next make matrix that has input parameters and output displacement: [x, y, z, d]
path = '/Users/mirajpar/Documents/SPVVVECTR/qualisys_tsv_data'
file_pattern = os.path.join(path, 'SPVVVECTR_test_*.tsv')
tsv_files = glob.glob(file_pattern) # list of file paths in 'qualisys_tsv_data'

def calculate_displacements(tsv_files_toCheck):
    """input a list of tsv mocap files (from qualisys) and output displacement for each trial as arr"""
    fitness = []
    # append displacement_i from trial_i to fitness vector 
    for file_path in tsv_files:
        file_name = os.path.basename(file_path)
        print(f"\nMeasuring displacement for: {file_name}")

        df = pd.read_csv(file_path, skiprows=range(0, 13), delimiter='\t')
        df = df[['top-strut X', 'Y', 'Z']].iloc[[0, -1]] # get only 1st and last row of desired cols

        x1 = df.iloc[0, 0]
        y1 = df.iloc[0, 1]
        z1 = df.iloc[0, 2]

        x2 = df.iloc[1,0]
        y2 = df.iloc[1,1]
        z2 = df.iloc[1,2]

        d = math.sqrt((float(x2) - float(x1))**2 + (float(y2) - float(y1))**2 + (float(z2) - float(z1))**2)
        d = float(f"{d:.4f}"[:-1])

        print(f"d = {d}\n")
        fitness.append(d)

        return fitness

def main():
    path = '/Users/mirajpar/Documents/SPVVVECTR/qualisys_tsv_data'
    file_pattern = os.path.join(path, 'SPVVVECTR_test_*.tsv')
    tsv_files = glob.glob(file_pattern) # list of file paths in 'qualisys_tsv_data'
    fitness = calculate_displacements(tsv_files)
    print(fitness)

main()
