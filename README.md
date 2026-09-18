# PCSWMM Data Extractor

A lightweight desktop utility for batch-extracting node results from multiple SWMM / PCSWMM `.OUT` files.

## v0.1

Version 0.1 introduces a refreshed desktop interface and a simple PowerShell launch workflow while preserving the original extraction and visualization logic.

### What it does

- Select multiple SWMM / PCSWMM `.OUT` files.
- Load node names from an Excel file containing a `Name` column.
- Extract ranked peaks, minimum values, or custom nth maximum/minimum values.
- Export results to Excel, CSV, or TXT.
- Use the existing visualization tools for hydrograph review and comparison.

## Run from PowerShell

Clone or download the repository, then open PowerShell in the project folder and run:

```powershell
.\run.ps1
```

On first run, the launcher creates a local `.venv` folder and installs the required Python packages. Future launches reuse that environment.

If PowerShell blocks local scripts, you can launch it for the current session with:

```powershell
powershell -ExecutionPolicy Bypass -File .\run.ps1
```

## Project structure

- `pcswmm_data_extractor.py` — modern v0.1 desktop interface.
- `data_Extraction.py` — original extraction and visualization implementation.
- `run.ps1` — PowerShell launcher and local environment setup.
- `requirements.txt` — Python dependencies.
- `CHANGELOG.md` — version notes.

## Input requirements

The node-list Excel file must contain a column named `Name`.

## Development direction

v0.1 intentionally keeps the proven extraction logic in place and focuses on desktop usability. A future release can separate the processing engine from the GUI and package the application as a standalone Windows executable.
