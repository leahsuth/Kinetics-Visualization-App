# DRE Kinetic Modeling Web App 

A containerized Streamlit web application designed to automate visualization and preliminary analysis of High Performance Liquid Chromatography (HPLC) kinetics data.

## Project Purpose
This application aims to:
- Automate parsing of HPLC output data
- Standardize kinetic data visualization
- Reduce manual Excel-based processing
- Provide interactive plotting for data analysis
Currently supports CSV mock data files. Pipeline expansion to additional file formats is in progress.

The application runs inside a Podman container to ensure consistent execution across environments.

## Getting Started

### Dependencies

The following packages are installed within the container:
- pandas
- streamlit
- seaborn
- matplotlib
- plotly

Container runtime:
- Podman

## System Requirements

- Podman installed and running
- Port 8501 available

### Running: Opening Streamlit UI

This program requires Podman to run. To view the current UI, run the following commands:
1. Navigate to project directory 
```bash
cd MERCK-1-26-Team-main
```

2. Build podman image 
```bash
./build_image.sh
```

3. Run container 
```bash
./run_image.sh
```

4. Open in Browser: http://localhost:8501

### Running : Using Streamlit

To view functionality in Streamlit:
1. Navigate to the Kinetics Page
2. Upload the mock CSV file: `Example_Data_SpiroXantPhos.csv`
3. Select:
- A sample (left panel)
- One or more analytes
4. Hover over graph points to view:
- Time
- Concentration
- Analyte identity
5. Click the camera icon in the top-right of the graph to download as PNG

## Roadmap/Future Work
- Add initial rate calculations
- Expand to handle other file formats, including Excel files with multiple sheets
- Implement database storage for experiment tracking
