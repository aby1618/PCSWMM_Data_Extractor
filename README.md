# SWMM Data Extractor

This Python script creates a graphical user interface (GUI) application for extracting data from SWMM (Storm Water Management Model) output files and exporting it to Excel.

## Key Features

- **GUI Framework**: Utilizes the `tkinter` library for a user-friendly interface.
- **File Selection**: Allows users to select `.OUT` and Excel files.
- **Data Extraction**: Reads node/conduit/subcatchment names from Excel and extracts relevant data from SWMM output.
- **Error Handling**: Catches exceptions and displays error messages.
- **Export Functionality**: Compiles results into a DataFrame and exports them to a new Excel file.
