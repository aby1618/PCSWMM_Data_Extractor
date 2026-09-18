from __future__ import annotations

import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import data_Extraction as legacy

APP_NAME = "PCSWMM Data Extractor"
APP_VERSION = "0.1"

COLORS = {
    "app_bg": "#0B1220",
    "surface": "#111827",
    "surface_alt": "#172033",
    "border": "#263247",
    "text": "#F8FAFC",
    "muted": "#94A3B8",
    "accent": "#38BDF8",
    "accent_hover": "#0EA5E9",
    "success": "#34D399",
}

# Keep the legacy visualization windows visually aligned with the new shell.
legacy.BG_COLOR = COLORS["app_bg"]
legacy.FG_COLOR = COLORS["text"]
legacy.BUTTON_COLOR = COLORS["surface_alt"]
legacy.HOVER_COLOR = COLORS["border"]


class ModernSWMMApp(legacy.SWMMApp):
    """Modern v0.1 UI shell around the existing extraction/visualization logic."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self._configure_theme()
        super().__init__(root)

        self.root.title(f"{APP_NAME} v{APP_VERSION}")
        self.root.geometry("1120x760")
        self.root.minsize(980, 680)
        self.root.configure(bg=COLORS["app_bg"])

    def _configure_theme(self) -> None:
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure(".", font=("Segoe UI", 10))
        style.configure("App.TFrame", background=COLORS["app_bg"])
        style.configure("Card.TFrame", background=COLORS["surface"], relief="flat")
        style.configure("CardAlt.TFrame", background=COLORS["surface_alt"], relief="flat")

        style.configure(
            "Title.TLabel",
            background=COLORS["app_bg"],
            foreground=COLORS["text"],
            font=("Segoe UI Semibold", 24),
        )
        style.configure(
            "Subtitle.TLabel",
            background=COLORS["app_bg"],
            foreground=COLORS["muted"],
            font=("Segoe UI", 10),
        )
        style.configure(
            "Section.TLabel",
            background=COLORS["surface"],
            foreground=COLORS["text"],
            font=("Segoe UI Semibold", 12),
        )
        style.configure(
            "Body.TLabel",
            background=COLORS["surface"],
            foreground=COLORS["text"],
        )
        style.configure(
            "Status.TLabel",
            background=COLORS["app_bg"],
            foreground=COLORS["muted"],
            font=("Segoe UI", 9),
        )

        style.configure(
            "Primary.TButton",
            background=COLORS["accent"],
            foreground="#062033",
            borderwidth=0,
            padding=(18, 11),
            font=("Segoe UI Semibold", 10),
        )
        style.map(
            "Primary.TButton",
            background=[("active", COLORS["accent_hover"]), ("pressed", COLORS["accent_hover"])],
            foreground=[("disabled", COLORS["muted"])],
        )

        style.configure(
            "Secondary.TButton",
            background=COLORS["surface_alt"],
            foreground=COLORS["text"],
            borderwidth=0,
            padding=(14, 9),
        )
        style.map(
            "Secondary.TButton",
            background=[("active", COLORS["border"]), ("pressed", COLORS["border"])],
        )

        style.configure(
            "Modern.TCheckbutton",
            background=COLORS["surface"],
            foreground=COLORS["text"],
            padding=(4, 5),
        )
        style.map(
            "Modern.TCheckbutton",
            background=[("active", COLORS["surface"])],
            foreground=[("disabled", COLORS["muted"])],
        )

        style.configure(
            "Modern.TCombobox",
            fieldbackground=COLORS["surface_alt"],
            background=COLORS["surface_alt"],
            foreground=COLORS["text"],
            arrowcolor=COLORS["text"],
            bordercolor=COLORS["border"],
            padding=7,
        )
        style.map(
            "Modern.TCombobox",
            fieldbackground=[("readonly", COLORS["surface_alt"])],
            foreground=[("readonly", COLORS["text"])],
        )

        style.configure(
            "Modern.Horizontal.TProgressbar",
            troughcolor=COLORS["surface_alt"],
            background=COLORS["accent"],
            bordercolor=COLORS["surface_alt"],
            lightcolor=COLORS["accent"],
            darkcolor=COLORS["accent"],
        )

        style.configure(
            "Modern.Treeview",
            background=COLORS["surface"],
            fieldbackground=COLORS["surface"],
            foreground=COLORS["text"],
            rowheight=30,
            borderwidth=0,
        )
        style.configure(
            "Modern.Treeview.Heading",
            background=COLORS["surface_alt"],
            foreground=COLORS["text"],
            relief="flat",
            font=("Segoe UI Semibold", 9),
        )
        style.map(
            "Modern.Treeview",
            background=[("selected", COLORS["accent_hover"])],
            foreground=[("selected", COLORS["text"])],
        )

    def create_widgets(self) -> None:
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=1)

        header = ttk.Frame(self.root, style="App.TFrame", padding=(28, 24, 28, 14))
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        ttk.Label(header, text=APP_NAME, style="Title.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            header,
            text="Batch-extract SWMM/PCSWMM node results from multiple .OUT files.",
            style="Subtitle.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(5, 0))

        version_badge = tk.Label(
            header,
            text=f"  v{APP_VERSION}  ",
            bg=COLORS["surface_alt"],
            fg=COLORS["accent"],
            font=("Segoe UI Semibold", 9),
            padx=8,
            pady=5,
        )
        version_badge.grid(row=0, column=1, rowspan=2, sticky="e")

        content = ttk.Frame(self.root, style="App.TFrame", padding=(28, 0, 28, 14))
        content.grid(row=1, column=0, sticky="nsew")
        content.grid_columnconfigure(0, weight=5)
        content.grid_columnconfigure(1, weight=4)
        content.grid_rowconfigure(0, weight=1)

        left = ttk.Frame(content, style="Card.TFrame", padding=22)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        left.grid_columnconfigure(0, weight=1)

        ttk.Label(left, text="1  Input files", style="Section.TLabel").grid(row=0, column=0, sticky="w")

        out_card = ttk.Frame(left, style="CardAlt.TFrame", padding=16)
        out_card.grid(row=1, column=0, sticky="ew", pady=(14, 8))
        out_card.grid_columnconfigure(0, weight=1)

        tk.Label(
            out_card,
            text="PCSWMM / SWMM output files",
            bg=COLORS["surface_alt"],
            fg=COLORS["text"],
            font=("Segoe UI Semibold", 10),
        ).grid(row=0, column=0, sticky="w")
        self.out_file_label = tk.Label(
            out_card,
            text="No .OUT files selected",
            bg=COLORS["surface_alt"],
            fg=COLORS["muted"],
            font=("Segoe UI", 9),
            anchor="w",
        )
        self.out_file_label.grid(row=1, column=0, sticky="ew", pady=(4, 10))

        out_actions = ttk.Frame(out_card, style="CardAlt.TFrame")
        out_actions.grid(row=2, column=0, sticky="w")
        ttk.Button(
            out_actions,
            text="Browse .OUT files",
            command=self.browse_out_files,
            style="Secondary.TButton",
        ).pack(side="left")
        ttk.Button(
            out_actions,
            text="Review selection",
            command=self.show_selected_files,
            style="Secondary.TButton",
        ).pack(side="left", padx=(8, 0))

        excel_card = ttk.Frame(left, style="CardAlt.TFrame", padding=16)
        excel_card.grid(row=2, column=0, sticky="ew", pady=8)
        excel_card.grid_columnconfigure(0, weight=1)

        tk.Label(
            excel_card,
            text="Node list",
            bg=COLORS["surface_alt"],
            fg=COLORS["text"],
            font=("Segoe UI Semibold", 10),
        ).grid(row=0, column=0, sticky="w")
        self.excel_file_label = tk.Label(
            excel_card,
            text="No Excel file selected",
            bg=COLORS["surface_alt"],
            fg=COLORS["muted"],
            font=("Segoe UI", 9),
            anchor="w",
        )
        self.excel_file_label.grid(row=1, column=0, sticky="ew", pady=(4, 10))
        ttk.Button(
            excel_card,
            text="Browse Excel file",
            command=self.browse_excel_file,
            style="Secondary.TButton",
        ).grid(row=2, column=0, sticky="w")

        tk.Label(
            left,
            text="The Excel input must contain a column named “Name”. Core extraction behavior is unchanged from the original tool.",
            bg=COLORS["surface"],
            fg=COLORS["muted"],
            justify="left",
            wraplength=500,
            font=("Segoe UI", 9),
        ).grid(row=3, column=0, sticky="ew", pady=(12, 0))

        right = ttk.Frame(content, style="Card.TFrame", padding=22)
        right.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        right.grid_columnconfigure(0, weight=1)

        ttk.Label(right, text="2  Extraction settings", style="Section.TLabel").grid(row=0, column=0, sticky="w")

        metrics = ttk.Frame(right, style="Card.TFrame")
        metrics.grid(row=1, column=0, sticky="ew", pady=(12, 4))
        metrics.grid_columnconfigure(0, weight=1)
        metrics.grid_columnconfigure(1, weight=1)

        for index, option in enumerate(self.max_options):
            ttk.Checkbutton(
                metrics,
                text=option,
                variable=self.selected_options[option],
                style="Modern.TCheckbutton",
            ).grid(row=index // 2, column=index % 2, sticky="w", padx=(0, 12), pady=2)

        custom = ttk.Frame(right, style="CardAlt.TFrame", padding=14)
        custom.grid(row=2, column=0, sticky="ew", pady=(10, 12))
        custom.grid_columnconfigure(1, weight=1)

        tk.Label(
            custom,
            text="Custom ranked values",
            bg=COLORS["surface_alt"],
            fg=COLORS["text"],
            font=("Segoe UI Semibold", 10),
        ).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 8))

        self._build_nth_row(custom, 1, "Nth maximum", self.nth_max_var, self.nth_max_value_var)
        self._build_nth_row(custom, 2, "Nth minimum", self.nth_min_var, self.nth_min_value_var)

        export_row = ttk.Frame(right, style="Card.TFrame")
        export_row.grid(row=3, column=0, sticky="ew", pady=(4, 0))
        export_row.grid_columnconfigure(1, weight=1)

        ttk.Label(export_row, text="Export format", style="Body.TLabel").grid(
            row=0, column=0, sticky="w", padx=(0, 12)
        )
        self.export_format_var = tk.StringVar(value="Excel")
        ttk.Combobox(
            export_row,
            textvariable=self.export_format_var,
            values=("Excel", "CSV", "TXT"),
            state="readonly",
            style="Modern.TCombobox",
            width=14,
        ).grid(row=0, column=1, sticky="ew")

        ttk.Separator(right, orient="horizontal").grid(row=4, column=0, sticky="ew", pady=18)

        actions = ttk.Frame(right, style="Card.TFrame")
        actions.grid(row=5, column=0, sticky="ew")
        actions.grid_columnconfigure(0, weight=1)
        actions.grid_columnconfigure(1, weight=1)

        self.extract_button = ttk.Button(
            actions,
            text="Extract data",
            command=self.start_extraction,
            style="Primary.TButton",
        )
        self.extract_button.grid(row=0, column=0, sticky="ew", padx=(0, 5))

        ttk.Button(
            actions,
            text="Visualize data",
            command=self.open_visualization_popup,
            style="Secondary.TButton",
        ).grid(row=0, column=1, sticky="ew", padx=(5, 0))

        self.progress_bar = ttk.Progressbar(
            right,
            mode="indeterminate",
            style="Modern.Horizontal.TProgressbar",
        )
        self.progress_bar.grid(row=6, column=0, sticky="ew", pady=(16, 0))

        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(
            self.root,
            textvariable=self.status_var,
            style="Status.TLabel",
            padding=(28, 0, 28, 16),
        ).grid(row=2, column=0, sticky="ew")

    def _build_nth_row(self, parent, row, label, enabled_var, value_var) -> None:
        tk.Checkbutton(
            parent,
            text=label,
            variable=enabled_var,
            bg=COLORS["surface_alt"],
            fg=COLORS["text"],
            activebackground=COLORS["surface_alt"],
            activeforeground=COLORS["text"],
            selectcolor=COLORS["surface"],
            highlightthickness=0,
            bd=0,
            font=("Segoe UI", 9),
        ).grid(row=row, column=0, sticky="w", pady=3)

        tk.Label(
            parent,
            text="n =",
            bg=COLORS["surface_alt"],
            fg=COLORS["muted"],
            font=("Segoe UI", 9),
        ).grid(row=row, column=1, sticky="e", padx=(10, 6))

        tk.Spinbox(
            parent,
            from_=1,
            to=100,
            textvariable=value_var,
            width=5,
            bg=COLORS["surface"],
            fg=COLORS["text"],
            buttonbackground=COLORS["surface_alt"],
            insertbackground=COLORS["text"],
            relief="flat",
            highlightthickness=1,
            highlightbackground=COLORS["border"],
            highlightcolor=COLORS["accent"],
        ).grid(row=row, column=2, sticky="e")

    def browse_out_files(self) -> None:
        selected = filedialog.askopenfilenames(
            title="Select SWMM / PCSWMM output files",
            filetypes=[("SWMM output files", "*.out"), ("All files", "*.*")],
        )
        if selected:
            self.out_file_paths = list(selected)
            count = len(self.out_file_paths)
            self.out_file_label.config(
                text=f"{count} file{'s' if count != 1 else ''} selected",
                fg=COLORS["success"],
            )
            self.status_var.set(f"Loaded {count} output file(s).")

    def browse_excel_file(self) -> None:
        selected = filedialog.askopenfilename(
            title="Select Excel node list",
            filetypes=[("Excel files", "*.xlsx;*.xls"), ("All files", "*.*")],
        )
        if selected:
            self.excel_file_path = selected
            self.excel_file_label.config(text=Path(selected).name, fg=COLORS["success"])
            self.status_var.set(f"Node list: {Path(selected).name}")

    def show_selected_files(self) -> None:
        if not self.out_file_paths:
            messagebox.showinfo("Selected files", "No .OUT files have been selected.")
            return

        popup = tk.Toplevel(self.root)
        popup.title("Selected .OUT files")
        popup.geometry("760x430")
        popup.minsize(620, 320)
        popup.configure(bg=COLORS["app_bg"])
        popup.transient(self.root)

        frame = ttk.Frame(popup, style="App.TFrame", padding=20)
        frame.pack(fill="both", expand=True)

        tk.Label(
            frame,
            text=f"{len(self.out_file_paths)} selected output file(s)",
            bg=COLORS["app_bg"],
            fg=COLORS["text"],
            font=("Segoe UI Semibold", 14),
        ).pack(anchor="w", pady=(0, 12))

        tree = ttk.Treeview(
            frame,
            columns=("file", "folder"),
            show="headings",
            style="Modern.Treeview",
        )
        tree.heading("file", text="File")
        tree.heading("folder", text="Folder")
        tree.column("file", width=240, anchor="w")
        tree.column("folder", width=450, anchor="w")

        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        for file_path in self.out_file_paths:
            path = Path(file_path)
            tree.insert("", "end", values=(path.name, str(path.parent)))

    def start_extraction(self) -> None:
        if not self.out_file_paths or not self.excel_file_path:
            messagebox.showerror("Missing inputs", "Select at least one .OUT file and an Excel node list.")
            return

        selected_metrics = [key for key, var in self.selected_options.items() if var.get()]
        if not selected_metrics and not self.nth_max_var.get() and not self.nth_min_var.get():
            messagebox.showerror(
                "No extraction metric",
                "Select at least one metric or enable an nth max/min option.",
            )
            return

        self.status_var.set(f"Extracting data from {len(self.out_file_paths)} output file(s)…")
        self.extract_button.state(["disabled"])

        thread = threading.Thread(target=self._extract_with_ui_cleanup, daemon=True)
        thread.start()

    def _extract_with_ui_cleanup(self) -> None:
        try:
            self.extract_data()
        finally:
            self.root.after(0, self._finish_extraction_ui)

    def _finish_extraction_ui(self) -> None:
        self.extract_button.state(["!disabled"])
        self.status_var.set("Ready")


def main() -> None:
    root = tk.Tk()
    ModernSWMMApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
