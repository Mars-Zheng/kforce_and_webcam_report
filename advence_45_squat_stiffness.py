import numpy as np
import pandas as pd
import math
from scipy.fft import fft, ifft, fftfreq
import statsmodels.api as sm
from scipy.signal import hilbert, butter, filtfilt
from io import BytesIO
import tkinter as tk
import os
from tkinter import filedialog, messagebox
from matplotlib.colors import LinearSegmentedColormap




def load_csv_data(file_path, skiprows1):
    try:
        df = pd.read_csv(file_path, skiprows=skiprows1, header=None)
        if not df.empty:
            new_column_names = ['time', 'col1_left', 'col2_left', 'col3_left', 'col4_left', 'pass_1',
                                'col1_right', 'col2_right', 'col3_right', 'col4_right', 'pass_2',
                                'x', 'y', 'z', 'w'] + ['q'] * (df.shape[1] - 15)
            df.columns = new_column_names[:df.shape[1]]
            columns_to_keep = ['time', 'col1_left', 'col2_left', 'col3_left', 'col4_left',
                               'col1_right', 'col2_right', 'col3_right', 'col4_right',
                               'x', 'y', 'z', 'w']
            df = df[columns_to_keep]
            print("First 5 rows of the dataset:\n", df.head())

            # Add force columns
            df['left_force'] = df[['col1_left', 'col2_left', 'col3_left', 'col4_left']].sum(axis=1)
            df['right_force'] = df[['col1_right', 'col2_right', 'col3_right', 'col4_right']].sum(axis=1)
            df.dropna(inplace=True)
            return df
        else:
            messagebox.showerror("Error", "CSV file is empty!")
            return None
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load CSV file: {str(e)}")
        return None
# Function to apply the Butterworth filter
def apply_lowpass_filter(data, cutoff, fs, order=5):
    nyquist = 0.5 * fs
    normal_cutoff = cutoff / nyquist
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    return filtfilt(b, a, data)

# Quaternion multiplication function
def quaternion_multiply(q1, q2):
    w1, x1, y1, z1 = q1
    w2, x2, y2, z2 = q2
    return np.array([
        w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2,
        w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2,
        w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
        w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2
    ])
    
def process_data_in_csv(df):
    fs = 200  # Sampling frequency (Hz)
    cutoff = 2.8  # Desired cutoff frequency for low-pass filter (Hz)
    order = 5  # Filter order

    # Apply low-pass filter to x, y, z, w
    x = df['x']
    y = df['y']
    z = df['z']
    w = df['w']

    x_filtered = apply_lowpass_filter(x, cutoff, fs, order)
    y_filtered = apply_lowpass_filter(y, cutoff, fs, order)
    z_filtered = apply_lowpass_filter(z, cutoff, fs, order)
    w_filtered = apply_lowpass_filter(w, cutoff, fs, order)

    # Store filtered data in the DataFrame
    df['x_filtered'] = x_filtered
    df['y_filtered'] = y_filtered
    df['z_filtered'] = z_filtered
    df['w_filtered'] = w_filtered

    # Quaternion rotation calculations
    angle_process = np.arccos(w_filtered)
    angle = 2 * angle_process
    sin_theta_half = np.sqrt(1 - w_filtered**2)
    df['axis_x'] = x_filtered / sin_theta_half
    df['axis_y'] = y_filtered / sin_theta_half
    df['axis_z'] = z_filtered / sin_theta_half
    return df


# Function to rotate a point using quaternion rotation
def rotate_point_with_quaternion(qx, qy, qz, qw, point):
    point_quat = np.array([0, point[0], point[1], point[2]])
    q = np.array([qw, qx, qy, qz])
    q_conjugate = np.array([qw, -qx, -qy, -qz])
    p1 = quaternion_multiply(q, point_quat)
    p2 = quaternion_multiply(p1, q_conjugate)
    return p2[1:]



def calculate_cartesian_coordination(df):
    # Rotate the points
    start_point = np.array([1, 0, 0])
    rotated_points = np.array([rotate_point_with_quaternion(row['x_filtered'], row['y_filtered'], row['z_filtered'], row['w_filtered'], start_point)
                            for _, row in df.iterrows()])

    # Extract the rotated x, y, z values
    rotated_x = rotated_points[:, 0]
    rotated_y = rotated_points[:, 1]
    rotated_z = rotated_points[:, 2]

    df['x_after_rotate'] = rotated_x
    df['y_after_rotate'] = rotated_y
    df['z_after_rotate'] = rotated_z

    # Calculate velocities and accelerations
    z_abs_velocity = np.abs(np.diff(rotated_z)) / 0.005
    z_abs_velocity = np.append(z_abs_velocity, 0)  # Add last element to match length
    df['z_abs_velocity'] = z_abs_velocity

    z_velocity = np.diff(rotated_z) / 0.005
    z_velocity = np.append(z_velocity, 0)  # Add last element to match length
    df['z_velocity'] = z_velocity

    z_acceleration = np.diff(z_velocity) / 0.005
    z_acceleration = np.append(z_acceleration, 0)  # Add last element to match length
    df['z_acceleration'] = z_acceleration

    # Filtered data based on velocity threshold
    threshold = 0.4
    first_valid_index = df[df["z_abs_velocity"] > threshold].index[0]
    df_filtered = df.loc[first_valid_index:].reset_index(drop=True)
    return df_filtered
    

