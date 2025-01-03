import os
import json
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, colorchooser
from datetime import datetime
from bokeh.plotting import figure
from bokeh.io import save, export_png
from bokeh.resources import CDN
from bokeh.embed import file_html
from bokeh.models import Legend
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
                output = self.parse_swmm_out_file(out_file)
                if output is None:
                    # Skip this .OUT file or record an error
                    results.append({"Name": None, ".OUT file name": out_file, "Error": "Could not parse this file"})
                    continue

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

    def parse_swmm_out_file(self, file_path):
        """
        Centralized method to parse a SWMM .OUT file using SwmmOutput.
        Returns the SwmmOutput object or None on error.
        """
        try:
            out = SwmmOutput(file_path)
            return out
        except Exception as e:
            logging.error(f"[ERROR] Could not parse {file_path}: {e}")
            return None

    def load_swmm_timeseries(self, out_file, node_name):
        """
        Loads the total_inflow time series for the given node from the specified .OUT file.
        Returns a Pandas DataFrame with DateTimeIndex and a single column named `node_name`,
        or None if the data is unavailable or there's an error.
        """
        try:
            # We can either call parse_swmm_out_file or directly do SwmmOutput
            # If parse_swmm_out_file returns None on error, handle that:
            output_obj = self.parse_swmm_out_file(out_file)
            if output_obj is None:
                return None

            inflow_data = output_obj.get_part("node", node_name, "total_inflow")
            if inflow_data is not None and not inflow_data.empty:
                df = inflow_data.to_frame(name=node_name)
                # 1) Check if df.index is already datetime-like
                if not pd.api.types.is_datetime64_any_dtype(df.index):
                    # Let's assume the index is in hours from the start of simulation
                    # or from some reference zero. If it's minutes, adjust accordingly.
                    # If we have a known start date (like aggregator logic sets),
                    # use that; otherwise, pick a fallback.

                    fallback_start = datetime(2020, 1, 1)  # or any date that you prefer
                    base_datetime = self.overlay_data_storage.get(out_file, {}).get("start_datetime") or fallback_start

                    # Convert numeric index -> actual timestamps
                    # Here we interpret each index entry as hours offset from 'base_datetime'
                    numeric_hours = df.index.astype(float)  # ensure float, just in case
                    df.index = [base_datetime + pd.Timedelta(hours=h) for h in numeric_hours]
                return df
            else:
                return None

        except Exception as e:
            logging.error(f"Error loading timeseries for node {node_name} in {out_file}: {e}")
            return None

    def open_visualization_popup(self):
        """
        Opens a popup for selecting which .OUT files and nodes to visualize,
        then gives buttons to do Aggregated Visualization or Comparative Overlay.
        """
        if not self.out_file_paths or not self.excel_file_path:
            messagebox.showerror("Error", "Please select both .OUT and Excel files for visualization.")
            return

        popup = tk.Toplevel(self.root)
        popup.title("Select Graphs to Visualize")
        popup.configure(bg=BG_COLOR)

        tk.Label(popup, text="Select Nodes and Files to Visualize", bg=BG_COLOR, fg=FG_COLOR).pack(pady=10)

        # -----------------------------------------------------------------
        # 1) File checkboxes with Select All
        # -----------------------------------------------------------------
        file_frame = tk.Frame(popup, bg=BG_COLOR)
        file_frame.pack(pady=5)

        tk.Label(file_frame, text=".OUT Files:", bg=BG_COLOR, fg=FG_COLOR).grid(row=0, column=0, padx=5, pady=5)

        self.file_vars = {}
        for i, file_path in enumerate(self.out_file_paths):
            var = tk.BooleanVar(value=False)
            self.file_vars[file_path] = var
            tk.Checkbutton(file_frame, text=file_path, variable=var, bg=BG_COLOR, fg=FG_COLOR,
                           selectcolor=BUTTON_COLOR).grid(row=i + 1, column=0, sticky="w")

        select_all_files_var = tk.BooleanVar(value=False)

        def toggle_select_all_files():
            for var in self.file_vars.values():
                var.set(select_all_files_var.get())

        tk.Checkbutton(file_frame, text="Select All", variable=select_all_files_var, command=toggle_select_all_files,
                       bg=BG_COLOR, fg=FG_COLOR, selectcolor=BUTTON_COLOR).grid(row=len(self.out_file_paths) + 1,
                                                                                column=0, sticky="w")

        # -----------------------------------------------------------------
        # 2) Node checkboxes with Select All
        # -----------------------------------------------------------------
        node_frame = tk.Frame(popup, bg=BG_COLOR)
        node_frame.pack(pady=5)

        tk.Label(node_frame, text="Nodes:", bg=BG_COLOR, fg=FG_COLOR).grid(row=0, column=0, padx=5, pady=5)

        self.node_vars = {}
        try:
            df = pd.read_excel(self.excel_file_path)
            nodes = df['Name'].tolist()
            for i, node in enumerate(nodes):
                var = tk.BooleanVar(value=False)
                self.node_vars[node] = var
                tk.Checkbutton(node_frame, text=node, variable=var, bg=BG_COLOR, fg=FG_COLOR,
                               selectcolor=BUTTON_COLOR).grid(row=i + 1, column=0, sticky="w")

            select_all_nodes_var = tk.BooleanVar(value=False)

            def toggle_select_all_nodes():
                for var in self.node_vars.values():
                    var.set(select_all_nodes_var.get())

            tk.Checkbutton(node_frame, text="Select All", variable=select_all_nodes_var,
                           command=toggle_select_all_nodes, bg=BG_COLOR, fg=FG_COLOR, selectcolor=BUTTON_COLOR).grid(
                row=len(nodes) + 1, column=0, sticky="w")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load nodes from Excel: {e}")

        # -----------------------------------------------------------------
        # 3) Buttons for aggregated and comparative visualization
        # -----------------------------------------------------------------

        # Tooltip helper
        def show_tooltip(message):
            tooltip = tk.Toplevel(self.root)
            tooltip.title("Information")
            tk.Label(tooltip, text=message, bg=BG_COLOR, fg=FG_COLOR, padx=10, pady=10).pack()
            tk.Button(tooltip, text="Close", command=tooltip.destroy, bg=BUTTON_COLOR, fg=FG_COLOR).pack(pady=5)

        # A frame to hold aggregator and comparative visualization buttons
        action_frame = tk.Frame(popup, bg=BG_COLOR)
        action_frame.pack(pady=10)

        # ------------------ AGGREGATED VISUALIZATION --------------------
        def aggregated_visualization():
            selected_files = [file for file, var in self.file_vars.items() if var.get()]
            selected_nodes = [node for node, var in self.node_vars.items() if var.get()]

            if not selected_files or not selected_nodes:
                messagebox.showerror("Error", "Please select at least one .OUT file and one node.")
                return

            try:
                fig, ax = plt.subplots(figsize=(10, 6))
                for file_path in selected_files:
                    output = SwmmOutput(file_path)
                    for node in selected_nodes:
                        inflow_data = output.get_part("node", node, "total_inflow")
                        if inflow_data is not None and not inflow_data.empty:
                            ax.plot(inflow_data, label=f"{node} ({file_path.split('/')[-1]})")

                ax.set_title("Aggregated Inflow Data")
                ax.set_xlabel("Time")
                ax.set_ylabel("Flow")
                ax.legend()

                graph_window = tk.Toplevel(self.root)
                graph_window.title("Aggregated Visualization")

                toolbar_frame = tk.Frame(graph_window)
                toolbar_frame.pack()

                canvas = FigureCanvasTkAgg(fig, master=graph_window)
                canvas.draw()
                canvas.get_tk_widget().pack()

                toolbar = NavigationToolbar2Tk(canvas, toolbar_frame)
                toolbar.update()

            except Exception as e:
                messagebox.showerror("Error", f"Visualization error: {e}")

        agg_frame = tk.Frame(action_frame, bg=BG_COLOR)
        agg_frame.pack(side=tk.LEFT, padx=10)

        tk.Button(agg_frame, text="Aggregated Visualization", command=aggregated_visualization,
                  bg=BUTTON_COLOR, fg=FG_COLOR).pack(side=tk.LEFT)
        tk.Button(agg_frame, text="?", command=lambda: show_tooltip(
            "Aggregated Visualization shows combined data trends for all selected files and nodes."),
                  bg=BG_COLOR, fg=FG_COLOR).pack(side=tk.LEFT, padx=5)

        # --------------------- MATPLOTLIB VISUALIZE ---------------------
        def visualize():
            """
            This is the simpler 'visualize' button that plots all selected
            nodes/files in a single sequential view (one at a time).
            """
            selected_files = [file for file, var in self.file_vars.items() if var.get()]
            selected_nodes = [node for node, var in self.node_vars.items() if var.get()]

            if not selected_files or not selected_nodes:
                messagebox.showerror("Error", "Please select at least one .OUT file and one node.")
                return

            try:
                # Prepare graph data
                graphs = []
                for file_path in selected_files:
                    output = self.parse_swmm_out_file(file_path)
                    if output is None:
                        # If parse failed, still append placeholders
                        for node in selected_nodes:
                            graphs.append((None, node, file_path))
                        continue

                    for node in selected_nodes:
                        inflow_data = output.get_part("node", node, "total_inflow")
                        if inflow_data is not None and not inflow_data.empty:
                            graphs.append((inflow_data, node, file_path))
                        else:
                            graphs.append((None, node, file_path))

                if not graphs:
                    messagebox.showerror("Error", "No data available for the selected nodes and files.")
                    return

                # Create a new window for navigation
                graph_window = tk.Toplevel(self.root)
                graph_window.title("Visualization - All Selected Graphs")

                # Matplotlib figure
                fig, ax = plt.subplots(figsize=(10, 6))
                canvas = FigureCanvasTkAgg(fig, master=graph_window)
                canvas.draw()
                canvas.get_tk_widget().pack()

                # Toolbar
                toolbar_frame = tk.Frame(graph_window)
                toolbar_frame.pack()
                toolbar = NavigationToolbar2Tk(canvas, toolbar_frame)
                toolbar.update()

                # Index for current graph
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

                nav_frame = tk.Frame(graph_window, bg=BG_COLOR)
                nav_frame.pack(pady=10)

                tk.Button(nav_frame, text="Previous", command=previous_graph,
                          bg=BUTTON_COLOR, fg=FG_COLOR).grid(row=0, column=0, padx=5)
                tk.Button(nav_frame, text="Next", command=next_graph,
                          bg=BUTTON_COLOR, fg=FG_COLOR).grid(row=0, column=1, padx=5)

                # Display the first graph
                update_graph()

            except Exception as e:
                messagebox.showerror("Error", f"Visualization error: {e}")

        tk.Button(popup, text="Visualize", command=visualize,
                  bg=BUTTON_COLOR, fg=FG_COLOR).pack(pady=10)

        # ---------------- COMPARATIVE VISUALIZATION BUTTONS -------------
        comp_frame = tk.Frame(action_frame, bg=BG_COLOR)
        comp_frame.pack(side=tk.RIGHT, padx=10)

        tk.Button(comp_frame, text="Comparative Visualization",
                  command=self.comparative_overlay_visualization,  # calls the method below
                  bg=BUTTON_COLOR, fg=FG_COLOR).pack(side=tk.LEFT)

        tk.Button(comp_frame, text="?",
                  command=lambda: show_tooltip("Comparative Visualization displays overlayed graphs "
                                               "for selected files and nodes."),
                  bg=BG_COLOR, fg=FG_COLOR).pack(side=tk.LEFT, padx=5)

    def comparative_overlay_visualization(self):
        """
        Opens a new window that allows overlay-based comparative visualization
        of multiple .OUT files for multiple nodes (one node at a time) using Bokeh.
        """

        # 1. Create Toplevel window
        popup = tk.Toplevel(self.root)
        popup.title("Comparative Overlay Visualization")
        popup.configure(bg=BG_COLOR)

        # Helper data structures:
        # We'll store time-shifts, colors, and dataframes for each .OUT file
        # in a dictionary. Key: file_path
        self.overlay_data_storage = {}

        # We also store user-chosen node names in a list
        # (We'll rely on your existing "self.node_vars" if available,
        #  or you can create a new selection UI. For now, let's assume
        #  we already have selected_nodes.)
        selected_nodes = [node for node, var in self.node_vars.items() if var.get()]
        if not selected_nodes:
            tk.messagebox.showerror("Error", "No nodes selected for comparative overlay.")
            popup.destroy()
            return

        # For storing color presets in a JSON file
        self.color_preset_path = "color_presets.json"
        if not os.path.exists(self.color_preset_path):
            with open(self.color_preset_path, 'w') as f:
                json.dump({}, f)

        # Load existing color presets
        with open(self.color_preset_path, 'r') as f:
            try:
                self.color_presets = json.load(f)
            except:
                self.color_presets = {}

        # Collect selected files
        selected_files = [f for f, var in self.file_vars.items() if var.get()]
        if not selected_files:
            tk.messagebox.showerror("Error", "No .OUT files selected for comparative overlay.")
            popup.destroy()
            return

        # 2. Prepare a frame to list each file, pick color, set shift
        file_frame = tk.Frame(popup, bg=BG_COLOR)
        file_frame.pack(pady=5, fill='x')

        tk.Label(file_frame, text="Comparative Overlay Configuration", bg=BG_COLOR, fg=FG_COLOR,
                 font=("Arial", 12, "bold")).pack(pady=5)

        # We'll store references to color and shift entries for each file
        self.file_config_entries = {}

        # Pre-load data & create a DataFrame with DateTimeIndex for each file
        # Also handle downsampling if > 1 million points
        for out_file in selected_files:
            output_obj = self.parse_swmm_out_file(out_file)
            if output_obj is None:
                tk.messagebox.showwarning("Warning", f"Could not parse {out_file}")
                continue

            node_dataframes = {}
            for node_name in selected_nodes:
                df = self.load_swmm_timeseries(out_file, node_name)
                if df is not None:
                    # (A) Convert numeric index -> Datetime (if needed)
                    if not pd.api.types.is_datetime64_any_dtype(df.index):
                        # Example assumption: index in hours
                        fallback_start = datetime(2020, 1, 1)
                        numeric_hours = df.index.astype(float)
                        df.index = [fallback_start + pd.Timedelta(hours=h) for h in numeric_hours]

                    # (B) Downsample if large
                    if len(df) > 1_000_000:
                        tk.messagebox.showinfo(
                            "Performance Note",
                            f"Data in {out_file} for node {node_name} is large. Downsampling..."
                        )
                        df = df.iloc[::10, :]
                    node_dataframes[node_name] = df
                else:
                    node_dataframes[node_name] = None

            # (C) Determine earliest start among loaded nodes
            valid_dfs = [ndf for ndf in node_dataframes.values() if isinstance(ndf, pd.DataFrame)]
            if valid_dfs:
                # earliest among them
                earliest_time = min(d.index[0] for d in valid_dfs)
            else:
                earliest_time = None

            # (D) Store in overlay_data_storage
            default_color = self.color_presets.get(out_file, "#000000")
            self.overlay_data_storage[out_file] = {
                "node_dfs": node_dataframes,
                "color": default_color,
                # The user might later choose to align to a brand-new date,
                # but let's store the raw earliest as "original_start_datetime"
                "original_start_datetime": earliest_time,
                # "start_datetime" will be the current alignment base
                "start_datetime": earliest_time,
                "shift_offset": pd.Timedelta(0),
            }

            # Attempt to find an earliest timestamp among loaded nodes
            valid_dfs = [ndf for ndf in node_dataframes.values() if isinstance(ndf, pd.DataFrame)]
            if valid_dfs:
                earliest_time = min(df.index[0] for df in valid_dfs)
                self.overlay_data_storage[out_file]["start_datetime"] = earliest_time
            else:
                self.overlay_data_storage[out_file]["start_datetime"] = None

        # Now create a row in file_frame for each file
        row_index = 1
        for out_file in self.overlay_data_storage.keys():
            config_frame = tk.Frame(file_frame, bg=BG_COLOR)
            config_frame.pack(pady=5, fill='x')

            tk.Label(config_frame, text=os.path.basename(out_file), bg=BG_COLOR, fg=FG_COLOR).grid(row=0, column=0,
                                                                                                   padx=5)

            # Color picker
            def pick_color_for_file(file=out_file):
                color_code = colorchooser.askcolor(title=f"Choose color for {file}")
                if color_code and color_code[1]:  # user picked something
                    self.overlay_data_storage[file]["color"] = color_code[1]
                    # Update JSON preset
                    self.color_presets[file] = color_code[1]
                    with open(self.color_preset_path, 'w') as f:
                        json.dump(self.color_presets, f)
                    # Refresh UI if needed

            color_button = tk.Button(config_frame, text="Pick Color", bg=BUTTON_COLOR, fg=FG_COLOR,
                                     command=pick_color_for_file)
            color_button.grid(row=0, column=1, padx=5)

            # Date-time entry for shifting
            # If we have a known earliest date/time, display it
            dt_label = tk.Label(config_frame, text="Align Start (YYYY-MM-DD HH:MM):", bg=BG_COLOR, fg=FG_COLOR)
            dt_label.grid(row=0, column=2, padx=5)

            dt_var = tk.StringVar()
            if self.overlay_data_storage[out_file]["start_datetime"] is not None:
                dt_var.set(str(self.overlay_data_storage[out_file]["start_datetime"]))

            dt_entry = tk.Entry(config_frame, textvariable=dt_var, width=20, bg=BUTTON_COLOR, fg=FG_COLOR)
            dt_entry.grid(row=0, column=3, padx=5)

            # Save references for later
            self.file_config_entries[out_file] = {
                "dt_var": dt_var
            }

            row_index += 1

        # 3. Node Navigation Controls (Previous / Next Node)
        navigation_frame = tk.Frame(popup, bg=BG_COLOR)
        navigation_frame.pack(pady=10)

        self.current_node_index = 0  # we start at the first node
        self.selected_nodes_list = selected_nodes

        def plot_current_node():
            """
            Plot overlay for the currently selected node index using Bokeh.
            """
            if not self.selected_nodes_list:
                tk.messagebox.showerror("Error", "No nodes selected.")
                return

            node = self.selected_nodes_list[self.current_node_index]

            # For each file, read the user-chosen alignment date from dt_var
            for file, config in self.overlay_data_storage.items():
                user_dt_str = self.file_config_entries[file]["dt_var"].get()

                # If user typed something valid, set config["start_datetime"] to that
                if config["original_start_datetime"] is not None and user_dt_str:
                    try:
                        # e.g., "2022-01-01 00:00:00"
                        user_chosen_dt = datetime.strptime(user_dt_str, "%Y-%m-%d %H:%M:%S")

                        # SHIFT = user_chosen_dt - original_start_datetime
                        # So if original was 2020-01-01, and user picks 2022-01-01,
                        # shift = 2 years
                        shift_offset = user_chosen_dt - config["original_start_datetime"]
                        config["shift_offset"] = pd.Timedelta(shift_offset)

                        # Also store that the "start_datetime" (i.e. current alignment) is user_chosen_dt
                        config["start_datetime"] = user_chosen_dt

                    except Exception as e:
                        print(f"Error parsing user_dt_str={user_dt_str}: {e}")
                        config["shift_offset"] = pd.Timedelta(0)
                        config["start_datetime"] = config["original_start_datetime"]
                else:
                    # If no user input or no original_start_datetime,
                    # revert to no shift
                    config["shift_offset"] = pd.Timedelta(0)
                    config["start_datetime"] = config["original_start_datetime"]

            # Now build the Bokeh figure
            bokeh_fig = figure(
                x_axis_type="datetime",
                width=800,  # Bokeh >= 3 uses width instead of plot_width
                height=400,
                background_fill_color="#FFFFFF",
                title=f"Overlay for Node: {node}"
            )

            legend_items = []

            # Plot each file
            for file, config in self.overlay_data_storage.items():
                node_dfs = config["node_dfs"]
                offset = config["shift_offset"]
                color = config["color"]
                df = node_dfs.get(node)
                if df is None or df.empty:
                    continue

                # Shift the index
                shifted_index = df.index + offset
                times = list(shifted_index)
                flows = df[node].tolist()

                r = bokeh_fig.line(x=times, y=flows, line_color=color, line_width=2, alpha=0.8)
                legend_items.append((os.path.basename(file), [r]))

                # (Optional) Debug print to confirm shift
                print(f"File={file}, Node={node}, OrigStart={df.index[0]}, Shift={offset}, NewStart={shifted_index[0]}")

            # Add legend
            if legend_items:
                legend = Legend(items=legend_items, location="top_left")
                bokeh_fig.add_layout(legend, 'right')

            # If we already have a display, clear it
            if hasattr(self, "bokeh_display_frame"):
                self.bokeh_display_frame.destroy()

            self.bokeh_display_frame = tk.Frame(popup, bg=BG_COLOR)
            self.bokeh_display_frame.pack(pady=10, fill='both', expand=True)

            # Show in browser or local HTML
            html_content = file_html(bokeh_fig, CDN, "Overlay")
            html_path = os.path.join(os.getcwd(), "temp_overlay.html")
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)

            import webbrowser
            webbrowser.open(f"file://{html_path}")

        def next_node():
            self.current_node_index += 1
            if self.current_node_index >= len(self.selected_nodes_list):
                self.current_node_index = 0
            plot_current_node()

        def previous_node():
            self.current_node_index -= 1
            if self.current_node_index < 0:
                self.current_node_index = len(self.selected_nodes_list) - 1
            plot_current_node()

        tk.Button(navigation_frame, text="<< Previous Node", bg=BUTTON_COLOR, fg=FG_COLOR,
                  command=previous_node).pack(side=tk.LEFT, padx=5)
        tk.Button(navigation_frame, text="Plot Current Node", bg=BUTTON_COLOR, fg=FG_COLOR,
                  command=plot_current_node).pack(side=tk.LEFT, padx=5)
        tk.Button(navigation_frame, text="Next Node >>", bg=BUTTON_COLOR, fg=FG_COLOR, command=next_node).pack(
            side=tk.LEFT, padx=5)

        # 4. Export Options
        export_frame = tk.Frame(popup, bg=BG_COLOR)
        export_frame.pack(pady=10)

        def export_html():
            # Use Bokeh's file_html to generate HTML with the current node's figure
            node = self.selected_nodes_list[self.current_node_index]
            bokeh_fig = figure(
                x_axis_type="datetime",
                title=f"Overlay for Node: {node}",
                width=1200,
                height=900
            )
            legend_items = []
            for file, config in self.overlay_data_storage.items():
                node_dfs = config["node_dfs"]
                color = config["color"]
                offset = config["shift_offset"]
                if node not in node_dfs or node_dfs[node] is None:
                    continue
                df = node_dfs[node]
                if df.empty:
                    continue

                shifted_index = df.index + offset
                times = list(shifted_index)
                flows = df[node].tolist()

                r = bokeh_fig.line(
                    x=times,
                    y=flows,
                    line_color=color,
                    line_width=2,
                    alpha=0.8
                )
                legend_items.append((os.path.basename(file), [r]))
            if legend_items:
                legend = Legend(items=legend_items, location="top_left")
                bokeh_fig.add_layout(legend, 'right')

            save_path = tk.filedialog.asksaveasfilename(defaultextension=".html",
                                                        filetypes=[("HTML files", "*.html")])
            if save_path:
                html = file_html(bokeh_fig, CDN, "Overlay Export")
                with open(save_path, 'w', encoding='utf-8') as f:
                    f.write(html)
                tk.messagebox.showinfo("Export", f"HTML Exported to {save_path}")

        def export_png_file():
            # Similar approach using bokeh export_png
            try:
                from bokeh.io import export_png
            except ImportError:
                tk.messagebox.showerror("Error",
                                        "You need to install pillow, selenium, etc. for export_png to work.")
                return

            node = self.selected_nodes_list[self.current_node_index]
            bokeh_fig = figure(
                x_axis_type="datetime",
                title=f"Overlay for Node: {node}",
                width=1200,
                height=900
            )
            legend_items = []
            for file, config in self.overlay_data_storage.items():
                node_dfs = config["node_dfs"]
                color = config["color"]
                offset = config["shift_offset"]
                if node not in node_dfs or node_dfs[node] is None:
                    continue
                df = node_dfs[node]
                if df.empty:
                    continue

                shifted_index = df.index + offset
                times = list(shifted_index)
                flows = df[node].tolist()

                r = bokeh_fig.line(x=times, y=flows, line_color=color, line_width=2, alpha=0.8)
                legend_items.append((os.path.basename(file), [r]))

            if legend_items:
                legend = Legend(items=legend_items, location="top_left")
                bokeh_fig.add_layout(legend, 'right')

            save_path = tk.filedialog.asksaveasfilename(defaultextension=".png",
                                                        filetypes=[("PNG files", "*.png")])
            if save_path:
                export_png(bokeh_fig, filename=save_path)
                tk.messagebox.showinfo("Export", f"PNG exported to {save_path}")

        tk.Button(export_frame, text="Export HTML", bg=BUTTON_COLOR, fg=FG_COLOR, command=export_html).pack(
            side=tk.LEFT, padx=5)
        tk.Button(export_frame, text="Export PNG", bg=BUTTON_COLOR, fg=FG_COLOR, command=export_png_file).pack(
            side=tk.LEFT, padx=5)

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

    # Matplotlib Toolbar Integration
    def add_toolbar(fig, graph_window):
        toolbar_frame = tk.Frame(graph_window)
        toolbar_frame.pack()
        canvas = FigureCanvasTkAgg(fig, master=graph_window)
        canvas.draw()
        canvas.get_tk_widget().pack()
        toolbar = NavigationToolbar2Tk(canvas, toolbar_frame)
        toolbar.update()

# Start application
if __name__ == "__main__":
    root = tk.Tk()
    app = SWMMApp(root)
    root.mainloop()
