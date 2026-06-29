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
    for file_path in tsv_files_toCheck:
        trial_num = 1
        file_name = os.path.basename(file_path)
        print(f"\nMeasuring displacement for: {file_name}")
        print(f"Trial: {trial_num}")

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

        print(f"d = {d} millimeters\n")
        fitness.append(d)

        return fitness

def get_actual_rpms(csv_files_tocheck):
    """input a list of csv files from spvvvectr and outputs the gait configs for each trial as a list within a list"""
    gait_configs = []
    print("working so far bruh")
    #print(csv_files_tocheck)
    for file_path in csv_files_tocheck:
        file_name = os.path.basename(file_path)
        print(f"getting inputs for: {file_name}")

        df = pd.read_csv(file_path, delimiter=',')
        df = df[['S1_Target_RPM', 'S2_Target_RPM', 'S3_Target_RPM']]

        gait_configs.append([float(df['S1_Target_RPM'].max()), float(df['S2_Target_RPM'].max()), float(df['S3_Target_RPM'].max())]) # getting .max() of each one because there may be points in trial where rpm=0
        return gait_configs
    
def get_vectors(qualisys_path, csv_path):
    """Parses the data folder to get label and feature vectors.

    Args:
        qualisys_path (str): The directory path containing the Qualisys TSV data files.
        csv_path (str): The directory path containing the SPVVVECTR CSV data files.
    
    Returns:
        tuple: A tuple containing:
            - label (numpy.ndarray): The array of displacements.
            - feature_vector (numpy.ndarray): The array of rpm configs for SPVVVECTR.
    """

    # common file naming schemes
    file_pattern_tsv = os.path.join(qualisys_path, 'SPVVVECTR_test_*.tsv')
    file_pattern_csv = os.path.join(csv_path, 'SPVVVECTR_data_*.csv')

    # list of file paths in both folders
    tsv_files = glob.glob(file_pattern_tsv) 
    csv_files = glob.glob(file_pattern_csv)

    # get label [d1, d2, ..., dn] & feature vector [[x1, y1, z1], [x2, y2, z2], ..., [xn, yn, zn]]
    label = calculate_displacements(tsv_files)
    feature_vector = get_actual_rpms(csv_files)

    # translate both into np arrays 
    feature_vector = np.array(feature_vector)
    label = np.array(label)

    return label, feature_vector

def main():
    # paths for files
    qualisys_path = '/Users/mirajpar/Documents/SPVVVECTR/data/tsv_data'
    csv_path = '/Users/mirajpar/Documents/SPVVVECTR/data/csv-files'
    label, feature_vector = get_vectors(qualisys_path, csv_path)



    # NEXT STEPS:
    # 1. run several manuel physical trials to fill up feature and label vector 
    # 2. implement bayesian optimizer 
    # 3. pray ts works

    



if __name__ == "__main__":
    main()
