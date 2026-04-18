import tkinter as tk
from tkinter import messagebox, ttk
from typing import Dict, Optional

from gear_engine import (
    DEFAULT_PRESSURE_ANGLE,
    FIELD_LABELS,
    InputError,
    auto_solve_gear,
    entered_fields_summary,
    format_result_value,
)


FIELD_ORDER = [
    "module",
    "teeth",
    "pressure_angle",
    "pitch_diameter",
    "outside_diameter",
    "root_diameter",
    "base_diameter",
    "addendum",
    "dedendum",
    "circular_pitch",
    "tooth_thickness",
]

FIELD_HINTS = {
    "module": "Metric module m",
    "teeth": "Whole-number tooth count z",
    "pressure_angle": "Defaults to 20 deg",
    "pitch_diameter": "d = m x z",
    "outside_diameter": "da = m x (z + 2)",
    "root_diameter": "df = m x (z - 2.5)",
    "base_diameter": "db = d x cos(phi)",
    "addendum": "ha = m",
    "dedendum": "hf = 1.25m",
    "circular_pitch": "p = pi x m",
    "tooth_thickness": "s = p / 2",
}

SAMPLE_INPUTS = {
    "module": "2.5",
    "teeth": "24",
    "pressure_angle": "20",
}

DIAMETER_SAMPLE_INPUTS = {
    "pitch_diameter": "72",
    "outside_diameter": "78",
    "pressure_angle": "20",
}


class SpurGearCalculatorApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Spur Gear Engineering Calculator")
        self.root.geometry("1240x760")
        self.root.minsize(1080, 680)

        self.entry_vars: Dict[str, tk.StringVar] = {}
        self.metric_value_labels: Dict[str, ttk.Label] = {}
        self.result_tree: Optional[ttk.Treeview] = None
        self.entered_text: Optional[tk.Text] = None
        self.status_var = tk.StringVar(value="Ready. Enter known gear values and calculate.")

        self._configure_style()
        self._build_layout()
        self._bind_shortcuts()
        self.load_sample_inputs()

    def _configure_style(self) -> None:
        self.root.configure(bg="#f3f5f7")

        style = ttk.Style()
        style.theme_use("clam")

        style.configure("App.TFrame", background="#f3f5f7")
        style.configure("Panel.TFrame", background="#ffffff", relief="flat")
        style.configure("Header.TFrame", background="#16324f")
        style.configure("HeaderTitle.TLabel", background="#16324f", foreground="#ffffff", font=("Segoe UI", 20, "bold"))
        style.configure("HeaderBody.TLabel", background="#16324f", foreground="#d8e5f2", font=("Segoe UI", 10))
        style.configure("PanelTitle.TLabel", background="#ffffff", foreground="#16324f", font=("Segoe UI", 11, "bold"))
        style.configure("CardValue.TLabel", background="#dfe8ef", foreground="#102538", font=("Segoe UI", 16, "bold"))
        style.configure("CardLabel.TLabel", background="#dfe8ef", foreground="#36546f", font=("Segoe UI", 9))
        style.configure("Status.TLabel", background="#102538", foreground="#f7fbff", font=("Segoe UI", 9))
        style.configure("Action.TButton", font=("Segoe UI", 10, "bold"))
        style.configure("Hint.TLabel", background="#ffffff", foreground="#567085", font=("Segoe UI", 9))
        style.configure("InputLabel.TLabel", background="#ffffff", foreground="#173552", font=("Segoe UI", 10, "bold"))

        style.configure(
            "Treeview",
            background="#ffffff",
            foreground="#1b2f41",
            fieldbackground="#ffffff",
            borderwidth=0,
            rowheight=28,
            font=("Consolas", 10),
        )
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))
        style.map("Treeview", background=[("selected", "#cfe1f2")], foreground=[("selected", "#102538")])

    def _build_layout(self) -> None:
        shell = ttk.Frame(self.root, style="App.TFrame", padding=18)
        shell.pack(fill="both", expand=True)
        shell.columnconfigure(0, weight=1)
        shell.rowconfigure(1, weight=1)

        self._build_header(shell)

        content = ttk.Frame(shell, style="App.TFrame")
        content.grid(row=1, column=0, sticky="nsew", pady=(16, 0))
        content.columnconfigure(0, weight=0)
        content.columnconfigure(1, weight=1)
        content.rowconfigure(0, weight=1)

        self._build_input_panel(content)
        self._build_results_panel(content)

        status = ttk.Label(shell, textvariable=self.status_var, style="Status.TLabel", anchor="w", padding=(12, 8))
        status.grid(row=2, column=0, sticky="ew", pady=(16, 0))

    def _build_header(self, parent: ttk.Frame) -> None:
        header = ttk.Frame(parent, style="Header.TFrame", padding=18)
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)

        ttk.Label(header, text="Spur Gear Engineering Calculator", style="HeaderTitle.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(
            header,
            text=(
                "A cleaner engineering workspace for standard full-depth metric spur gears. "
                "Enter any valid combination of known values, solve the geometry, and review the derived checks."
            ),
            style="HeaderBody.TLabel",
            wraplength=760,
            justify="left",
        ).grid(row=1, column=0, sticky="w", pady=(8, 0))

    def _build_input_panel(self, parent: ttk.Frame) -> None:
        panel = ttk.Frame(parent, style="Panel.TFrame", padding=18)
        panel.grid(row=0, column=0, sticky="nsw", padx=(0, 18))
        panel.columnconfigure(0, weight=1)

        ttk.Label(panel, text="Known Inputs", style="PanelTitle.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            panel,
            text=(
                "You only need a solvable combination. The pressure angle defaults to "
                f"{DEFAULT_PRESSURE_ANGLE:.0f} deg if left blank."
            ),
            style="Hint.TLabel",
            wraplength=320,
            justify="left",
        ).grid(row=1, column=0, sticky="w", pady=(4, 14))

        fields_frame = ttk.Frame(panel, style="Panel.TFrame")
        fields_frame.grid(row=2, column=0, sticky="nsew")
        fields_frame.columnconfigure(1, weight=1)

        for row_index, field_name in enumerate(FIELD_ORDER):
            ttk.Label(fields_frame, text=FIELD_LABELS[field_name], style="InputLabel.TLabel").grid(
                row=row_index * 2,
                column=0,
                sticky="w",
                pady=(0, 2),
            )

            var = tk.StringVar()
            entry = ttk.Entry(fields_frame, textvariable=var, width=24, font=("Segoe UI", 10))
            entry.grid(row=row_index * 2, column=1, sticky="ew", padx=(12, 0))
            self.entry_vars[field_name] = var

            ttk.Label(fields_frame, text=FIELD_HINTS[field_name], style="Hint.TLabel").grid(
                row=(row_index * 2) + 1,
                column=0,
                columnspan=2,
                sticky="w",
                pady=(0, 10),
            )

        actions = ttk.Frame(panel, style="Panel.TFrame")
        actions.grid(row=3, column=0, sticky="ew", pady=(8, 0))
        actions.columnconfigure((0, 1), weight=1)

        ttk.Button(actions, text="Calculate", style="Action.TButton", command=self.run_calculation).grid(
            row=0, column=0, sticky="ew", padx=(0, 8)
        )
        ttk.Button(actions, text="Load Sample Gear", command=self.load_sample_inputs).grid(
            row=0, column=1, sticky="ew"
        )
        ttk.Button(actions, text="Load Diameter Pair", command=self.load_diameter_sample).grid(
            row=1, column=0, sticky="ew", padx=(0, 8), pady=(8, 0)
        )
        ttk.Button(actions, text="Clear Inputs", command=self.clear_fields).grid(
            row=1, column=1, sticky="ew", pady=(8, 0)
        )

        helper = tk.Text(
            panel,
            height=9,
            wrap="word",
            bd=0,
            bg="#eef3f7",
            fg="#28445c",
            font=("Segoe UI", 9),
            padx=12,
            pady=10,
        )
        helper.grid(row=4, column=0, sticky="ew", pady=(18, 0))
        helper.insert(
            "1.0",
            "Recommended input combinations:\n"
            "- module + teeth\n"
            "- pitch diameter + teeth\n"
            "- outside diameter + teeth\n"
            "- pitch diameter + outside diameter\n"
            "- pitch diameter + root diameter\n"
            "- outside diameter + root diameter\n\n"
            "The calculator rejects conflicting data so the result stays trustworthy.",
        )
        helper.configure(state="disabled")

    def _build_results_panel(self, parent: ttk.Frame) -> None:
        panel = ttk.Frame(parent, style="Panel.TFrame", padding=18)
        panel.grid(row=0, column=1, sticky="nsew")
        panel.columnconfigure(0, weight=1)
        panel.rowconfigure(2, weight=1)
        panel.rowconfigure(3, weight=1)

        ttk.Label(panel, text="Solved Gear", style="PanelTitle.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            panel,
            text="Review the primary outputs first, then inspect the full property table and the entered-value snapshot.",
            style="Hint.TLabel",
            wraplength=720,
            justify="left",
        ).grid(row=1, column=0, sticky="w", pady=(4, 14))

        cards = ttk.Frame(panel, style="Panel.TFrame")
        cards.grid(row=2, column=0, sticky="ew")
        cards.columnconfigure((0, 1, 2, 3), weight=1)

        for column, (key, title) in enumerate(
            [
                ("module", "Module"),
                ("teeth", "Teeth"),
                ("pitch_diameter", "Pitch Diameter"),
                ("base_diameter", "Base Diameter"),
            ]
        ):
            card = tk.Frame(cards, bg="#dfe8ef", padx=16, pady=14)
            card.grid(row=0, column=column, sticky="nsew", padx=(0, 10 if column < 3 else 0))
            value_label = ttk.Label(card, text="--", style="CardValue.TLabel")
            value_label.pack(anchor="w")
            ttk.Label(card, text=title, style="CardLabel.TLabel").pack(anchor="w", pady=(6, 0))
            self.metric_value_labels[key] = value_label

        lower = ttk.Frame(panel, style="Panel.TFrame")
        lower.grid(row=3, column=0, sticky="nsew", pady=(18, 0))
        lower.columnconfigure(0, weight=3)
        lower.columnconfigure(1, weight=2)
        lower.rowconfigure(0, weight=1)

        table_frame = ttk.Frame(lower, style="Panel.TFrame")
        table_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 16))
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(1, weight=1)

        ttk.Label(table_frame, text="Geometry Table", style="PanelTitle.TLabel").grid(row=0, column=0, sticky="w")
        self.result_tree = ttk.Treeview(table_frame, columns=("property", "value"), show="headings")
        self.result_tree.heading("property", text="Property")
        self.result_tree.heading("value", text="Value")
        self.result_tree.column("property", width=220, anchor="w")
        self.result_tree.column("value", width=220, anchor="w")
        self.result_tree.grid(row=1, column=0, sticky="nsew", pady=(8, 0))

        snapshot_frame = ttk.Frame(lower, style="Panel.TFrame")
        snapshot_frame.grid(row=0, column=1, sticky="nsew")
        snapshot_frame.columnconfigure(0, weight=1)
        snapshot_frame.rowconfigure(1, weight=1)

        ttk.Label(snapshot_frame, text="Entered Values Snapshot", style="PanelTitle.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        self.entered_text = tk.Text(
            snapshot_frame,
            wrap="word",
            bd=0,
            bg="#f5f8fa",
            fg="#28445c",
            font=("Consolas", 10),
            padx=12,
            pady=12,
        )
        self.entered_text.grid(row=1, column=0, sticky="nsew", pady=(8, 0))

        buttons = ttk.Frame(panel, style="Panel.TFrame")
        buttons.grid(row=4, column=0, sticky="e", pady=(14, 0))
        ttk.Button(buttons, text="Copy Results", command=self.copy_results).pack(side="right")

    def _bind_shortcuts(self) -> None:
        self.root.bind("<Return>", lambda _event: self.run_calculation())
        self.root.bind("<Escape>", lambda _event: self.clear_fields())

    def clear_fields(self) -> None:
        for var in self.entry_vars.values():
            var.set("")
        self._clear_result_views()
        self.status_var.set("Inputs cleared.")

    def load_sample_inputs(self) -> None:
        self.clear_fields()
        for field_name, value in SAMPLE_INPUTS.items():
            self.entry_vars[field_name].set(value)
        self.status_var.set("Sample gear loaded.")

    def load_diameter_sample(self) -> None:
        self.clear_fields()
        for field_name, value in DIAMETER_SAMPLE_INPUTS.items():
            self.entry_vars[field_name].set(value)
        self.status_var.set("Diameter-pair sample loaded.")

    def read_inputs(self) -> Dict[str, Optional[float]]:
        values: Dict[str, Optional[float]] = {}

        for field_name, var in self.entry_vars.items():
            raw = var.get().strip()
            if not raw:
                values[field_name] = None
                continue

            try:
                values[field_name] = float(raw)
            except ValueError as exc:
                raise InputError(f"{FIELD_LABELS[field_name]} must be a valid number.") from exc

        return values

    def run_calculation(self) -> None:
        try:
            values = self.read_inputs()
            result = auto_solve_gear(values)
            self._render_result(values, result.as_dict())
            self.status_var.set("Calculation complete. Review the solved gear on the right.")
        except InputError as exc:
            self.status_var.set("Input issue found. Review the message and adjust the values.")
            messagebox.showerror("Input Error", str(exc))
        except Exception as exc:
            self.status_var.set("Unexpected error encountered.")
            messagebox.showerror("Unexpected Error", f"Unexpected error: {exc}")

    def _render_result(self, entered_values: Dict[str, Optional[float]], result: Dict[str, float]) -> None:
        for field_name, label in self.metric_value_labels.items():
            label.configure(text=format_result_value(field_name, result[field_name]))

        if self.result_tree is not None:
            self.result_tree.delete(*self.result_tree.get_children())
            for field_name in FIELD_ORDER:
                self.result_tree.insert(
                    "",
                    "end",
                    values=(FIELD_LABELS[field_name], format_result_value(field_name, result[field_name])),
                )

        snapshot_lines = entered_fields_summary(entered_values)
        snapshot_text = "\n".join(snapshot_lines) if snapshot_lines else "No values were entered."

        if self.entered_text is not None:
            self.entered_text.configure(state="normal")
            self.entered_text.delete("1.0", tk.END)
            self.entered_text.insert(
                "1.0",
                snapshot_text
                + "\n\nAssumptions\n"
                + "- Standard full-depth metric spur gear\n"
                + "- Addendum = m\n"
                + "- Dedendum = 1.25m\n"
                + "- Tooth thickness = circular pitch / 2",
            )
            self.entered_text.configure(state="disabled")

    def _clear_result_views(self) -> None:
        for label in self.metric_value_labels.values():
            label.configure(text="--")

        if self.result_tree is not None:
            self.result_tree.delete(*self.result_tree.get_children())

        if self.entered_text is not None:
            self.entered_text.configure(state="normal")
            self.entered_text.delete("1.0", tk.END)
            self.entered_text.insert(
                "1.0",
                "Waiting for a solved gear.\n\nRun a calculation to populate the engineering summary and property table.",
            )
            self.entered_text.configure(state="disabled")

    def copy_results(self) -> None:
        if self.result_tree is None or not self.result_tree.get_children():
            messagebox.showinfo("Copy Results", "No calculated results are available yet.")
            return

        lines = []
        for item in self.result_tree.get_children():
            name, value = self.result_tree.item(item, "values")
            lines.append(f"{name}: {value}")

        result_text = "\n".join(lines)
        self.root.clipboard_clear()
        self.root.clipboard_append(result_text)
        self.status_var.set("Solved values copied to the clipboard.")


def run() -> None:
    root = tk.Tk()
    SpurGearCalculatorApp(root)
    root.mainloop()