# Phase calculation functions
def calculate_instantaneous_phase(signal):
    signal_min = np.min(signal)
    signal_max = np.max(signal)
    signal_as_angle = 2 * (signal - signal_min) / (signal_max - signal_min) - 1
    analytic_signal = hilbert(signal_as_angle)
    real_part = np.real(analytic_signal)
    imaginary_part = np.imag(analytic_signal)
    instantaneous_phase = np.unwrap(np.arctan2(imaginary_part, real_part))
    instantaneous_phase_deg = np.degrees(instantaneous_phase)
    instantaneous_phase_deg = (instantaneous_phase_deg + 180) % 360 - 180

    corrected_phase_deg = np.zeros(len(instantaneous_phase_deg))
    corrected_phase_deg[0] = instantaneous_phase_deg[0]

    for i in range(1, len(instantaneous_phase_deg)):
        current_value = corrected_phase_deg[i - 1]
        next_value = instantaneous_phase_deg[i]
        if current_value < 0 and next_value > 0 and (next_value - current_value) > 180:
            corrected_phase_deg[i] = next_value - 360
        elif current_value > 0 and next_value < 0 and (current_value - next_value) > 180:
            corrected_phase_deg[i] = next_value + 360
        else:
            corrected_phase_deg[i] = next_value
    return corrected_phase_deg - 180

def phase_identify(instantaneous_phase_deg):
    phase_identify_array = np.zeros(len(instantaneous_phase_deg))
    phase_identify_array[0] = -100
    a = -100
    for i in range(1, len(instantaneous_phase_deg) - 1):
        current_value = instantaneous_phase_deg[i]
        next_value = instantaneous_phase_deg[i + 1]
        if current_value > 0 and next_value < 0:
            phase_identify_array[i] = -a
            a = -a
        elif current_value < 0 and next_value > 0:
            phase_identify_array[i] = -a
            a = -a
    return phase_identify_array

def out_put_csv(df_filtered, input_file_path):
    df_filtered = df_filtered.dropna(subset=['z_after_rotate'])
    z2 = df_filtered['z_after_rotate']
    phase_angle = calculate_instantaneous_phase(z2)
    identified = phase_identify(phase_angle)
    df_filtered['phase angle'] = phase_angle
    df_filtered['identified'] = identified
    
    fs = 200  # Sampling frequency (Hz)
    cutoff = 2.8  # Desired cutoff frequency for low-pass filter (Hz)
    order = 5  # Filter order
    

    # Extract 'z_after_rotate', 'z_velocity', and 'z_acceleration' from the filtered DataFrame
    zp = df_filtered['z_after_rotate']
    zv = df_filtered['z_velocity']
    za = df_filtered['z_acceleration']

    # Apply low-pass filtering with the given parameters
    zp_filtered = apply_lowpass_filter(zp, cutoff, fs, order)
    zv_filtered = apply_lowpass_filter(zv, cutoff, fs, 8)
    za_filtered = apply_lowpass_filter(za, cutoff, fs, 8)

    # Standardization of zp
    min_zp_filtered = np.min(zp_filtered)
    max_zp_filtered = np.max(zp_filtered)
    zp_std = ((zp - min_zp_filtered) / (max_zp_filtered - min_zp_filtered)) * 2 - 1

    # Standardization of zv
    abs_zv_filtered = np.abs(zv_filtered)
    max_abs_zv_filtered = np.max(abs_zv_filtered)
    print(max_abs_zv_filtered)
    zv_std = zv_filtered / max_abs_zv_filtered
    print(np.max(np.abs(zv_std)))

    # Standardization of za
    abs_za_filtered = np.abs(za_filtered)
    max_abs_za_filtered = np.max(abs_za_filtered)
    print(max_abs_za_filtered)
    za_std = za_filtered / max_abs_za_filtered
    print(np.max(np.abs(za_std)))

    # Assign standardized values to the DataFrame using .loc to avoid the warning
    df_filtered.loc[:, "zp_std"] = zp_std
    df_filtered.loc[:, "zv_std"] = zv_std
    df_filtered.loc[:, "za_std"] = za_std

    # Calculate cubic of zp_std and assign to a new column
    zp_std_quadratic = zp_std ** 2
    df_filtered.loc[:, "zp_std_quadratic"] = zp_std_quadratic
    zp_std_cubic = zp_std ** 3
    df_filtered.loc[:, "zp_std_cubic"] = zp_std_cubic
    zp_std_quartic = zp_std ** 4
    df_filtered.loc[:, "zp_std_quartic"] = zp_std_quartic
    
    df_filtered.loc[:, "cycle"] = (df_filtered["identified"] == -100).cumsum()


    base_name = os.path.splitext(os.path.basename(input_file_path))[0]
    # Create the new output file name
    output_file_name = f"output_{base_name}.csv"

    # Save the DataFrame to the new CSV file
    df_filtered.to_csv(output_file_name, index=False)
    print(f"Output saved as: {output_file_name}")
    return df_filtered

