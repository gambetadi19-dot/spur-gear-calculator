import csv
import datetime
import math
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Dict, List, Optional

import customtkinter as ctk

try:
    from PIL import ImageGrab
except Exception:
    ImageGrab = None

from gear_engine import (
    DEFAULT_PRESSURE_ANGLE,
    FIELD_LABELS,
    FIELD_UNITS,
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

SAMPLE_INPUTS = {"module": "2.5", "teeth": "24", "pressure_angle": "20"}
DIAMETER_SAMPLE_INPUTS = {"pitch_diameter": "72", "outside_diameter": "78", "pressure_angle": "20"}
APP_VERSION = "v1.0"
UNITS_LABEL = "Units: Metric (mm), pressure angle in deg"


class ToolTip:
    def __init__(self, widget: tk.Widget, text: str) -> None:
        self.widget = widget
        self.text = text
        self.tip_window: Optional[tk.Toplevel] = None
        widget.bind("<Enter>", self._show)
        widget.bind("<Leave>", self._hide)

    def _show(self, _event: tk.Event) -> None:
        if self.tip_window is not None:
            return
        x = self.widget.winfo_rootx() + 14
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 6
        self.tip_window = tk.Toplevel(self.widget)
        self.tip_window.wm_overrideredirect(True)
        self.tip_window.wm_geometry(f"+{x}+{y}")
        tk.Label(
            self.tip_window,
            text=self.text,
            bg="#152739",
            fg="#F2F7FC",
            relief="solid",
            bd=1,
            padx=8,
            pady=4,
            font=("Segoe UI", 9),
        ).pack()

    def _hide(self, _event: tk.Event) -> None:
        if self.tip_window is not None:
            self.tip_window.destroy()
            self.tip_window = None


class SpurGearCalculatorApp:
    def __init__(self, root: ctk.CTk) -> None:
        self.root = root
        self.root.title(f"Spur Gear Engineering Calculator {APP_VERSION}")
        self.root.geometry("1380x860")
        self.root.minsize(980, 620)
        self._icon_image: Optional[tk.PhotoImage] = None

        self.entry_vars: Dict[str, tk.StringVar] = {}
        self.entry_widgets: Dict[str, ctk.CTkEntry] = {}
        self.error_labels: Dict[str, ctk.CTkLabel] = {}

        self.summary_labels: Dict[str, ctk.CTkLabel] = {}
        self.result_tree: Optional[ttk.Treeview] = None
        self.entered_textbox: Optional[ctk.CTkTextbox] = None
        self.checks_textbox: Optional[ctk.CTkTextbox] = None

        self.preview_canvas: Optional[tk.Canvas] = None
        self.preview_zoom = 1.0
        self.preview_pan_x = 0.0
        self.preview_pan_y = 0.0
        self.preview_drag_start_x = 0
        self.preview_drag_start_y = 0
        self.preview_zoom_var = tk.StringVar(value="100%")

        self.last_entered_values: Optional[Dict[str, Optional[float]]] = None
        self.last_result_values: Optional[Dict[str, float]] = None
        self.status_var = tk.StringVar(value="Ready. Enter gear values and click Solve Gear.")

        self.main_body: Optional[ctk.CTkFrame] = None
        self.workspace_bar: Optional[ctk.CTkFrame] = None
        self.left_panel: Optional[ctk.CTkFrame] = None
        self.right_panel: Optional[ctk.CTkFrame] = None
        self.preview_card: Optional[ctk.CTkFrame] = None
        self.results_tabview: Optional[ctk.CTkTabview] = None
        self.preview_normal_height = 290
        self.preview_expanded_height = 460
        self.inputs_panel_visible = True
        self.results_panel_visible = True
        self.preview_expanded = False
        self.inputs_toggle_text = tk.StringVar(value="Hide Inputs")
        self.results_toggle_text = tk.StringVar(value="Hide Results")
        self.preview_toggle_text = tk.StringVar(value="Expand Preview")
        self._compact_layout = False

        self._configure_theme()
        self._set_window_icon()
        self._build_ui()
        self._bind_events()
        self.load_example_inputs()

    def _set_window_icon(self) -> None:
        try:
            self._icon_image = self._build_gear_icon_image(64)
            self.root.iconphoto(True, self._icon_image)
        except Exception:
            # Keep startup robust if icon rendering fails on a platform.
            self._icon_image = None

    def _build_gear_icon_image(self, size: int = 64) -> tk.PhotoImage:
        img = tk.PhotoImage(width=size, height=size)
        c = (size - 1) / 2.0
        teeth = 16
        step = (2.0 * math.pi) / teeth

        bg = (22, 50, 79)
        metal_dark = (74, 86, 100)
        metal_mid = (166, 177, 189)
        metal_light = (229, 235, 242)
        hub_dark = (38, 52, 68)
        hub_light = (191, 201, 212)

        r_root = size * 0.34
        r_tip = size * 0.45
        r_hub_outer = size * 0.18
        r_hub_inner = size * 0.085

        def hex_color(rgb: tuple[int, int, int]) -> str:
            return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"

        for y in range(size):
            for x in range(size):
                dx = x - c
                dy = y - c
                r = math.hypot(dx, dy)
                theta = math.atan2(dy, dx)

                tooth_phase = ((theta + step * 0.5) % step) - (step * 0.5)
                is_tooth = abs(tooth_phase) <= (step * 0.24)
                outer = r_tip if is_tooth else r_root

                color_rgb = bg
                if r <= outer:
                    # Ring shading from dark near root to bright near tooth tips.
                    t = max(0.0, min(1.0, (r / max(outer, 1e-6))))
                    if t < 0.52:
                        blend = t / 0.52
                        color_rgb = tuple(
                            int(metal_dark[i] + (metal_mid[i] - metal_dark[i]) * blend) for i in range(3)
                        )
                    else:
                        blend = (t - 0.52) / 0.48
                        color_rgb = tuple(
                            int(metal_mid[i] + (metal_light[i] - metal_mid[i]) * blend) for i in range(3)
                        )

                if r <= r_hub_outer:
                    blend = max(0.0, min(1.0, r / max(r_hub_outer, 1e-6)))
                    color_rgb = tuple(
                        int(hub_light[i] + (hub_dark[i] - hub_light[i]) * blend) for i in range(3)
                    )

                if r <= r_hub_inner:
                    color_rgb = (18, 32, 49)

                img.put(hex_color(color_rgb), (x, y))

        return img

    def _configure_theme(self) -> None:
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        self.root.configure(fg_color="#ECEFF3")

        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure(
            "Treeview",
            background="#F9FBFD",
            foreground="#1D3348",
            fieldbackground="#F9FBFD",
            borderwidth=0,
            rowheight=30,
            font=("Consolas", 10),
        )
        style.configure(
            "Treeview.Heading",
            font=("Segoe UI", 10, "bold"),
            background="#E6EDF4",
            foreground="#16324C",
        )
        style.map("Treeview", background=[("selected", "#D5E5F4")], foreground=[("selected", "#102538")])

    def _build_ui(self) -> None:
        shell = ctk.CTkFrame(self.root, fg_color="transparent")
        shell.grid(row=0, column=0, sticky="nsew", padx=18, pady=16)
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        shell.grid_rowconfigure(2, weight=1)
        shell.grid_columnconfigure(0, weight=1)

        self._build_header(shell)
        self._build_workspace_toolbar(shell)

        self.main_body = ctk.CTkFrame(shell, fg_color="transparent")
        self.main_body.grid(row=2, column=0, sticky="nsew", pady=(12, 0))
        self.main_body.grid_columnconfigure(0, weight=1)
        self.main_body.grid_columnconfigure(1, weight=2)
        self.main_body.grid_rowconfigure(0, weight=1)

        self._build_left_panel(self.main_body)
        self._build_right_panel(self.main_body)
        self._apply_main_layout()
        self._apply_results_visibility()
        self._apply_preview_sizing()
        self._update_workspace_controls()

        ctk.CTkLabel(
            shell,
            textvariable=self.status_var,
            corner_radius=10,
            fg_color="#102538",
            text_color="#F0F7FF",
            anchor="w",
            padx=12,
            height=34,
            font=("Segoe UI", 12),
        ).grid(row=3, column=0, sticky="ew", pady=(14, 0))

    def _build_workspace_toolbar(self, parent: ctk.CTkFrame) -> None:
        self.workspace_bar = ctk.CTkFrame(parent, fg_color="#FFFFFF", corner_radius=10, border_width=1, border_color="#DCE4EC")
        self.workspace_bar.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        self.workspace_bar.grid_columnconfigure(0, weight=1)
        self.workspace_bar.grid_columnconfigure(1, weight=1)

        left = ctk.CTkFrame(self.workspace_bar, fg_color="transparent")
        left.grid(row=0, column=0, sticky="w", padx=10, pady=8)
        right = ctk.CTkFrame(self.workspace_bar, fg_color="transparent")
        right.grid(row=0, column=1, sticky="e", padx=10, pady=8)

        ctk.CTkButton(
            left,
            textvariable=self.inputs_toggle_text,
            command=self.toggle_inputs_panel,
            width=116,
            height=30,
            fg_color="#E8EEF4",
            text_color="#173552",
            hover_color="#D7E3EE",
        ).pack(side="left")
        ctk.CTkButton(
            left,
            textvariable=self.results_toggle_text,
            command=self.toggle_results_panel,
            width=118,
            height=30,
            fg_color="#E8EEF4",
            text_color="#173552",
            hover_color="#D7E3EE",
        ).pack(side="left", padx=(8, 0))
        ctk.CTkButton(
            left,
            textvariable=self.preview_toggle_text,
            command=self.toggle_preview_expand,
            width=128,
            height=30,
            fg_color="#E8EEF4",
            text_color="#173552",
            hover_color="#D7E3EE",
        ).pack(side="left", padx=(8, 0))

        ctk.CTkButton(right, text="Full View", width=98, height=30, command=lambda: self.set_workspace_mode("full")).pack(side="left")
        ctk.CTkButton(right, text="Preview Focus", width=118, height=30, command=lambda: self.set_workspace_mode("preview")).pack(side="left", padx=(8, 0))
        ctk.CTkButton(right, text="Table Focus", width=102, height=30, command=lambda: self.set_workspace_mode("table")).pack(side="left", padx=(8, 0))
        ctk.CTkButton(
            right,
            text="Help / About",
            width=116,
            height=30,
            command=self.show_about_dialog,
            fg_color="#1D4E7A",
            hover_color="#173F63",
        ).pack(side="left", padx=(10, 0))

    def _build_header(self, parent: ctk.CTkFrame) -> None:
        header = ctk.CTkFrame(parent, fg_color="#16324F", corner_radius=12, border_width=0)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(1, weight=1)
        header.grid_columnconfigure(2, weight=0)

        logo = tk.Canvas(header, width=56, height=56, bg="#16324F", highlightthickness=0, bd=0)
        logo.grid(row=0, column=0, rowspan=2, padx=(18, 12), pady=14, sticky="nw")
        self._draw_gear_logo(logo)

        ctk.CTkLabel(
            header,
            text="Spur Gear Engineering Calculator",
            font=("Segoe UI Semibold", 34),
            text_color="#F3F8FD",
            anchor="w",
        ).grid(row=0, column=1, sticky="w", pady=(12, 0), padx=(0, 16))

        ctk.CTkLabel(
            header,
            text=(
                "Premium engineering workspace for metric spur gear geometry. "
                "Use valid input combinations, solve instantly, and export professional outputs."
            ),
            font=("Segoe UI", 14),
            text_color="#D6E5F3",
            anchor="w",
            justify="left",
        ).grid(row=1, column=1, sticky="w", pady=(0, 14), padx=(0, 16))

        meta = ctk.CTkFrame(header, fg_color="#1C3C5C", corner_radius=8, border_width=1, border_color="#2D5376")
        meta.grid(row=0, column=2, rowspan=2, sticky="e", padx=(0, 16), pady=14)
        ctk.CTkLabel(meta, text=f"Release {APP_VERSION}", font=("Segoe UI Semibold", 12), text_color="#F0F7FF").grid(
            row=0, column=0, sticky="e", padx=12, pady=(8, 2)
        )
        ctk.CTkLabel(meta, text=UNITS_LABEL, font=("Segoe UI", 11), text_color="#CFE0F1").grid(
            row=1, column=0, sticky="e", padx=12, pady=(0, 8)
        )

    def _build_left_panel(self, parent: ctk.CTkFrame) -> None:
        self.left_panel = ctk.CTkFrame(parent, fg_color="#FFFFFF", corner_radius=12, border_width=1, border_color="#DCE4EC")
        self.left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        self.left_panel.grid_rowconfigure(0, weight=1)
        self.left_panel.grid_columnconfigure(0, weight=1)

        scroll = ctk.CTkScrollableFrame(self.left_panel, fg_color="transparent", corner_radius=0)
        scroll.grid(row=0, column=0, sticky="nsew", padx=14, pady=14)
        scroll.grid_columnconfigure(0, weight=1)

        self._build_input_group(scroll, 0, "Core Inputs", ["module", "teeth", "pressure_angle"])
        self._build_input_group(scroll, 1, "Optional Diameter Inputs", ["pitch_diameter", "outside_diameter", "root_diameter", "base_diameter"])
        self._build_input_group(scroll, 2, "Derived Tooth Properties", ["addendum", "dedendum", "circular_pitch", "tooth_thickness"])

        action = ctk.CTkFrame(scroll, fg_color="#F6F9FC", corner_radius=12, border_width=1, border_color="#DCE4EC")
        action.grid(row=3, column=0, sticky="ew", pady=(10, 0))
        action.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(
            action, text="Solve Gear", command=self.run_calculation, height=40, corner_radius=10,
            fg_color="#1D4E7A", hover_color="#173F63", font=("Segoe UI Semibold", 14)
        ).grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=(10, 8))

        ctk.CTkButton(
            action, text="Reset", command=self.clear_fields, height=36, corner_radius=10,
            fg_color="#E8EEF4", text_color="#1C3347", hover_color="#D7E3EE", font=("Segoe UI", 13)
        ).grid(row=1, column=0, sticky="ew", padx=(10, 6), pady=(0, 10))

        ctk.CTkButton(
            action, text="Load Example", command=self.load_example_inputs, height=36, corner_radius=10,
            fg_color="#E8EEF4", text_color="#1C3347", hover_color="#D7E3EE", font=("Segoe UI", 13)
        ).grid(row=1, column=1, sticky="ew", padx=(6, 10), pady=(0, 10))

    def _build_input_group(self, parent: ctk.CTkScrollableFrame, row: int, title: str, fields: List[str]) -> None:
        card = ctk.CTkFrame(parent, fg_color="#FFFFFF", corner_radius=12, border_width=1, border_color="#DCE4EC")
        card.grid(row=row, column=0, sticky="ew", pady=(0, 10))
        card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(card, text=title, font=("Segoe UI Semibold", 17), text_color="#173552", anchor="w").grid(
            row=0, column=0, sticky="w", padx=12, pady=(10, 4)
        )

        content = ctk.CTkFrame(card, fg_color="transparent")
        content.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 10))
        content.grid_columnconfigure(0, weight=1)

        for idx, field_name in enumerate(fields):
            base = idx * 4
            ctk.CTkLabel(content, text=FIELD_LABELS[field_name], font=("Segoe UI Semibold", 13), text_color="#1B3650", anchor="w").grid(
                row=base, column=0, sticky="w", pady=(0, 2)
            )

            var = tk.StringVar()
            entry = ctk.CTkEntry(
                content,
                textvariable=var,
                height=34,
                corner_radius=8,
                border_width=1,
                border_color="#CBD8E5",
                fg_color="#FCFDFE",
                placeholder_text=FIELD_HINTS[field_name],
                font=("Segoe UI", 13),
            )
            entry.grid(row=base + 1, column=0, sticky="ew")
            entry.bind("<FocusOut>", lambda _e, name=field_name: self._validate_single_field(name))

            ctk.CTkLabel(content, text=FIELD_HINTS[field_name], font=("Segoe UI", 11), text_color="#6A8197", anchor="w").grid(
                row=base + 2, column=0, sticky="w", pady=(2, 0)
            )
            err = ctk.CTkLabel(content, text="", font=("Segoe UI", 11, "bold"), text_color="#B12D2D", anchor="w")
            err.grid(row=base + 3, column=0, sticky="w", pady=(1, 6))

            self.entry_vars[field_name] = var
            self.entry_widgets[field_name] = entry
            self.error_labels[field_name] = err

    def _build_right_panel(self, parent: ctk.CTkFrame) -> None:
        self.right_panel = ctk.CTkFrame(parent, fg_color="#FFFFFF", corner_radius=12, border_width=1, border_color="#DCE4EC")
        self.right_panel.grid(row=0, column=1, sticky="nsew", padx=(12, 0))
        self.right_panel.grid_columnconfigure(0, weight=1)
        self.right_panel.grid_rowconfigure(1, weight=1)
        self.right_panel.grid_rowconfigure(2, weight=1)

        self._build_summary_cards(self.right_panel)
        self._build_preview(self.right_panel)
        self._build_tabs(self.right_panel)

    def _build_summary_cards(self, parent: ctk.CTkFrame) -> None:
        wrap = ctk.CTkFrame(parent, fg_color="transparent")
        wrap.grid(row=0, column=0, sticky="ew", padx=14, pady=(14, 8))
        wrap.grid_columnconfigure((0, 1, 2, 3), weight=1)

        defs = [("module", "Module"), ("teeth", "Teeth"), ("pitch_diameter", "Pitch Diameter"), ("base_diameter", "Base Diameter")]
        for col, (key, title) in enumerate(defs):
            card = ctk.CTkFrame(wrap, fg_color="#EDF4FA", corner_radius=10, border_width=1, border_color="#D8E4EF")
            card.grid(row=0, column=col, sticky="nsew", padx=(0, 8 if col < 3 else 0))
            val = ctk.CTkLabel(card, text="--", font=("Segoe UI Semibold", 28), text_color="#102B42", anchor="w")
            val.grid(row=0, column=0, sticky="w", padx=12, pady=(10, 0))
            ctk.CTkLabel(card, text=title, font=("Segoe UI", 12), text_color="#3C5C76", anchor="w").grid(
                row=1, column=0, sticky="w", padx=12, pady=(2, 10)
            )
            self.summary_labels[key] = val

    def _build_preview(self, parent: ctk.CTkFrame) -> None:
        card = ctk.CTkFrame(parent, fg_color="#FFFFFF", corner_radius=10, border_width=1, border_color="#DCE4EC")
        self.preview_card = card
        card.grid(row=1, column=0, sticky="nsew", padx=14, pady=(6, 8))
        card.grid_columnconfigure(0, weight=1)
        card.grid_rowconfigure(1, weight=1)

        head = ctk.CTkFrame(card, fg_color="transparent")
        head.grid(row=0, column=0, sticky="ew", padx=10, pady=(8, 0))
        head.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(head, text="Gear Preview", font=("Segoe UI Semibold", 18), text_color="#173552").grid(row=0, column=0, sticky="w")

        bar = ctk.CTkFrame(head, fg_color="transparent")
        bar.grid(row=0, column=1, sticky="e")

        z_out = ctk.CTkButton(bar, text="-", width=34, height=30, command=self.preview_zoom_out, fg_color="#E8EEF4", text_color="#173552", hover_color="#D7E3EE")
        z_in = ctk.CTkButton(bar, text="+", width=34, height=30, command=self.preview_zoom_in, fg_color="#E8EEF4", text_color="#173552", hover_color="#D7E3EE")
        fit = ctk.CTkButton(bar, text="Fit", width=56, height=30, command=self.preview_fit_view, fg_color="#E8EEF4", text_color="#173552", hover_color="#D7E3EE")
        reset = ctk.CTkButton(bar, text="Reset", width=60, height=30, command=self.preview_reset_view, fg_color="#E8EEF4", text_color="#173552", hover_color="#D7E3EE")
        z_out.pack(side="left")
        z_in.pack(side="left", padx=(6, 0))
        fit.pack(side="left", padx=(8, 0))
        reset.pack(side="left", padx=(8, 0))
        ctk.CTkLabel(bar, textvariable=self.preview_zoom_var, font=("Segoe UI", 11), text_color="#4F6A80").pack(side="left", padx=(10, 0))

        ToolTip(z_out, "Zoom out")
        ToolTip(z_in, "Zoom in")
        ToolTip(fit, "Fit gear to view")
        ToolTip(reset, "Reset zoom and pan")

        self.preview_canvas = tk.Canvas(
            card,
            height=self.preview_normal_height,
            bg="#F4F8FC",
            highlightthickness=1,
            highlightbackground="#D6E1EB",
            bd=0,
        )
        self.preview_canvas.grid(row=1, column=0, sticky="nsew", padx=10, pady=(8, 10))
        self.preview_canvas.bind("<Configure>", lambda _e: self.update_preview(self.last_result_values))
        self.preview_canvas.bind("<MouseWheel>", self._on_preview_mousewheel)
        self.preview_canvas.bind("<ButtonPress-1>", self._on_preview_pan_start)
        self.preview_canvas.bind("<B1-Motion>", self._on_preview_pan_move)
        self.preview_canvas.bind("<Double-Button-1>", lambda _e: self.preview_reset_view())
        ToolTip(self.preview_canvas, "Mouse wheel: zoom | Drag: pan | Double-click: reset")
        self.update_preview(None)

    def _build_tabs(self, parent: ctk.CTkFrame) -> None:
        tabs = ctk.CTkTabview(
            parent,
            fg_color="#FFFFFF",
            segmented_button_fg_color="#E6EDF4",
            segmented_button_selected_color="#1D4E7A",
            segmented_button_unselected_color="#E6EDF4",
            segmented_button_selected_hover_color="#173F63",
        )
        self.results_tabview = tabs
        tabs.grid(row=2, column=0, sticky="nsew", padx=14, pady=(6, 14))
        geo = tabs.add("Geometry Table")
        entered = tabs.add("Entered Values")
        checks = tabs.add("Engineering Checks")
        export = tabs.add("Export")

        geo.grid_columnconfigure(0, weight=1)
        geo.grid_rowconfigure(0, weight=1)
        holder = ctk.CTkFrame(geo, fg_color="transparent")
        holder.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        holder.grid_columnconfigure(0, weight=1)
        holder.grid_rowconfigure(0, weight=1)

        self.result_tree = ttk.Treeview(holder, columns=("property", "value"), show="headings")
        self.result_tree.heading("property", text="Property")
        self.result_tree.heading("value", text="Value")
        self.result_tree.column("property", width=280, anchor="w")
        self.result_tree.column("value", width=280, anchor="w")
        self.result_tree.tag_configure("even", background="#EEF4FA")
        self.result_tree.tag_configure("odd", background="#F9FBFD")
        self.result_tree.grid(row=0, column=0, sticky="nsew")
        s1 = ttk.Scrollbar(holder, orient="vertical", command=self.result_tree.yview)
        self.result_tree.configure(yscrollcommand=s1.set)
        s1.grid(row=0, column=1, sticky="ns", padx=(8, 0))

        entered.grid_columnconfigure(0, weight=1)
        entered.grid_rowconfigure(0, weight=1)
        self.entered_textbox = ctk.CTkTextbox(entered, fg_color="#F8FBFE", border_width=1, border_color="#DCE4EC")
        self.entered_textbox.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)

        checks.grid_columnconfigure(0, weight=1)
        checks.grid_rowconfigure(0, weight=1)
        self.checks_textbox = ctk.CTkTextbox(checks, fg_color="#F8FBFE", border_width=1, border_color="#DCE4EC")
        self.checks_textbox.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)

        export.grid_columnconfigure((0, 1), weight=1)
        ctk.CTkButton(export, text="Export CSV", command=self.export_csv, fg_color="#E8EEF4", text_color="#173552", hover_color="#D7E3EE").grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 6))
        ctk.CTkButton(export, text="Export PDF", command=self.export_pdf, fg_color="#E8EEF4", text_color="#173552", hover_color="#D7E3EE").grid(row=0, column=1, sticky="ew", padx=8, pady=(8, 6))
        ctk.CTkButton(export, text="Export Preview PNG", command=self.export_png, fg_color="#E8EEF4", text_color="#173552", hover_color="#D7E3EE").grid(row=1, column=0, sticky="ew", padx=8, pady=(6, 8))
        ctk.CTkButton(export, text="Copy Results", command=self.copy_results, fg_color="#1D4E7A", hover_color="#173F63").grid(row=1, column=1, sticky="ew", padx=8, pady=(6, 8))

    def _bind_events(self) -> None:
        self.root.bind("<Return>", lambda _e: self.run_calculation())
        self.root.bind("<Escape>", lambda _e: self.clear_fields())
        self.root.bind("<Configure>", self._on_window_resize)

    def _apply_main_layout(self) -> None:
        if self.main_body is None or self.left_panel is None or self.right_panel is None:
            return
        self.left_panel.grid_remove()
        self.right_panel.grid_remove()

        if self.inputs_panel_visible:
            if self._compact_layout:
                self.main_body.grid_columnconfigure(0, weight=1)
                self.main_body.grid_columnconfigure(1, weight=0)
                self.main_body.grid_rowconfigure(0, weight=0)
                self.main_body.grid_rowconfigure(1, weight=1)
                self.left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 0), pady=(0, 12))
                self.right_panel.grid(row=1, column=0, sticky="nsew", padx=(0, 0), pady=(0, 0))
            else:
                self.main_body.grid_columnconfigure(0, weight=1)
                self.main_body.grid_columnconfigure(1, weight=2)
                self.main_body.grid_rowconfigure(0, weight=1)
                self.main_body.grid_rowconfigure(1, weight=0)
                self.left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 12), pady=(0, 0))
                self.right_panel.grid(row=0, column=1, sticky="nsew", padx=(12, 0), pady=(0, 0))
        else:
            self.main_body.grid_columnconfigure(0, weight=1)
            self.main_body.grid_columnconfigure(1, weight=0)
            self.main_body.grid_rowconfigure(0, weight=1)
            self.main_body.grid_rowconfigure(1, weight=0)
            self.right_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 0), pady=(0, 0))

    def _apply_results_visibility(self) -> None:
        if self.results_tabview is None or self.right_panel is None:
            return
        if self.results_panel_visible:
            self.results_tabview.grid()
            self.right_panel.grid_rowconfigure(2, weight=1)
        else:
            self.results_tabview.grid_remove()
            self.right_panel.grid_rowconfigure(2, weight=0)

    def _apply_preview_sizing(self) -> None:
        if self.preview_canvas is None or self.right_panel is None:
            return
        target_height = self.preview_expanded_height if self.preview_expanded else self.preview_normal_height
        if not self.results_panel_visible:
            target_height = max(target_height, self.preview_expanded_height)
        self.preview_canvas.configure(height=target_height)

        if self.results_panel_visible:
            self.right_panel.grid_rowconfigure(1, weight=3 if self.preview_expanded else 1)
            self.right_panel.grid_rowconfigure(2, weight=1)
        else:
            self.right_panel.grid_rowconfigure(1, weight=1)
            self.right_panel.grid_rowconfigure(2, weight=0)
        self.update_preview(self.last_result_values)

    def _update_workspace_controls(self) -> None:
        self.inputs_toggle_text.set("Hide Inputs" if self.inputs_panel_visible else "Show Inputs")
        self.results_toggle_text.set("Hide Results" if self.results_panel_visible else "Show Results")
        self.preview_toggle_text.set("Normal Preview" if self.preview_expanded else "Expand Preview")

    def toggle_inputs_panel(self) -> None:
        self.inputs_panel_visible = not self.inputs_panel_visible
        self._apply_main_layout()
        self._update_workspace_controls()

    def toggle_results_panel(self) -> None:
        self.results_panel_visible = not self.results_panel_visible
        self._apply_results_visibility()
        self._apply_preview_sizing()
        self._update_workspace_controls()

    def toggle_preview_expand(self) -> None:
        self.preview_expanded = not self.preview_expanded
        self._apply_preview_sizing()
        self._update_workspace_controls()

    def set_workspace_mode(self, mode: str) -> None:
        mode_lc = mode.strip().lower()
        if mode_lc == "preview":
            self.inputs_panel_visible = False
            self.results_panel_visible = False
            self.preview_expanded = True
            self.status_var.set("Workspace mode: Preview Focus")
        elif mode_lc == "table":
            self.inputs_panel_visible = False
            self.results_panel_visible = True
            self.preview_expanded = False
            self.status_var.set("Workspace mode: Table Focus")
        else:
            self.inputs_panel_visible = True
            self.results_panel_visible = True
            self.preview_expanded = False
            self.status_var.set("Workspace mode: Full View")

        self._apply_main_layout()
        self._apply_results_visibility()
        self._apply_preview_sizing()
        self._update_workspace_controls()

    def _on_window_resize(self, event: tk.Event) -> None:
        if event.widget is not self.root or self.main_body is None or self.left_panel is None or self.right_panel is None:
            return
        compact = event.width < 1220
        if compact == self._compact_layout:
            return
        self._compact_layout = compact
        self._apply_main_layout()

    def _draw_gear_logo(self, canvas: tk.Canvas) -> None:
        canvas.delete("all")
        cx, cy = 28, 28
        teeth = 20
        r_root = 19.0
        r_tip = 27.0

        # Drop shadow for depth.
        canvas.create_oval(cx - 26, cy - 24, cx + 28, cy + 30, fill="#0E2235", outline="")
        canvas.create_oval(cx - 24, cy - 22, cx + 26, cy + 28, fill="#122A40", outline="")

        # Gear body with short flat-topped teeth.
        pts: List[float] = []
        step = (2 * math.pi) / teeth
        for i in range(teeth):
            a = i * step
            pts.extend(
                [
                    cx + math.cos(a - step * 0.42) * r_root,
                    cy + math.sin(a - step * 0.42) * r_root,
                    cx + math.cos(a - step * 0.16) * r_tip,
                    cy + math.sin(a - step * 0.16) * r_tip,
                    cx + math.cos(a + step * 0.16) * r_tip,
                    cy + math.sin(a + step * 0.16) * r_tip,
                    cx + math.cos(a + step * 0.42) * r_root,
                    cy + math.sin(a + step * 0.42) * r_root,
                ]
            )
        canvas.create_polygon(pts, fill="#AEB6C0", outline="#E6EBF1", width=1)

        # Radial highlights to mimic brushed metal rings.
        canvas.create_oval(cx - 20, cy - 20, cx + 20, cy + 20, fill="#6A7482", outline="#909BA8", width=1)
        canvas.create_oval(cx - 17, cy - 17, cx + 17, cy + 17, fill="#4A5562", outline="#7F8997", width=1)
        canvas.create_oval(cx - 13, cy - 13, cx + 13, cy + 13, fill="#C7CFD8", outline="#EEF2F7", width=1)
        canvas.create_oval(cx - 10, cy - 10, cx + 10, cy + 10, fill="#A7B0BB", outline="#D8DEE7", width=1)
        canvas.create_oval(cx - 6, cy - 6, cx + 6, cy + 6, fill="#1A293A", outline="#8D98A5", width=1)

        # Light sheen across the upper-left side.
        canvas.create_arc(
            cx - 26,
            cy - 26,
            cx + 26,
            cy + 26,
            start=110,
            extent=95,
            style="arc",
            outline="#F4F7FB",
            width=2,
        )

    def _set_field_error(self, field_name: str, msg: str) -> None:
        self.entry_widgets[field_name].configure(border_color="#B12D2D")
        self.error_labels[field_name].configure(text=msg)

    def _clear_field_error(self, field_name: str) -> None:
        self.entry_widgets[field_name].configure(border_color="#CBD8E5")
        self.error_labels[field_name].configure(text="")

    def _validate_single_field(self, field_name: str) -> bool:
        raw = self.entry_vars[field_name].get().strip()
        if not raw:
            self._clear_field_error(field_name)
            return True
        try:
            value = float(raw)
        except ValueError:
            self._set_field_error(field_name, "Enter a valid number")
            return False

        if field_name == "teeth":
            if value <= 0 or abs(value - round(value)) > 1e-6:
                self._set_field_error(field_name, "Use a positive whole number")
                return False
        elif field_name == "pressure_angle":
            if value <= 0 or value >= 45:
                self._set_field_error(field_name, "Use an angle between 0 and 45")
                return False
        elif value <= 0:
            self._set_field_error(field_name, "Must be greater than zero")
            return False
        self._clear_field_error(field_name)
        return True

    def _validate_all_fields(self) -> bool:
        return all(self._validate_single_field(name) for name in FIELD_ORDER)

    def read_inputs(self) -> Dict[str, Optional[float]]:
        if not self._validate_all_fields():
            raise InputError("INLINE_VALIDATION")
        values: Dict[str, Optional[float]] = {}
        for field_name, var in self.entry_vars.items():
            raw = var.get().strip()
            values[field_name] = float(raw) if raw else None
        if all(v is None for v in values.values()):
            raise InputError(
                "No inputs were entered. Provide at least a solvable pair (for example: module + teeth)."
            )
        return values

    # Placeholder-friendly solver wrapper.
    def solve_gear(self, values: Dict[str, Optional[float]]) -> Dict[str, float]:
        return auto_solve_gear(values).as_dict()

    def run_calculation(self) -> None:
        try:
            values = self.read_inputs()
            result = self.solve_gear(values)
            self._render_result(values, result)
            self.status_var.set("Solve complete. Review geometry, checks, and exports.")
        except InputError as exc:
            if str(exc) == "INLINE_VALIDATION":
                self.status_var.set("Fix highlighted fields and try again.")
                return
            self.status_var.set("Input conflict detected.")
            messagebox.showerror("Input Error", str(exc))
        except Exception as exc:
            self.status_var.set("Unexpected error encountered.")
            messagebox.showerror("Error", f"Unexpected error: {exc}")

    def _render_result(self, entered_values: Dict[str, Optional[float]], result: Dict[str, float]) -> None:
        self.last_entered_values = entered_values
        self.last_result_values = result

        for key, label in self.summary_labels.items():
            label.configure(text=format_result_value(key, result[key]))

        if self.result_tree is not None:
            self.result_tree.delete(*self.result_tree.get_children())
            for idx, field_name in enumerate(FIELD_ORDER):
                self.result_tree.insert(
                    "",
                    "end",
                    values=(FIELD_LABELS[field_name], format_result_value(field_name, result[field_name])),
                    tags=("even" if idx % 2 == 0 else "odd",),
                )

        snap_lines = entered_fields_summary(entered_values)
        snapshot = "\n".join(snap_lines) if snap_lines else "No values entered."
        assumptions = (
            "\n\nAssumptions\n"
            "- Standard full-depth metric spur gear\n"
            "- Addendum = m\n"
            "- Dedendum = 1.25m\n"
            "- Tooth thickness = circular pitch / 2"
        )
        if self.entered_textbox is not None:
            self.entered_textbox.configure(state="normal")
            self.entered_textbox.delete("1.0", "end")
            self.entered_textbox.insert("1.0", snapshot + assumptions)
            self.entered_textbox.configure(state="disabled")

        if self.checks_textbox is not None:
            self.checks_textbox.configure(state="normal")
            self.checks_textbox.delete("1.0", "end")
            self.checks_textbox.insert("1.0", self._build_engineering_checks(result))
            self.checks_textbox.configure(state="disabled")

        self.update_preview(result)

    def _build_engineering_checks(self, result: Dict[str, float]) -> str:
        teeth = int(result["teeth"])
        module = result["module"]
        pressure = result["pressure_angle"]
        sin_phi = math.sin(math.radians(pressure))
        min_teeth = int(math.ceil(2.0 / max(1e-9, sin_phi * sin_phi)))
        tip_thickness = result["tooth_thickness"] - (2 * result["addendum"] * math.tan(math.radians(pressure)))
        eq_pitch = abs(result["pitch_diameter"] - (result["module"] * result["teeth"]))
        eq_outside = abs(result["outside_diameter"] - (result["module"] * (result["teeth"] + 2)))
        eq_root = abs(result["root_diameter"] - (result["module"] * (result["teeth"] - 2.5)))
        eq_base = abs(
            result["base_diameter"] - (result["pitch_diameter"] * math.cos(math.radians(result["pressure_angle"])))
        )

        def grade(ok: bool, warning: bool = False) -> str:
            if ok:
                return "PASS"
            return "WARNING" if warning else "ERROR"

        return "\n".join(
            [
                "Engineering Checks",
                "",
                "Core Equations",
                f"{grade(eq_pitch <= 1e-9)}: d = m x z (residual {eq_pitch:.3e} mm)",
                f"{grade(eq_outside <= 1e-9)}: da = m x (z + 2) (residual {eq_outside:.3e} mm)",
                f"{grade(eq_root <= 1e-9)}: df = m x (z - 2.5) (residual {eq_root:.3e} mm)",
                f"{grade(eq_base <= 1e-9)}: db = d x cos(phi) (residual {eq_base:.3e} mm)",
                "",
                f"Undercut threshold (approx): z >= {min_teeth}",
                f"{grade(teeth >= min_teeth, warning=True)}: current teeth = {teeth}",
                "",
                f"Tip thickness estimate: {tip_thickness:.4f} mm",
                f"{grade(tip_thickness > 0.1 * module, warning=True)}: tip thickness vs module criterion",
                "",
                f"Root diameter: {result['root_diameter']:.4f} mm",
                f"{grade(result['root_diameter'] > 0)}: root diameter validity",
                "",
                f"Units check: {UNITS_LABEL}",
            ]
        )

    def compute_label_positions(
        self, legend_top: float, legend_bottom: float, annotation_keys: List[str]
    ) -> Dict[str, float]:
        content_top = legend_top + 16
        content_bottom = legend_bottom - 16
        line_count = 9
        step = (content_bottom - content_top) / max(1, line_count - 1)
        key_to_row = {
            "outside_diameter": 2,
            "pitch_diameter": 3,
            "base_diameter": 4,
            "root_diameter": 5,
        }
        return {key: content_top + (key_to_row[key] * step) for key in annotation_keys}

    def map_geometry_to_lines(
        self,
        cx: float,
        cy: float,
        legend_left: float,
        geometry_annotations: List[Dict[str, float | str]],
        label_positions: Dict[str, float],
    ) -> List[Dict[str, float | str]]:
        line_data: List[Dict[str, float | str]] = []
        elbow_x = legend_left - 18
        text_x = legend_left + 8

        for ann in geometry_annotations:
            key = str(ann["key"])
            radius = float(ann["radius"])
            label_y = label_positions[key]

            dy = label_y - cy
            dy_clamped = max(-radius + 1.0, min(radius - 1.0, dy))
            chord = math.sqrt(max(0.0, (radius * radius) - (dy_clamped * dy_clamped)))
            start_x = cx + chord
            start_y = cy + dy_clamped

            mid_x = max(start_x + 16.0, elbow_x)
            line_data.append(
                {
                    "key": key,
                    "color": ann["color"],
                    "label_y": label_y,
                    "start_x": start_x,
                    "start_y": start_y,
                    "mid_x": mid_x,
                    "text_x": text_x,
                }
            )
        return line_data

    def draw_annotations(
        self,
        canvas: tk.Canvas,
        result: Dict[str, float],
        geometry_annotations: List[Dict[str, float | str]],
        legend_left: float,
        legend_top: float,
        legend_bottom: float,
        cx: float,
        cy: float,
    ) -> None:
        annotation_keys = [str(a["key"]) for a in geometry_annotations]
        label_positions = self.compute_label_positions(legend_top, legend_bottom, annotation_keys)
        line_data = self.map_geometry_to_lines(cx, cy, legend_left, geometry_annotations, label_positions)

        for line in line_data:
            sx = float(line["start_x"])
            sy = float(line["start_y"])
            mx = float(line["mid_x"])
            ly = float(line["label_y"])
            tx = float(line["text_x"])
            color = str(line["color"])
            canvas.create_line(sx, sy, mx, ly, fill=color, width=1, capstyle=tk.ROUND)
            canvas.create_line(mx, ly, tx, ly, fill=color, width=2, capstyle=tk.ROUND)

        content_top = legend_top + 16
        content_bottom = legend_bottom - 16
        line_count = 9
        step = (content_bottom - content_top) / max(1, line_count - 1)
        text_x = legend_left + 14

        text_rows = [
            ("Geometry Summary", content_top + (0 * step), "#244761", ("Segoe UI Semibold", 12)),
            (f"Teeth: {int(result['teeth'])}", content_top + (1 * step), "#244761", ("Segoe UI", 11)),
            (f"Outside diameter: {result['outside_diameter']:.2f} mm", label_positions["outside_diameter"], "#244761", ("Segoe UI", 11)),
            (f"Pitch diameter: {result['pitch_diameter']:.2f} mm", label_positions["pitch_diameter"], "#244761", ("Segoe UI", 11)),
            (f"Base diameter: {result['base_diameter']:.2f} mm", label_positions["base_diameter"], "#244761", ("Segoe UI", 11)),
            (f"Root diameter: {result['root_diameter']:.2f} mm", label_positions["root_diameter"], "#244761", ("Segoe UI", 11)),
            ("", content_top + (6 * step), "#244761", ("Segoe UI", 11)),
            (f"Module: {result['module']:.3f} mm", content_top + (7 * step), "#244761", ("Segoe UI", 11)),
            (f"Pressure angle: {result['pressure_angle']:.2f} deg", content_top + (8 * step), "#244761", ("Segoe UI", 11)),
        ]
        for text, y, color, font in text_rows:
            if text:
                canvas.create_text(text_x, y, text=text, anchor="w", fill=color, font=font)

    # Placeholder-friendly preview wrapper.
    def update_preview(self, result: Optional[Dict[str, float]]) -> None:
        if self.preview_canvas is None:
            return
        canvas = self.preview_canvas
        canvas.delete("all")

        try:
            width = max(1, canvas.winfo_width())
            height = max(1, canvas.winfo_height())
            if width <= 1 or height <= 1:
                width = int(canvas.cget("width"))
                height = int(canvas.cget("height"))

            if result is None:
                canvas.create_text(
                    width / 2, height / 2, text="Run a solve to render gear preview.", fill="#5A7084", font=("Segoe UI", 11)
                )
                return

            od = result["outside_diameter"]
            pd = result["pitch_diameter"]
            rd = result["root_diameter"]
            bd = result["base_diameter"]
            teeth = max(1, int(result["teeth"]))

            max_d = max(od, pd, rd, bd)
            scale = (min(width, height) * 0.36 / max_d) * self.preview_zoom
            cx = (width * 0.30) + self.preview_pan_x
            cy = (height * 0.50) + self.preview_pan_y

            r_out = (od * 0.5) * scale
            r_pitch = (pd * 0.5) * scale
            r_root = (rd * 0.5) * scale
            r_base = (bd * 0.5) * scale

            pad = 14
            legend_w = max(250, min(360, int(width * 0.38)))
            legend_left = max((cx + r_out + 44), width - legend_w - pad)
            legend_right = width - pad
            legend_top = max(16, cy - 96)
            legend_bottom = min(height - 16, legend_top + 196)
            if legend_bottom - legend_top < 150:
                legend_top = max(16, legend_bottom - 150)

            canvas.create_rectangle(
                legend_left, legend_top, legend_right, legend_bottom, fill="#F2F7FB", outline="#D0DBE7", width=1
            )

            def draw_circle(radius: float, outline: str, dash: Optional[tuple[int, int]] = None) -> None:
                canvas.create_oval(cx - radius, cy - radius, cx + radius, cy + radius, outline=outline, width=2, dash=dash)

            canvas.create_oval(cx - r_root, cy - r_root, cx + r_root, cy + r_root, fill="#D9E5F0", outline="")

            tooth_pitch = (2 * math.pi) / teeth
            pitch_r_mm = max(1e-6, pd * 0.5)
            half_pitch = (result["tooth_thickness"] / pitch_r_mm) * 0.5
            half_pitch = min(half_pitch, tooth_pitch * 0.45)
            half_root = min(half_pitch * 1.35, tooth_pitch * 0.49)
            half_tip = max(half_pitch * 0.72, tooth_pitch * 0.20)
            half_tip = min(half_tip, tooth_pitch * 0.42)

            def polar(radius: float, angle: float) -> tuple[float, float]:
                return (cx + math.cos(angle) * radius, cy + math.sin(angle) * radius)

            for idx in range(teeth):
                a = idx * tooth_pitch
                points = [
                    polar(r_root, a - half_root),
                    polar(r_base, a - (half_root * 0.80)),
                    polar(r_pitch, a - half_pitch),
                    polar(r_out, a - half_tip),
                    polar(r_out, a + half_tip),
                    polar(r_pitch, a + half_pitch),
                    polar(r_base, a + (half_root * 0.80)),
                    polar(r_root, a + half_root),
                ]
                flat = [v for p in points for v in p]
                canvas.create_polygon(flat, fill="#C9D9E7", outline="#7F9EB8", width=1)

            draw_circle(r_out, "#2F6F9F")
            draw_circle(r_pitch, "#4F8AB5", (5, 4))
            draw_circle(r_base, "#6F9BBF", (2, 4))
            draw_circle(r_root, "#8CAEC7")
            canvas.create_oval(cx - 8, cy - 8, cx + 8, cy + 8, fill="#18344E", outline="")

            geometry_annotations = [
                {"key": "outside_diameter", "label": "Outside diameter", "radius": r_out, "color": "#2F6F9F"},
                {"key": "pitch_diameter", "label": "Pitch diameter", "radius": r_pitch, "color": "#4F8AB5"},
                {"key": "base_diameter", "label": "Base diameter", "radius": r_base, "color": "#6F9BBF"},
                {"key": "root_diameter", "label": "Root diameter", "radius": r_root, "color": "#8CAEC7"},
            ]
            self.draw_annotations(canvas, result, geometry_annotations, legend_left, legend_top, legend_bottom, cx, cy)
        except Exception:
            canvas.delete("all")
            canvas.create_text(
                width / 2,
                height / 2,
                text="Preview unavailable for current view.\nUse Fit or Reset to recover.",
                fill="#8A2B2B",
                font=("Segoe UI", 11),
                justify="center",
            )

    def clear_fields(self) -> None:
        for name, var in self.entry_vars.items():
            var.set("")
            self._clear_field_error(name)
        self.last_entered_values = None
        self.last_result_values = None
        self.preview_zoom = 1.0
        self.preview_pan_x = 0.0
        self.preview_pan_y = 0.0
        self._update_zoom_label()

        for label in self.summary_labels.values():
            label.configure(text="--")
        if self.result_tree is not None:
            self.result_tree.delete(*self.result_tree.get_children())
        if self.entered_textbox is not None:
            self.entered_textbox.configure(state="normal")
            self.entered_textbox.delete("1.0", "end")
            self.entered_textbox.insert("1.0", "Waiting for solved gear values.")
            self.entered_textbox.configure(state="disabled")
        if self.checks_textbox is not None:
            self.checks_textbox.configure(state="normal")
            self.checks_textbox.delete("1.0", "end")
            self.checks_textbox.insert("1.0", "Engineering checks will appear after a successful solve.")
            self.checks_textbox.configure(state="disabled")
        self.update_preview(None)
        self.status_var.set("Inputs cleared.")

    def load_example_inputs(self) -> None:
        self.clear_fields()
        for name, value in SAMPLE_INPUTS.items():
            self.entry_vars[name].set(value)
            self._validate_single_field(name)
        self.status_var.set("Example inputs loaded.")

    def load_diameter_sample(self) -> None:
        self.clear_fields()
        for name, value in DIAMETER_SAMPLE_INPUTS.items():
            self.entry_vars[name].set(value)
            self._validate_single_field(name)
        self.status_var.set("Diameter-pair sample loaded.")

    def _require_result_for_export(self) -> bool:
        if self.last_result_values is not None:
            return True
        messagebox.showinfo("Export", "Run a solve first to export results.")
        return False

    # Placeholder-friendly export methods.
    def export_csv(self) -> None:
        if not self._require_result_for_export() or self.last_result_values is None:
            return
        path = filedialog.asksaveasfilename(
            title="Export CSV",
            defaultextension=".csv",
            initialfile="spur_gear_results.csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                w = csv.writer(f)
                w.writerow(["Spur Gear Engineering Calculator", APP_VERSION])
                w.writerow([UNITS_LABEL, ""])
                w.writerow([])
                w.writerow(["Property", "Value", "Unit"])
                for field in FIELD_ORDER:
                    w.writerow(
                        [
                            FIELD_LABELS[field],
                            f"{self.last_result_values[field]:.6f}" if field != "teeth" else int(self.last_result_values[field]),
                            FIELD_UNITS[field],
                        ]
                    )
            self.status_var.set(f"CSV exported: {path}")
        except Exception as exc:
            messagebox.showerror("Export CSV", f"Failed to export CSV.\n{exc}")
            self.status_var.set("CSV export failed.")

    @staticmethod
    def _pdf_escape(text: str) -> str:
        return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

    def _write_simple_pdf(self, filepath: str, lines: List[str]) -> None:
        escaped = [self._pdf_escape(line) for line in lines]
        content = ["BT", "/F1 12 Tf", "50 790 Td", "14 TL"]
        for i, line in enumerate(escaped):
            content.append((("" if i == 0 else "T* ") + f"({line}) Tj"))
        content.append("ET")
        stream = "\n".join(content).encode("latin-1", errors="replace")
        objs = [
            b"<< /Type /Catalog /Pages 2 0 R >>",
            b"<< /Type /Pages /Count 1 /Kids [3 0 R] >>",
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>",
            b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream",
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        ]
        buff = bytearray()
        buff.extend(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
        offs = [0]
        for i, obj in enumerate(objs, 1):
            offs.append(len(buff))
            buff.extend(f"{i} 0 obj\n".encode("ascii"))
            buff.extend(obj)
            buff.extend(b"\nendobj\n")
        xref = len(buff)
        buff.extend(f"xref\n0 {len(offs)}\n".encode("ascii"))
        buff.extend(b"0000000000 65535 f \n")
        for off in offs[1:]:
            buff.extend(f"{off:010} 00000 n \n".encode("ascii"))
        buff.extend((f"trailer\n<< /Size {len(offs)} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n").encode("ascii"))
        with open(filepath, "wb") as f:
            f.write(buff)

    def export_pdf(self) -> None:
        if not self._require_result_for_export() or self.last_result_values is None:
            return
        path = filedialog.asksaveasfilename(
            title="Export PDF",
            defaultextension=".pdf",
            initialfile="spur_gear_report.pdf",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            generated = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            lines = [
                f"Spur Gear Engineering Calculator - Report ({APP_VERSION})",
                f"Generated: {generated}",
                UNITS_LABEL,
                "",
            ]
            for field in FIELD_ORDER:
                value = self.last_result_values[field]
                vtxt = f"{int(value)}" if field == "teeth" else f"{value:.6f}"
                unit = FIELD_UNITS[field]
                lines.append(f"{FIELD_LABELS[field]}: {vtxt}{(' ' + unit) if unit else ''}")
            self._write_simple_pdf(path, lines)
            self.status_var.set(f"PDF exported: {path}")
        except Exception as exc:
            messagebox.showerror("Export PDF", f"Failed to export PDF.\n{exc}")
            self.status_var.set("PDF export failed.")

    def export_png(self) -> None:
        if self.preview_canvas is None:
            return
        if self.last_result_values is None:
            messagebox.showinfo("Export Preview", "Run a solve first to generate a preview.")
            return
        if ImageGrab is None:
            messagebox.showerror("Export Preview", "PNG export requires Pillow. Install with: pip install Pillow")
            return
        path = filedialog.asksaveasfilename(
            title="Export Preview PNG",
            defaultextension=".png",
            initialfile="gear_preview.png",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            self.root.update_idletasks()
            time.sleep(0.05)
            x1 = self.preview_canvas.winfo_rootx()
            y1 = self.preview_canvas.winfo_rooty()
            x2 = x1 + self.preview_canvas.winfo_width()
            y2 = y1 + self.preview_canvas.winfo_height()
            ImageGrab.grab(bbox=(x1, y1, x2, y2)).save(path, "PNG")
            self.status_var.set(f"Preview PNG exported: {path}")
        except Exception as exc:
            messagebox.showerror("Export Preview", f"Failed to export PNG.\n{exc}")
            self.status_var.set("Preview PNG export failed.")

    def copy_results(self) -> None:
        if self.result_tree is None or not self.result_tree.get_children():
            messagebox.showinfo("Copy Results", "No solved results available yet.")
            return
        lines: List[str] = []
        for item in self.result_tree.get_children():
            name, value = self.result_tree.item(item, "values")
            lines.append(f"{name}: {value}")
        text = f"Spur Gear Engineering Calculator {APP_VERSION}\n{UNITS_LABEL}\n\n" + "\n".join(lines)
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.status_var.set("Solved values copied to clipboard.")

    def _update_zoom_label(self) -> None:
        self.preview_zoom_var.set(f"{int(round(self.preview_zoom * 100))}%")

    def preview_zoom_in(self) -> None:
        self.preview_zoom = min(self.preview_zoom * 1.12, 3.0)
        self._update_zoom_label()
        self.update_preview(self.last_result_values)

    def preview_zoom_out(self) -> None:
        self.preview_zoom = max(self.preview_zoom / 1.12, 0.5)
        self._update_zoom_label()
        self.update_preview(self.last_result_values)

    def preview_fit_view(self) -> None:
        self.preview_pan_x = 0.0
        self.preview_pan_y = 0.0
        self.preview_zoom = self._calculate_fit_zoom()
        self._update_zoom_label()
        self.update_preview(self.last_result_values)

    def preview_reset_view(self) -> None:
        self.preview_fit_view()

    def _on_preview_mousewheel(self, event: tk.Event) -> None:
        if event.delta > 0:
            self.preview_zoom_in()
        elif event.delta < 0:
            self.preview_zoom_out()

    def _on_preview_pan_start(self, event: tk.Event) -> None:
        self.preview_drag_start_x = event.x
        self.preview_drag_start_y = event.y

    def _on_preview_pan_move(self, event: tk.Event) -> None:
        dx = event.x - self.preview_drag_start_x
        dy = event.y - self.preview_drag_start_y
        self.preview_drag_start_x = event.x
        self.preview_drag_start_y = event.y
        self.preview_pan_x += dx
        self.preview_pan_y += dy
        self.update_preview(self.last_result_values)

    def _calculate_fit_zoom(self) -> float:
        if self.preview_canvas is None or self.last_result_values is None:
            return 1.0
        width = max(1, self.preview_canvas.winfo_width())
        height = max(1, self.preview_canvas.winfo_height())
        if width <= 1 or height <= 1:
            width = int(self.preview_canvas.cget("width"))
            height = int(self.preview_canvas.cget("height"))

        od = max(1e-9, self.last_result_values["outside_diameter"])
        pd = max(1e-9, self.last_result_values["pitch_diameter"])
        rd = max(1e-9, self.last_result_values["root_diameter"])
        bd = max(1e-9, self.last_result_values["base_diameter"])
        max_d = max(od, pd, rd, bd)

        base_scale = min(width, height) * 0.36 / max_d
        base_radius = (od * 0.5) * base_scale

        legend_w = max(250, min(360, int(width * 0.38)))
        cx = width * 0.30
        max_radius_x = max(28.0, min(cx - 24.0, (width - legend_w - 56.0) - cx))
        max_radius_y = max(28.0, min(height * 0.42, (height * 0.50) - 24.0))
        fit_radius = max(24.0, min(max_radius_x, max_radius_y))
        fit_zoom = fit_radius / max(base_radius, 1e-9)
        return max(0.45, min(2.6, fit_zoom))

    def show_about_dialog(self) -> None:
        formula_lines = [
            f"Spur Gear Engineering Calculator {APP_VERSION}",
            "",
            "Metric Spur Gear Engineering Calculator",
            UNITS_LABEL,
            "",
            "Core formulas:",
            "- Pitch diameter d = m x z",
            "- Outside diameter da = m x (z + 2)",
            "- Root diameter df = m x (z - 2.5)",
            "- Base diameter db = d x cos(phi)",
            "",
            "Assumptions:",
            "- Standard full-depth metric spur gear",
            "- Addendum = m",
            "- Dedendum = 1.25m",
            "- Tooth thickness = circular pitch / 2",
            f"- Default pressure angle = {DEFAULT_PRESSURE_ANGLE:.1f} deg",
        ]
        messagebox.showinfo("Help / About", "\n".join(formula_lines))


def run() -> None:
    root = ctk.CTk()
    SpurGearCalculatorApp(root)
    root.mainloop()
