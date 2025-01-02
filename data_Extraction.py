import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import logging
import pandas as pd
from swmm_api import SwmmOutput
from scipy.signal import find_peaks
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

# Logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define a consistent color palette
BG_COLOR = "#2E2E2E"
FG_COLOR = "white"
BUTTON_COLOR = "#4A4A4A"
HOVER_COLOR = "#6A6A6A"

class SWMMApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SWMM Data Extraction Tool")
        self.root.geometry("900x600")
        self.root.configure(bg=BG_COLOR)

        self.out_file_paths = []
        self.excel_file_path = ""
        self.max_options = ["1st Max", "2nd Max", "3rd Max", "4th Max", "5th Max", "Minimum"]
        self.selected_options = {option: tk.BooleanVar(value=False) for option in self.max_options}
        self.nth_max_var = tk.BooleanVar(value=False)
        self.nth_min_var = tk.BooleanVar(value=False)
        self.nth_max_value_var = tk.IntVar(value=1)
        self.nth_min_value_var = tk.IntVar(value=1)
        self.create_widgets()

    def create_widgets(self):
        # File selection widgets
        self.out_file_label = tk.Label(self.root, text="No .OUT File Selected", bg=BG_COLOR, fg=FG_COLOR)
        self.out_file_label.grid(row=0, column=1, padx=10, pady=10)

        tk.Button(self.root, text="Browse .OUT Files", command=self.browse_out_files, bg=BUTTON_COLOR, fg=FG_COLOR).grid(row=0, column=0, padx=10, pady=10)

        tk.Button(self.root, text="Show Selected Files", command=self.show_selected_files, bg=BUTTON_COLOR, fg=FG_COLOR).grid(row=0, column=2, padx=10, pady=10)

        self.excel_file_label = tk.Label(self.root, text="No Excel File Selected", bg=BG_COLOR, fg=FG_COLOR)
        self.excel_file_label.grid(row=1, column=1, padx=10, pady=10)

        tk.Button(self.root, text="Browse Excel File", command=self.browse_excel_file, bg=BUTTON_COLOR, fg=FG_COLOR).grid(row=1, column=0, padx=10, pady=10)

        # Checkboxes for max/min options
        checkbox_frame = tk.Frame(self.root, bg=BG_COLOR)
        checkbox_frame.grid(row=2, column=0, columnspan=3, pady=10)

        for i, option in enumerate(self.max_options):
            tk.Checkbutton(checkbox_frame, text=option, variable=self.selected_options[option], bg=BG_COLOR, fg=FG_COLOR, selectcolor=BUTTON_COLOR).grid(row=i // 3, column=i % 3, padx=5, pady=5)

        # Inline configuration for nth maximum and nth minimum
        nth_frame = tk.Frame(self.root, bg=BG_COLOR)
        nth_frame.grid(row=3, column=0, columnspan=3, pady=10)

        # Nth Maximum
        tk.Checkbutton(nth_frame, text="Enable nth Maximum", variable=self.nth_max_var, bg=BG_COLOR, fg=FG_COLOR, selectcolor=BUTTON_COLOR).grid(row=0, column=0, padx=5, pady=5)
        tk.Label(nth_frame, text="n =", bg=BG_COLOR, fg=FG_COLOR).grid(row=0, column=1, padx=5, pady=5)
        tk.Spinbox(nth_frame, from_=1, to=100, textvariable=self.nth_max_value_var, bg=BUTTON_COLOR, fg=FG_COLOR, width=5).grid(row=0, column=2, padx=5, pady=5)

        # Nth Minimum
        tk.Checkbutton(nth_frame, text="Enable nth Minimum", variable=self.nth_min_var, bg=BG_COLOR, fg=FG_COLOR, selectcolor=BUTTON_COLOR).grid(row=1, column=0, padx=5, pady=5)
        tk.Label(nth_frame, text="n =", bg=BG_COLOR, fg=FG_COLOR).grid(row=1, column=1, padx=5, pady=5)
        tk.Spinbox(nth_frame, from_=1, to=100, textvariable=self.nth_min_value_var, bg=BUTTON_COLOR, fg=FG_COLOR, width=5).grid(row=1, column=2, padx=5, pady=5)

        # Export format selection
        export_format_label = tk.Label(self.root, text="Select Export Format:", bg=BG_COLOR, fg=FG_COLOR)
        export_format_label.grid(row=4, column=0, padx=10, pady=10)

        self.export_format_var = tk.StringVar(value="Excel")
        ttk.OptionMenu(self.root, self.export_format_var, "Excel", "Excel", "CSV", "TXT").grid(row=4, column=1, padx=10, pady=10)

        # Visualization button
        tk.Button(self.root, text="Visualize Data", command=self.open_visualization_popup, bg=BUTTON_COLOR, fg=FG_COLOR).grid(row=5, column=1, padx=10, pady=10)

        # Extraction button
        tk.Button(self.root, text="Extract Data", command=self.start_extraction, bg=BUTTON_COLOR, fg=FG_COLOR).grid(row=5, column=0, padx=10, pady=10)

        # Progress bar
        self.progress_bar = ttk.Progressbar(self.root, mode='indeterminate')
        self.progress_bar.grid(row=6, column=0, columnspan=3, pady=10, padx=10)

    def browse_out_files(self):
        self.out_file_paths = filedialog.askopenfilenames(filetypes=[("OUT files", "*.out")])
        self.out_file_label.config(text=f"{len(self.out_file_paths)} .OUT files selected" if self.out_file_paths else "No .OUT File Selected")

    def show_selected_files(self):
        if not self.out_file_paths:
            messagebox.showinfo("Selected Files", "No .OUT files have been selected.")
        else:
            file_list = "\n".join(self.out_file_paths)
            messagebox.showinfo("Selected Files", file_list)

    def browse_excel_file(self):
        self.excel_file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx;*.xls")])
        self.excel_file_label.config(text="Excel file selected" if self.excel_file_path else "No Excel File Selected")

    def start_extraction(self):
        if not self.out_file_paths or not self.excel_file_path:
            messagebox.showerror("Error", "Please select both .OUT and Excel files.")
            return

        thread = threading.Thread(target=self.extract_data)
        thread.start()

    def extract_data(self):
        self.progress_bar.start()

        try:
            selected_metrics = [key for key, var in self.selected_options.items() if var.get()]
            nth_max_value = self.nth_max_value_var.get()
            nth_min_value = self.nth_min_value_var.get()
            enable_nth_max = self.nth_max_var.get()
            enable_nth_min = self.nth_min_var.get()

            if not selected_metrics and not enable_nth_max and not enable_nth_min:
                messagebox.showerror("Error", "Please select at least one metric or enable nth max/min options.")
                return

            logging.info("Starting data extraction")

            df = pd.read_excel(self.excel_file_path)
            node_names = df['Name'].tolist()
            results = []

            for out_file in self.out_file_paths:
                output = SwmmOutput(out_file)
                out_file_name = out_file.split('/')[-1]

                for node_name in node_names:
                    try:
                        inflow_data = output.get_part('node', node_name, 'total_inflow')

                        if inflow_data is not None:
                            inflow_list = inflow_data.tolist() if isinstance(inflow_data, np.ndarray) else inflow_data
                            peaks, _ = find_peaks(inflow_list)
                            peak_values = [inflow_list[i] for i in peaks]
                            sorted_peaks = sorted(peak_values, reverse=True)

                            result = {"Name": node_name, ".OUT file name": out_file_name}

                            for metric in selected_metrics:
                                if "Max" in metric:
                                    index = int(metric.split(" ")[0][0]) - 1
                                    result[metric] = sorted_peaks[index] if index < len(sorted_peaks) else "Not Available"
                                elif metric == "Minimum":
                                    result[metric] = min(inflow_list) if inflow_list else "Not Available"

                            # Nth value processing
                            if enable_nth_max:
                                result[f"{nth_max_value}th Max"] = sorted_peaks[nth_max_value - 1] if nth_max_value <= len(sorted_peaks) else "Not Available"
                            if enable_nth_min:
                                result[f"{nth_min_value}th Min"] = sorted(inflow_list)[nth_min_value - 1] if nth_min_value <= len(inflow_list) else "Not Available"

                            results.append(result)

                        else:
                            results.append({"Name": node_name, ".OUT file name": out_file_name, "Status": "Data Not Found"})

                    except Exception as e:
                        logging.error(f"Error processing node {node_name}: {e}")
                        results.append({"Name": node_name, ".OUT file name": out_file_name, "Error": str(e)})

            results_df = pd.DataFrame(results)
            results_df = results_df.set_index(["Name", ".OUT file name"]).stack().reset_index()
            results_df.columns = ["Name", ".OUT file name", "Objective", "Outcome"]

            output_format = self.export_format_var.get()
            filetypes = []
            extension = ""

            if output_format == "Excel":
                extension = ".xlsx"
                filetypes = [("Excel files", "*.xlsx")]
            elif output_format == "CSV":
                extension = ".csv"
                filetypes = [("CSV files", "*.csv")]
            elif output_format == "TXT":
                extension = ".txt"
                filetypes = [("Text files", "*.txt")]

            save_path = filedialog.asksaveasfilename(defaultextension=extension, filetypes=filetypes)

            if save_path:
                if output_format == "Excel":
                    results_df.to_excel(save_path, index=False)
                elif output_format == "CSV" or output_format == "TXT":
                    results_df.to_csv(save_path, index=False)

                messagebox.showinfo("Success", f"Data saved to {save_path}")

        except Exception as e:
            logging.error(f"An error occurred during extraction: {e}")
            messagebox.showerror("Error", f"An error occurred: {e}")

        finally:
            self.progress_bar.stop()

    def open_visualization_popup(self):
        if not self.out_file_paths:
            messagebox.showerror("Error", "No .OUT files selected for visualization.")
            return

        popup = tk.Toplevel(self.root)
        popup.title("Select Graphs to Visualize")
        popup.configure(bg=BG_COLOR)

        file_frame = tk.Frame(popup, bg=BG_COLOR)
        file_frame.pack(pady=5)

        tk.Label(file_frame, text=".OUT Files:", bg=BG_COLOR, fg=FG_COLOR).grid(row=0, column=0, padx=5, pady=5)

        self.file_vars = {}
        for i, file_path in enumerate(self.out_file_paths):
            var = tk.BooleanVar(value=False)
            self.file_vars[file_path] = var
            tk.Checkbutton(file_frame, text=file_path, variable=var, bg=BG_COLOR, fg=FG_COLOR, selectcolor=BUTTON_COLOR).grid(row=i + 1, column=0, sticky="w")

        select_all_files_var = tk.BooleanVar(value=False)

        def toggle_select_all_files():
            for var in self.file_vars.values():
                var.set(select_all_files_var.get())

        tk.Checkbutton(file_frame, text="Select All", variable=select_all_files_var, command=toggle_select_all_files, bg=BG_COLOR, fg=FG_COLOR, selectcolor=BUTTON_COLOR).grid(row=len(self.out_file_paths) + 1, column=0, sticky="w")

        # Select nodes with checkboxes
        node_frame = tk.Frame(popup, bg=BG_COLOR)
        node_frame.pack(pady=5)

        tk.Label(node_frame, text="Nodes:", bg=BG_COLOR, fg=FG_COLOR).grid(row=0, column=0, padx=5, pady=5)

        self.node_vars = {}
        try:
            df = pd.read_excel(self.excel_file_path)
            nodes = df["Name"].tolist()
            for i, node in enumerate(nodes):
                var = tk.BooleanVar(value=False)
                self.node_vars[node] = var
                tk.Checkbutton(node_frame, text=node, variable=var, bg=BG_COLOR, fg=FG_COLOR, selectcolor=BUTTON_COLOR).grid(row=i + 1, column=0, sticky="w")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load nodes from Excel: {e}")

        select_all_nodes_var = tk.BooleanVar(value=False)

        def toggle_select_all_nodes():
            for var in self.node_vars.values():
                var.set(select_all_nodes_var.get())

        tk.Checkbutton(node_frame, text="Select All", variable=select_all_nodes_var, command=toggle_select_all_nodes, bg=BG_COLOR, fg=FG_COLOR, selectcolor=BUTTON_COLOR).grid(row=len(nodes) + 1, column=0, sticky="w")

        # Visualize Button
        def visualize():
            selected_files = [file for file, var in self.file_vars.items() if var.get()]
            selected_nodes = [node for node, var in self.node_vars.items() if var.get()]

            if not selected_files or not selected_nodes:
                messagebox.showerror("Error", "Please select at least one .OUT file and one node.")
                return

            try:
                # Prepare graph data
                graphs = []
                for file_path in selected_files:
                    output = SwmmOutput(file_path)
                    for node in selected_nodes:
                        inflow_data = output.get_part("node", node, "total_inflow")
                        if inflow_data is not None and not inflow_data.empty:
                            graphs.append((inflow_data, node, file_path))
                        else:
                            graphs.append((None, node, file_path))

                if not graphs:
                    messagebox.showerror("Error", "No data available for the selected nodes and files.")
                    return

                # Create a Tkinter window for navigation
                graph_window = tk.Toplevel(self.root)
                graph_window.title("Visualization - All Selected Graphs")

                # Create Matplotlib figure
                fig, ax = plt.subplots(figsize=(10, 6))
                canvas = FigureCanvasTkAgg(fig, master=graph_window)
                canvas.draw()
                canvas.get_tk_widget().pack()

                # Add Matplotlib toolbar
                toolbar_frame = tk.Frame(graph_window)
                toolbar_frame.pack()
                toolbar = NavigationToolbar2Tk(canvas, toolbar_frame)
                toolbar.update()

                # State to track current graph index
                current_index = tk.IntVar(value=0)

                def update_graph():
                    ax.clear()
                    inflow_data, node, file_path = graphs[current_index.get()]
                    if inflow_data is not None:
                        ax.plot(inflow_data, label=f"{node} ({file_path.split('/')[-1]})")
                        ax.set_title(f"Node: {node}, File: {file_path.split('/')[-1]}")
                        ax.set_xlabel("Time")
                        ax.set_ylabel("Flow")
                        ax.legend()
                    else:
                        ax.set_title(f"No data for Node: {node}, File: {file_path.split('/')[-1]}")
                        ax.axis("off")
                    canvas.draw()

                def next_graph():
                    if current_index.get() < len(graphs) - 1:
                        current_index.set(current_index.get() + 1)
                        update_graph()

                def previous_graph():
                    if current_index.get() > 0:
                        current_index.set(current_index.get() - 1)
                        update_graph()

                # Navigation buttons
                nav_frame = tk.Frame(graph_window, bg=BG_COLOR)
                nav_frame.pack(pady=10)

                tk.Button(nav_frame, text="Previous", command=previous_graph, bg=BUTTON_COLOR, fg=FG_COLOR).grid(row=0, column=0, padx=5)
                tk.Button(nav_frame, text="Next", command=next_graph, bg=BUTTON_COLOR, fg=FG_COLOR).grid(row=0, column=1, padx=5)

                # Display the first graph
                update_graph()

            except Exception as e:
                messagebox.showerror("Error", f"Visualization error: {e}")

        tk.Button(popup, text="Visualize", command=visualize, bg=BUTTON_COLOR, fg=FG_COLOR).pack(pady=10)

    def display_graph(self, inflow_data, node_name, file_name):
        graph_window = tk.Toplevel(self.root)
        graph_window.title(f"Visualization - {node_name}")

        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(inflow_data, label=f"{node_name} ({file_name})")
        ax.set_title(f"Inflow Data for Node {node_name}")
        ax.set_xlabel("Time")
        ax.set_ylabel("Flow")
        ax.legend()

        canvas = FigureCanvasTkAgg(fig, master=graph_window)
        canvas.draw()
        canvas.get_tk_widget().pack()

# Start application
if __name__ == "__main__":
    root = tk.Tk()
    app = SWMMApp(root)
    root.mainloop()