def calculate_linear_regression(df, x_column, v_column, x_column_quadratic, x_column_cubic, x_column__quartic, a_column):
    """
    Perform multiple linear regressions for 3 models across different cycle stages and return the results as a DataFrame.
    """
    try:
        # Define cycle stages
        cycle_stages = {
            'early': (1, 15),
            'middle': (16, 30),
            'last': (31, df["cycle"].max())
        }
        
        all_results = []

        # Loop through each cycle stage
        for stage_name, (start, end) in cycle_stages.items():
            # Filter data for the current cycle stage
            stage_df = df[(df["cycle"] >= start) & (df["cycle"] <= end)]
            
            # Skip if the stage_df is empty
            if stage_df.empty:
                continue
            
            # Model 1: Linear regression with x_column and v_column
            x1 = stage_df[[x_column, v_column]]
            y1 = stage_df[a_column]
            model1 = sm.OLS(y1, x1).fit()
            
            # Model 2: Linear regression with cubic term
            x2 = stage_df[[x_column, v_column, x_column_cubic]]
            y2 = stage_df[a_column]
            model2 = sm.OLS(y2, x2).fit()
            
            # Model 3: Linear regression with quadratic, cubic, and quartic terms
            x3 = stage_df[[x_column, v_column, x_column_quadratic, x_column_cubic, x_column__quartic]]
            y3 = stage_df[a_column]
            model3 = sm.OLS(y3, x3).fit()
            
            # Collect results for the current stage
            results = [
                {
                    'stage': stage_name,
                    'model': 'Model 1',
                    'r_squared': model1.rsquared,
                    'coefficients': model1.params.to_dict(),
                    'p_values': model1.pvalues.to_dict()
                },
                {
                    'stage': stage_name,
                    'model': 'Model 2',
                    'r_squared': model2.rsquared,
                    'coefficients': model2.params.to_dict(),
                    'p_values': model2.pvalues.to_dict()
                },
                {
                    'stage': stage_name,
                    'model': 'Model 3',
                    'r_squared': model3.rsquared,
                    'coefficients': model3.params.to_dict(),
                    'p_values': model3.pvalues.to_dict()
                }
            ]
            all_results.extend(results)
        
        # Convert all results into a DataFrame
        results_df = pd.DataFrame(all_results)
        return results_df

    except Exception as e:
        print(f"Regression failed: {str(e)}")
        return pd.DataFrame([{'error': str(e)}])


def save_csvs(df, summary, input_file_path):
    base_name = os.path.splitext(os.path.basename(input_file_path))[0]
    df_filtered=out_put_csv(df, input_file_path)
    summary_file = f"summary_{base_name}.csv"
    # Save summary CSV
    summary_df = summary
    summary_df.to_csv(summary_file, index=False)
    print(f"Summary saved as: {summary_file}")
    return df_filtered





# GUI setup
root = tk.Tk()
root.title("CSV File Processor")
root.geometry("400x300")
selected_file_path = tk.StringVar()
skip_rows_value = tk.StringVar()  # Store user input for skipped rows

def select_file():
    file_path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
    if file_path:
        selected_file_path.set(file_path)

def process_file():
    """Process the selected file and generate output and summary CSVs."""
    file_path = selected_file_path.get()
    if not file_path:
        messagebox.showwarning("Warning", "No file selected!")
        return

    try:
        skip_rows = int(skip_rows_value.get())  # Get user input for skipped rows
        df = load_csv_data(file_path, skip_rows)  # Pass skip_rows to load_csv_data
        if df is not None:
            df_processed = process_data_in_csv(df)
            df_filtered = calculate_cartesian_coordination(df_processed)
            df_filtered2 = out_put_csv(df_filtered, file_path)

            # Perform regression without intercept
            summary = calculate_linear_regression(
                df_filtered2, 
                'zp_std', 
                'zv_std', 
                'zp_std_quadratic',
                'zp_std_cubic',
                'zp_std_quartic',
                'za_std'
            )

            # Save both CSVs
            save_csvs(df_filtered2, summary, file_path)

            messagebox.showinfo("Success", "Processing completed! Output and summary saved.")
    except ValueError:
        messagebox.showerror("Error", "Please enter a valid integer for skipped rows.")
    except Exception as e:
        messagebox.showerror("Error", f"Processing failed: {str(e)}")

# GUI elements
label = tk.Label(root, text="Select a CSV file:")
label.pack(pady=10)

file_path_display = tk.Entry(root, textvariable=selected_file_path, width=50)
file_path_display.pack(padx=10, pady=5)

select_button = tk.Button(root, text="Browse", command=select_file)
select_button.pack(pady=5)

skip_label = tk.Label(root, text="Enter number of rows to skip:")
skip_label.pack(pady=5)

skip_entry = tk.Entry(root, textvariable=skip_rows_value, width=10)
skip_entry.pack(pady=5)

process_button = tk.Button(root, text="Process and Save", command=process_file)
process_button.pack(pady=10)

root.mainloop()