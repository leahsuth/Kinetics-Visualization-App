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

```
├── AUTHORS.md                                Lists authors of this repo
├── Dockerfile                                Defines the base environment, installs dependencies, and sets the working directory to build the application
├── README.md                                 Project overview
├── Welcome.py                                Configures the application homepage
├── assets                                    Contains image files used within application
│   ├── Initial_input.png                     Instructions for Initial Input page
│   ├── Kinetics.png                          Instructions for Kinetics page
│   ├── Merck_Logo.png                        Company logo
│   └── Unit_Conversions.png                  Instructions for Unit Conversions page
├── build_image.sh                            Builds the application
├── data                                      Sample datafiles
│   ├── Example_Data_SpiroXantPhos.csv
│   ├── NB-0123-0005_Cat_Loading_Conditions.csv
│   ├── NB-0123-0005_Cat_Loading_Conditions.xlsx
│   ├── NB-0123-0005_Cat_Loading_Data.csv
│   ├── NB-0123-0005_Cat_Loading_Data.xlsx
│   └── NB-0123-0005_Cat_Loading_Initial_Rates.xlsx
├── dataset_with_loading_data.csv             Sample datafile
├── docker-compose.yml                        Standardizes application environment
├── index.css                                 Configures buttons used within application
├── interactive.sh                            Allows users to input commands
├── pages
│   ├── Initial_Input.py                      Configures the Initial Input page of application
│   ├── Kinetics.py                           Configures the Kinetics page of application
│   ├── Utilities.py                          Configures the Unit Conversions page of application
├── requirements.txt                          Contains libaries
├── run_image.sh                              Runs the application
├── src
│   ├── __init__.py
│   ├── figures
│   │   ├── __pycache__
│   │   │   ├── graph_preprocessed_data.cpython-310.pyc
│   │   │   └── graph_xl.cpython-310.pyc
│   │   ├── graph_csv.py
│   │   ├── graph_preprocessed_data.py
│   │   └── graph_xl.py
│   ├── page_styling
│   │   ├── __pycache__
│   │   │   ├── plate_selector.cpython-310.pyc
│   │   │   ├── plate_selector.cpython-312.pyc
│   │   │   ├── rate_information.cpython-310.pyc
│   │   │   ├── report_generator.cpython-310.pyc
│   │   │   └── welcome_page.cpython-310.pyc
│   │   ├── html
│   │   │   ├── __pycache__
│   │   │   │   ├── input_page_markdown.cpython-310.pyc
│   │   │   │   └── input_page_markdown.cpython-312.pyc
│   │   │   └── input_page_markdown.py
│   │   ├── plate_selector.py
│   │   ├── rate_information.py
│   │   ├── report_generator.py
│   │   ├── upload_files
│   │   │   ├── __pycache__
│   │   │   │   ├── file_uploader_buttons.cpython-310.pyc
│   │   │   │   └── file_uploader_buttons.cpython-312.pyc
│   │   │   └── file_uploader_buttons.py
│   │   ├── utilities_page
│   │   │   ├── concentration.py
│   │   │   ├── dilution.py
│   │   │   └── unit_conversion.py
│   │   └── welcome_page.py
│   ├── parsing
│   │   ├── __pycache__
│   │   │   ├── add_loading_data_info.cpython-310.pyc
│   │   │   ├── parse_file_type.cpython-310.pyc
│   │   │   ├── parsing_cat_loading_conditions.cpython-310.pyc
│   │   │   ├── parsing_data.cpython-310.pyc
│   │   │   ├── parsing_hplc_files.cpython-310.pyc
│   │   │   ├── parsing_initial_input.cpython-310.pyc
│   │   │   ├── plotting_process.cpython-310.pyc
│   │   │   ├── process_preprocessed_data.cpython-310.pyc
│   │   │   └── standardize.cpython-310.pyc
│   │   ├── add_loading_data_info.py
│   │   ├── input_page
│   │   │   ├── __pycache__
│   │   │   │   ├── helpers.cpython-310.pyc
│   │   │   │   ├── helpers.cpython-312.pyc
│   │   │   │   └── plate_setup.cpython-310.pyc
│   │   │   ├── helpers.py
│   │   │   └── plate_setup.py
│   │   ├── parse_file_type.py
│   │   ├── parsing_cat_loading_conditions.py
│   │   ├── parsing_data.py
│   │   ├── parsing_hplc_files.py
│   │   ├── plotting_process.py
│   │   ├── process_preprocessed_data.py
│   │   └── standardize.py
│   ├── regression
│   │   ├── __pycache__
│   │   │   └── rate_calculation.cpython-310.pyc
│   │   └── rate_calculation.py
│   └── utils
│       ├── __pycache__
│       │   ├── png_utils.cpython-310.pyc
│       │   └── png_utils.cpython-312.pyc
│       ├── png_utils.py
│       └── utilities_page.py
└── tests
    ├── conftest.py
    ├── initial_rate_tests.py
    ├── test_graphs.py
    └── test_parsing_data.py
```




