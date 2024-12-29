import tkinter as tk
from tkinter import filedialog, messagebox

import pandas as pd
from swmm_api import SwmmOutput

# Initialize main application window
root = tk.Tk()
root.title("SWMM Data Extractor")
root.geometry("400x300")
root.configure(bg="#2E2E2E")

# Global variables
out_file_path = ""
excel_file_path = ""


def browse_out_file():
    global out_file_path
    out_file_path = filedialog.askopenfilename(filetypes=[("OUT files", "*.out")])
    if out_file_path:
        out_file_label.config(text=f"Selected .OUT File: {out_file_path}")


def browse_excel_file():
    global excel_file_path
    excel_file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx;*.xls")])
    if excel_file_path:
        excel_file_label.config(text=f"Selected Excel File: {excel_file_path}")


def extract_data():
    if not out_file_path or not excel_file_path:
        messagebox.showerror("Error", "Please select both .OUT and Excel files.")
        return

    try:
        # Read Excel file to get node/conduit/subcatchment names
        df = pd.read_excel(excel_file_path)

        # Assuming column with names is 'Name' (you can change this accordingly)
        names = df['Name'].tolist()

        # Open .OUT file using swmm-api
        output = SwmmOutput(out_file_path)

        results = []

        # Extract data for each name provided in the Excel file
        for name in names:
            try:
                # Fetch attributes for nodes/conduits/subcatchments
                attributes = output.get_part('node', name,
                                             'total_inflow')  # Change to output.get_conduit(name) or
                # output.get_subcatchment(name) as needed

                if attributes is not None:
                    max_flow = attributes.max()
                    results.append({'Name': name, 'Max Flow': max_flow})
                else:
                    results.append({'Name': name, 'Max Flow': 'Not Found'})
            except Exception as e:
                results.append({'Name': name, 'Max Flow': f'Error: {str(e)}'})

        # Convert results to DataFrame and export to new Excel file
        results_df = pd.DataFrame(results)
        output_excel_path = filedialog.asksaveasfilename(defaultextension=".xlsx",
                                                         filetypes=[("Excel files", "*.xlsx;*.xls")])
        if output_excel_path:
            results_df.to_excel(output_excel_path, index=False)
            messagebox.showinfo("Success", f"Data exported successfully to {output_excel_path}")

    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {str(e)}")


# UI Elements
out_file_label = tk.Label(root, text="No .OUT File Selected", bg="#2E2E2E", fg="white")
out_file_label.pack(pady=10)

browse_out_button = tk.Button(root, text="Browse .OUT File", command=browse_out_file)
browse_out_button.pack(pady=5)

excel_file_label = tk.Label(root, text="No Excel File Selected", bg="#2E2E2E", fg="white")
excel_file_label.pack(pady=10)

browse_excel_button = tk.Button(root, text="Browse Excel File", command=browse_excel_file)
browse_excel_button.pack(pady=5)

extract_button = tk.Button(root, text="Extract Data", command=extract_data)
extract_button.pack(pady=20)

# Start the application
root.mainloop()

