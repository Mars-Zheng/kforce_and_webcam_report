# KForce + Webcam Automated Report System

This repo integrates KForce data and webcam video to generate automatic visual reports.  
You can try with the files in the `example_files` folder.

## Features

- Webcam video recording and annotation  
- Squat stiffness analysis using nonlinear ODE  
- Auto-classification (linear, U, S-type)  
- Generates CSV + visual summaries  

## Files Interpretation with Practice Tips

### `start.py`

It is for recording videos with middle line in the window and three operational buttons.

- First, connect your computer with a webcam, then run `start.py`.
- Second, calibrate your webcam.
- Third, let one subject stand in the center of the screen. You may consider using calibration materials for better precision.
- Press `'r'` to record, `'s'` to stop, `'q'` to quit.
- Then you can start your task protocol.

---

### `video_editor.py`

This script provides an interactive tool for editing and annotating recorded videos.

**Functions include:**

- Frame-by-frame video playback with scrollbar  
- Drawing horizontal/vertical lines and calculating angles  
- Frame clipping and saving segments  
- Screenshot capture and image overlay fusion  
- Custom shortcuts for standard views (e.g., upper/lower/balance frames)

**Tips:**

- Left-click: draw lines and mark angle points  
- Right-click: draw horizontal/vertical reference lines  
- `r`: mark start frame  
- `s`: mark stop frame  
- `w`: export video clip  
- `1`, `2`: capture two images and perform exposure fusion  
- `p`: save current frame (e.g., `143025.jpg`)  
- `!` → `vd_upper_1.jpg`, `@` → `vd_upper_2.jpg`, `#` → `vd_upper_3.jpg`  
- `$`, `%`, `^` → `vd_lower_1.jpg`, `vd_lower_2.jpg`, `vd_lower_3.jpg`  
- `&`, `*` → `vd_balance_open_1.jpg`, `vd_balance_open_2.jpg`  
- `(`, `)` → `vd_balance_close_1.jpg`, `vd_balance_close_2.jpg`  
- `m`: toggle centerline  
- `l`: enter ruler mode (mark 2 points + enter distance)  
- `c`: clear annotations  
- `q` or `ESC`: quit  

---

### `basic_10_squat_stiffness.py`

This script processes KForce Squat Advanced Analysis CSV data for **10 squat movements** to evaluate lower limb stiffness.

**Functions include:**

- Load and parse CSV with header skipping  
- Apply Butterworth filter to quaternion (x, y, z, w)  
- Convert quaternion to Cartesian displacement, velocity, and acceleration (z-axis)  
- Identify valid squats via phase angle (Hilbert transform)  
- Standardize displacement, velocity, acceleration  
- Fit 3 regression models:
  - Linear  
  - Inverted-U (3rd-order)  
  - S-shaped (4th-order)  
- Auto-generate:
  - `output_<filename>.csv`  
  - `summary_<filename>.csv`  
  - `stiffness_graph_<model>.png`  
- GUI interface using `tkinter`  

---

### `advence_45_squat_stiffness.py`

This script processes **45 consecutive squats** and evaluates stiffness across three fatigue stages.

**Functions include:**

- Same preprocessing as `basic_10_squat_stiffness.py`  
- Segment cycles into:
  - Early stage (1–15)
  - Middle stage (16–30)
  - Late stage (31–45)  
- Fit same 3 regression models for each stage  
- Auto-generate:
  - `output_<filename>.csv`  
  - `summary_<filename>.csv`  
- GUI interface using `tkinter`

---

### `new_gen_Report_20241203版.py`

This script generates a full PowerPoint report (`MXPT_report_基礎型_20241203版.pptx`) by extracting images from four KForce PDF reports.

**Functions include:**

- Prompt user to select PDFs in this order:
  1. Upper limb test  
  2. Lower limb test  
  3. Eyes-open balance test  
  4. Eyes-closed balance test  

- Extract and crop images from specific pages  
- Replace matching placeholder shapes in PowerPoint  
- Embed:
  - 6 upper limb figures (`kf_*.jpg`, `vd_*.jpg`)  
  - 6 lower limb figures  
  - 4 balance figures (open/closed)  
- Automatically insert `stiffness_graph_*.png` if found  
- Clean up temp image files  
- Save updated PowerPoint in-place

---




## Installation
```bash
pip install -r requirements.txt
```
