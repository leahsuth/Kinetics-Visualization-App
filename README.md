# DRE Kinetic Modeling Web App 

A containerized Streamlit web application designed to automate visualization and preliminary analysis of High Performance Liquid Chromatography (HPLC) kinetics data.

## Project Purpose
This application aims to:
- Automate parsing of HPLC output data
- Standardize kinetic data visualization
- Calculate & visualize initial rate of reaction
- Reduce manual Excel-based processing
- Provide interactive plotting for data analysis
Supports .csv, .xlsx, and pre-processed datafiles

The application runs inside a Podman container to ensure consistent execution across environments.

## Getting Started

### Dependencies

The following packages are installed within the container:
- pandas
- streamlit
- seaborn
- matplotlib
- plotly
- openpyxl
- pytest
- numpy
- scikit-learn
- cairosvg
- Pillow
- fpdf2
  
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

```
├── AUTHORS.md                                  Lists authors of this repo
├── Dockerfile                                  Defines the base environment, installs dependencies, and sets the working directory to build the application
├── README.md                                   Project overview
├── Welcome.py                                  Configures the application homepage
├── assets                                      Contains image files used within application
│   ├── Initial_input.png                       Instructions for Initial Input page
│   ├── Kinetics.png                            Instructions for Kinetics page
│   ├── Merck_Logo.png                          Company logo
│   └── Unit_Conversions.png                    Instructions for Unit Conversions page
├── build_image.sh                              Builds the application
├── data                                        Sample datafiles
│   ├── Example_Data_SpiroXantPhos.csv
│   ├── NB-0123-0005_Cat_Loading_Conditions.csv
│   ├── NB-0123-0005_Cat_Loading_Conditions.xlsx
│   ├── NB-0123-0005_Cat_Loading_Data.csv
│   ├── NB-0123-0005_Cat_Loading_Data.xlsx
│   └── NB-0123-0005_Cat_Loading_Initial_Rates.xlsx
├── dataset_with_loading_data.csv               Sample datafile
├── docker-compose.yml                          Standardizes application environment
├── index.css                                   Configures buttons used within application
├── interactive.sh                              Allows users to input commands
├── pages                                       Webpage Directory
│   ├── Initial_Input.py                        Configures the Initial Input page of application
│   ├── Kinetics.py                             Configures the Kinetics page of application
│   ├── Utilities.py                            Configures the Unit Conversions page of application
├── requirements.txt                            Contains libaries
├── run_image.sh                                Runs the application
├── src                                         Source code directory
│   ├── __init__.py                             Sets up directory
│   ├── figures                                 Graph configuration directory
│   │   ├── graph_csv.py                        Configures Kinetics graphs from .csv files
│   │   ├── graph_preprocessed_data.py          Configures Kinetics graphs from preprocessed datafiles
│   │   └── graph_xl.py                         Configures Kinetics graphs from .xlsx files
│   ├── page_styling                            Page styling directory
│   │   ├── html                                HTML directory for Initial Input page
│   │   │   └── input_page_markdown.py          Defines functions that call st.markdown
│   │   ├── plate_selector.py                   Formats well plates and for Initial Input page
│   │   ├── rate_information.py                 Calculates initial rate
│   │   ├── report_generator.py                 Generates reports on Kinetics page
│   │   ├── upload_files                        Directory for file uploading functions
│   │   │   └── file_uploader_buttons.py        Configures buttons to upload experimental conditions & HPLC data on Initial Input page
│   │   ├── utilities_page                      Directory for Unit Conversion page
│   │   │   ├── concentration.py                Calls concentration widget UI
│   │   │   ├── dilution.py                     (Pending) 
│   │   │   └── unit_conversion.py              (Pending)
│   │   └── welcome_page.py                     Configures UI for Welcome page
│   ├── parsing                                 Directory for parsing datafiles
│   │   ├── add_loading_data_info.py            Loads information from Initial Input file into a dataframe
│   │   ├── input_page                          Directory for datafile parsing on Initial Input page
│   │   │   ├── helpers.py                      Parses uploaded datafile
│   │   │   └── plate_setup.py                  Formats parsed reaction rows for generation of plate map & Kinetics graphs
│   │   ├── parse_file_type.py                  Enables user to upload .csv and .xlsx files
│   │   ├── parsing_cat_loading_conditions.py   
│   │   ├── parsing_data.py
│   │   ├── parsing_hplc_files.py
│   │   ├── plotting_process.py
│   │   ├── process_preprocessed_data.py
│   │   └── standardize.py
│   ├── regression
│   │   └── rate_calculation.py
│   └── utils
│       ├── png_utils.py
│       └── utilities_page.py
└── tests
    ├── conftest.py
    ├── initial_rate_tests.py
    ├── test_graphs.py
    └── test_parsing_data.py
```




