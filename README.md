# JMeter Report Analyzer and Comparer

A Streamlit web application for analyzing and comparing JMeter HTML Dashboard Reports. This tool helps you parse and visualize key metrics from JMeter reports, and compare performance metrics between different test runs.

## Project Structure

```
jmeter-report-generator/
├── src/
│   ├── __init__.py
│   ├── app.py                 # Main Streamlit application
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── file_handling.py   # ZIP extraction and file operations
│   │   └── table_parsing.py   # HTML table parsing utilities
│   └── comparison/
│       ├── __init__.py
│       ├── endpoint_comparison.py    # Endpoint stats comparison
│       ├── aggregate_comparison.py   # Aggregate metrics comparison
│       └── error_comparison.py       # Error statistics comparison
├── tests/                     # Test directory (to be implemented)
├── requirements.txt           # Project dependencies
├── README.md                  # Project documentation
└── .gitignore                # Git ignore rules
```

## Features

- **Single Report Analysis**: View and analyze tables from a single JMeter report
- **Report Comparison**: Compare specific tables between two JMeter reports
- **Multiple Table Types**: Supports analysis of:
  - Endpoint-wise Stats
  - Aggregate Metrics Summary
  - Errors
- **Export Options**: Download comparison results in Excel and Markdown formats

## Installation

1. Clone this repository
2. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Run the Streamlit application:
   ```bash
   streamlit run src/app.py
   ```

2. The application will open in your default web browser

3. Choose between two modes:
   - **Single Report Analysis**: Upload a single JMeter report ZIP file to view its tables
   - **Report Comparison**: Upload two JMeter report ZIP files to compare specific tables

4. For report comparison:
   - Upload both reports
   - Select the table type you want to compare
   - Click "Compare Reports"
   - View the comparison results and download them in your preferred format

## Input Requirements

- The application expects ZIP files containing JMeter HTML Dashboard Reports
- Each ZIP file should contain an `index.html` file and associated resources
- The reports should be generated using JMeter's Dashboard Report feature

## Output Formats

- **Excel (.xlsx)**: Tabular format suitable for further analysis in spreadsheet software
- **Markdown (.md)**: Text-based format suitable for documentation and version control

## Error Handling

The application includes comprehensive error handling for:
- Invalid ZIP files
- Missing index.html
- Missing or malformed tables
- Comparison of incompatible reports

## Development

The project is structured to be easily maintainable and extensible:

- `src/utils/`: Contains utility functions for file handling and table parsing
- `src/comparison/`: Contains comparison logic for different types of metrics
- `src/app.py`: Main Streamlit application that orchestrates the functionality

To add new features:
1. Add new utility functions in the appropriate module under `src/utils/`
2. Add new comparison functions in `src/comparison/`
3. Update the main application in `src/app.py` to use the new functionality

## License

This project is open source and available under the MIT License. 