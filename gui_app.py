"""
gui_app.py – Interfaz gráfica principal del Editor/Patcher de PES EXE.

Tecnología: Tkinter (incluido en la biblioteca estándar de Python 3).

Estructura de la interfaz:
  - Barra de herramientas (cargar archivo, guardar, guardar como).
  - Barra de estado inferior con información del archivo cargado.
  - Área central con pestañas (Notebook) por categoría de parámetros.
  - Cada pestaña muestra una lista de parámetros con controles apropiados
    según el tipo de dato:
      · float  → Spinbox + botones ↑↓ + entrada de incremento.
      · int*   → Spinbox de enteros.
      · uint*  → Spinbox de enteros sin signo.
      · bool   → Checkbutton.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import struct
import os

from binary_handler import BinaryHandler, BinaryFileError, OffsetOutOfRangeError
from offsets import OFFSET_DEFINITIONS, GLOBAL_CONSTANTS, warn_if_example_offsets


# ---------------------------------------------------------------------------
# Widget personalizado para valores float con control fino
# ---------------------------------------------------------------------------

class BoolControl(tk.Frame):
    """Checkbutton para valores booleanos."""

    def __init__(self, master, initial: bool, **kwargs):
        super().__init__(master, **kwargs)
        self._var = tk.BooleanVar(value=bool(initial))
        cb = tk.Checkbutton(self, variable=self._var, bg=kwargs.get("bg", "white"))
        cb.pack(side=tk.LEFT)

    def get(self) -> bool:
        return self._var.get()

    def set(self, value) -> None:
        self._var.set(bool(value))
    """
    Control compuesto para editar valores float con precisión controlada.

    Contiene:
      - Un Entry para el valor actual.
      - Un Entry para el incremento.
      - Botones ▲ y ▼ para ajuste fino.
      - Un Slider (Scale) para ajuste rápido en el rango permitido.
    """

    def __init__(self, master, min_val: float, max_val: float,
                 step: float, initial: float, **kwargs):
        super().__init__(master, **kwargs)
        self.min_val = float(min_val)
        self.max_val = float(max_val)
        self._step = tk.DoubleVar(value=step)
        self._value = tk.DoubleVar(value=initial)

        self._build()

    def _build(self):
        # --- Fila 1: entry de valor + botones de flecha ---
        row1 = tk.Frame(self)
        row1.pack(fill=tk.X)

        self._entry = tk.Entry(row1, textvariable=self._value, width=14, justify="right")
        self._entry.pack(side=tk.LEFT, padx=(0, 2))
        self._entry.bind("<FocusOut>", self._clamp_entry)
        self._entry.bind("<Return>", self._clamp_entry)

        btn_up = tk.Button(row1, text="▲", width=2, command=self._increment)
        btn_up.pack(side=tk.LEFT)
        btn_dn = tk.Button(row1, text="▼", width=2, command=self._decrement)
        btn_dn.pack(side=tk.LEFT)

        # --- Fila 2: label "Paso:" + entry de incremento ---
        row2 = tk.Frame(self)
        row2.pack(fill=tk.X, pady=(2, 0))

        tk.Label(row2, text="Paso:", font=("TkDefaultFont", 7)).pack(side=tk.LEFT)
        self._step_entry = tk.Entry(row2, textvariable=self._step, width=8, justify="right")
        self._step_entry.pack(side=tk.LEFT, padx=(2, 0))

        # --- Fila 3: Slider ---
        self._slider = tk.Scale(
            self,
            from_=self.min_val,
            to=self.max_val,
            orient=tk.HORIZONTAL,
            resolution=(self.max_val - self.min_val) / 1000.0,
            variable=self._value,
            showvalue=False,
            length=180,
        )
        self._slider.pack(fill=tk.X, pady=(2, 0))

    def _increment(self):
        try:
            step = float(self._step.get())
        except (tk.TclError, ValueError):
            step = 0.1
        self._value.set(round(min(self._value.get() + step, self.max_val), 6))

    def _decrement(self):
        try:
            step = float(self._step.get())
        except (tk.TclError, ValueError):
            step = 0.1
        self._value.set(round(max(self._value.get() - step, self.min_val), 6))

    def _clamp_entry(self, _event=None):
        try:
            v = float(self._value.get())
            v = max(self.min_val, min(self.max_val, v))
            self._value.set(round(v, 6))
        except (tk.TclError, ValueError):
            self._value.set(self.min_val)

    def get(self) -> float:
        try:
            v = float(self._value.get())
        except (tk.TclError, ValueError):
            v = self.min_val
        return round(max(self.min_val, min(self.max_val, v)), 6)

    def set(self, value: float):
        self._value.set(round(float(value), 6))


# ---------------------------------------------------------------------------
# Widget para valores enteros con Spinbox
# ---------------------------------------------------------------------------

class IntControl(tk.Frame):
    """Spinbox para valores enteros (int / uint)."""

    def __init__(self, master, min_val: int, max_val: int,
                 initial: int, **kwargs):
        super().__init__(master, **kwargs)
        self.min_val = int(min_val)
        self.max_val = int(max_val)
        self._value = tk.StringVar(value=str(initial))
        self._build()

    def _build(self):
        self._spinbox = tk.Spinbox(
            self,
            from_=self.min_val,
            to=self.max_val,
            textvariable=self._value,
            width=14,
            justify="right",
        )
        self._spinbox.pack(side=tk.LEFT)

    def get(self) -> int:
        try:
            v = int(self._value.get())
        except (tk.TclError, ValueError):
            v = self.min_val
        return max(self.min_val, min(self.max_val, v))

    def set(self, value: int):
        self._value.set(str(int(value)))


# ---------------------------------------------------------------------------
# Aplicación principal
# ---------------------------------------------------------------------------

class PESEditorApp(tk.Tk):
    """Ventana principal del Editor/Patcher de PES EXE."""

    APP_TITLE = "PES EXE Editor / Patcher"
    WINDOW_SIZE = "1100x700"

    def __init__(self):
        super().__init__()
        self.title(self.APP_TITLE)
        self.geometry(self.WINDOW_SIZE)
        self.minsize(800, 500)

        self._handler = BinaryHandler()
        # Diccionario {(category, label): widget_control}
        self._controls: dict = {}

        self._build_menu()
        self._build_toolbar()
        self._build_main_area()
        self._build_statusbar()

        self._set_controls_state(enabled=False)

    # ------------------------------------------------------------------
    # Construcción de la interfaz
    # ------------------------------------------------------------------

    def _build_menu(self):
        menubar = tk.Menu(self)

        # Menú Archivo
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Abrir ejecutable…", accelerator="Ctrl+O",
                              command=self._open_file)
        file_menu.add_separator()
        file_menu.add_command(label="Aplicar y guardar (sobrescribir)", accelerator="Ctrl+S",
                              command=lambda: self._save(overwrite=True))
        file_menu.add_command(label="Guardar como…", accelerator="Ctrl+Shift+S",
                              command=lambda: self._save(overwrite=False))
        file_menu.add_separator()
        file_menu.add_command(label="Salir", command=self.quit)
        menubar.add_cascade(label="Archivo", menu=file_menu)

        # Menú Editar
        edit_menu = tk.Menu(menubar, tearoff=0)
        edit_menu.add_command(label="Recargar valores desde archivo",
                              command=self._reload_values)
        menubar.add_cascade(label="Editar", menu=edit_menu)

        # Menú Ayuda
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Acerca de…", command=self._show_about)
        menubar.add_cascade(label="Ayuda", menu=help_menu)

        self.config(menu=menubar)
        self.bind("<Control-o>", lambda _e: self._open_file())
        self.bind("<Control-s>", lambda _e: self._save(overwrite=True))

    def _build_toolbar(self):
        toolbar = tk.Frame(self, bd=1, relief=tk.RIDGE)
        toolbar.pack(side=tk.TOP, fill=tk.X)

        self._btn_open = tk.Button(toolbar, text="📂 Abrir EXE",
                                   command=self._open_file, relief=tk.FLAT,
                                   padx=8, pady=4)
        self._btn_open.pack(side=tk.LEFT, padx=2, pady=2)

        self._btn_reload = tk.Button(toolbar, text="🔄 Recargar",
                                     command=self._reload_values, relief=tk.FLAT,
                                     padx=8, pady=4)
        self._btn_reload.pack(side=tk.LEFT, padx=2, pady=2)

        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(
            side=tk.LEFT, fill=tk.Y, padx=4, pady=2
        )

        self._btn_patch = tk.Button(toolbar, text="💾 Parchear (guardar)",
                                    command=lambda: self._save(overwrite=True),
                                    relief=tk.FLAT, padx=8, pady=4,
                                    background="#4CAF50", foreground="white")
        self._btn_patch.pack(side=tk.LEFT, padx=2, pady=2)

        self._btn_save_as = tk.Button(toolbar, text="💾 Guardar como…",
                                      command=lambda: self._save(overwrite=False),
                                      relief=tk.FLAT, padx=8, pady=4)
        self._btn_save_as.pack(side=tk.LEFT, padx=2, pady=2)

        # Información del archivo a la derecha
        self._lbl_file = tk.Label(toolbar, text="Sin archivo cargado",
                                   font=("TkDefaultFont", 9, "italic"),
                                   foreground="gray")
        self._lbl_file.pack(side=tk.RIGHT, padx=10)

    def _build_main_area(self):
        """Crea el Notebook con pestañas por categoría."""
        container = tk.Frame(self)
        container.pack(fill=tk.BOTH, expand=True, padx=6, pady=4)

        self._notebook = ttk.Notebook(container)
        self._notebook.pack(fill=tk.BOTH, expand=True)

        for category, params in OFFSET_DEFINITIONS.items():
            self._build_category_tab(category, params)

        # Pestaña de constantes globales
        self._build_global_constants_tab()

    def _build_category_tab(self, category: str, params: list):
        """Construye una pestaña para una categoría de parámetros."""
        # Canvas + Scrollbar para lista larga de parámetros
        outer = tk.Frame(self._notebook)
        outer.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(outer, borderwidth=0)
        scrollbar = ttk.Scrollbar(outer, orient=tk.VERTICAL, command=canvas.yview)
        scroll_frame = tk.Frame(canvas)

        scroll_frame.bind(
            "<Configure>",
            lambda e, c=canvas: c.configure(scrollregion=c.bbox("all")),
        )
        canvas.create_window((0, 0), window=scroll_frame, anchor=tk.NW)
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Cabecera de columnas
        headers = ["Parámetro", "Offset (hex)", "Tipo", "Valor actual", "Rango"]
        col_widths = [240, 100, 70, 220, 140]
        header_frame = tk.Frame(scroll_frame, bg="#2b2b2b")
        header_frame.pack(fill=tk.X, pady=(0, 2))
        for i, (h, w) in enumerate(zip(headers, col_widths)):
            tk.Label(header_frame, text=h, bg="#2b2b2b", fg="white",
                     font=("TkDefaultFont", 9, "bold"),
                     width=w // 8, anchor="w").grid(row=0, column=i, padx=4, pady=3, sticky="w")

        # Filas de parámetros
        for row_idx, param in enumerate(params):
            bg = "#f5f5f5" if row_idx % 2 == 0 else "white"
            self._build_param_row(scroll_frame, category, param, row_idx + 1, bg)

        self._notebook.add(outer, text=category)

    def _build_param_row(self, parent, category: str, param: dict,
                         row: int, bg: str):
        """Construye una fila en la tabla de parámetros."""
        row_frame = tk.Frame(parent, bg=bg, relief=tk.FLAT)
        row_frame.pack(fill=tk.X, padx=2, pady=1)

        label_text = param["label"]
        offset_text = f"0x{param['offset']:08X}"
        type_text = param["type"]
        range_text = f"{param['min']} … {param['max']}"

        # Columna 1: nombre del parámetro con tooltip (descripción)
        lbl = tk.Label(row_frame, text=label_text, bg=bg,
                       font=("TkDefaultFont", 9), anchor="w", width=30)
        lbl.grid(row=0, column=0, padx=6, pady=4, sticky="w")
        self._add_tooltip(lbl, param.get("description", ""))

        # Columna 2: offset
        tk.Label(row_frame, text=offset_text, bg=bg,
                 font=("Courier", 9), foreground="#555555",
                 width=12, anchor="w").grid(row=0, column=1, padx=4, sticky="w")

        # Columna 3: tipo
        tk.Label(row_frame, text=type_text, bg=bg,
                 font=("TkDefaultFont", 8), foreground="#888888",
                 width=8, anchor="w").grid(row=0, column=2, padx=4, sticky="w")

        # Columna 4: control de edición
        control = self._build_control(row_frame, param, bg)
        control.grid(row=0, column=3, padx=4, sticky="w")
        self._controls[(category, label_text)] = (param, control)

        # Columna 5: rango
        tk.Label(row_frame, text=range_text, bg=bg,
                 font=("TkDefaultFont", 8), foreground="#999999",
                 width=18, anchor="w").grid(row=0, column=4, padx=4, sticky="w")

    def _build_control(self, parent, param: dict, bg: str) -> tk.Widget:
        """Crea y devuelve el widget de control apropiado para el tipo de dato."""
        ptype = param["type"]
        initial = param.get("default", param["min"])

        if ptype == "bool":
            ctrl = BoolControl(parent, initial=bool(initial), bg=bg)
            return ctrl

        if ptype == "float":
            ctrl = FloatControl(
                parent,
                min_val=param["min"],
                max_val=param["max"],
                step=param.get("step", 0.1),
                initial=float(initial),
                bg=bg,
            )
            return ctrl

        # Tipos enteros (int8, int16, int32, uint8, uint16, uint32)
        ctrl = IntControl(
            parent,
            min_val=int(param["min"]),
            max_val=int(param["max"]),
            initial=int(initial),
            bg=bg,
        )
        return ctrl

    def _build_global_constants_tab(self):
        """Pestaña de constantes globales del juego."""
        outer = tk.Frame(self._notebook)
        canvas = tk.Canvas(outer, borderwidth=0)
        scrollbar = ttk.Scrollbar(outer, orient=tk.VERTICAL, command=canvas.yview)
        scroll_frame = tk.Frame(canvas)

        scroll_frame.bind(
            "<Configure>",
            lambda e, c=canvas: c.configure(scrollregion=c.bbox("all")),
        )
        canvas.create_window((0, 0), window=scroll_frame, anchor=tk.NW)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        category = "Constantes Globales"
        for row_idx, (name, param) in enumerate(GLOBAL_CONSTANTS.items()):
            param = dict(param)
            param["label"] = name
            bg = "#f5f5f5" if row_idx % 2 == 0 else "white"
            self._build_param_row(scroll_frame, category, param, row_idx, bg)

        self._notebook.add(outer, text=category)

    def _build_statusbar(self):
        status_bar = tk.Frame(self, bd=1, relief=tk.SUNKEN)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        self._status_var = tk.StringVar(value="Listo. Abra un archivo ejecutable para comenzar.")
        tk.Label(status_bar, textvariable=self._status_var,
                 anchor=tk.W, font=("TkDefaultFont", 9)).pack(side=tk.LEFT, padx=6)

        self._size_var = tk.StringVar(value="")
        tk.Label(status_bar, textvariable=self._size_var,
                 anchor=tk.E, font=("TkDefaultFont", 9),
                 foreground="gray").pack(side=tk.RIGHT, padx=6)

    # ------------------------------------------------------------------
    # Acciones del usuario
    # ------------------------------------------------------------------

    def _open_file(self):
        """Abre un diálogo para seleccionar y cargar el ejecutable."""
        filepath = filedialog.askopenfilename(
            title="Seleccionar ejecutable",
            filetypes=[("Ejecutables", "*.exe"), ("Todos los archivos", "*.*")],
        )
        if not filepath:
            return

        try:
            self._handler.load(filepath)
        except (FileNotFoundError, BinaryFileError) as exc:
            messagebox.showerror("Error al cargar", str(exc))
            return

        self._lbl_file.config(
            text=os.path.basename(filepath),
            foreground="black",
            font=("TkDefaultFont", 9, "bold"),
        )
        size_kb = self._handler.file_size() / 1024
        self._size_var.set(f"Tamaño: {size_kb:,.1f} KB  |  {filepath}")

        self._reload_values()
        self._set_controls_state(enabled=True)
        self._status("Archivo cargado correctamente: " + os.path.basename(filepath))

        # Advertir al usuario si se están usando offsets de ejemplo no verificados.
        warning = warn_if_example_offsets()
        if warning:
            messagebox.showwarning("Offsets de ejemplo", warning)

    def _reload_values(self):
        """Lee los valores actuales del archivo y actualiza los controles."""
        if not self._handler.is_loaded():
            return

        errors = []
        for (category, label), (param, control) in self._controls.items():
            try:
                value = self._handler.read_value(param["offset"], param["type"])
                control.set(value)
            except (OffsetOutOfRangeError, struct.error) as exc:
                errors.append(f"  • [{category}] {label}: {exc}")

        if errors:
            msg = "No se pudieron leer algunos valores:\n" + "\n".join(errors[:10])
            if len(errors) > 10:
                msg += f"\n  … y {len(errors) - 10} más."
            messagebox.showwarning("Advertencia de lectura", msg)
            self._status(f"Valores cargados con {len(errors)} advertencia(s).")
        else:
            self._status("Valores actualizados desde el archivo.")

    def _save(self, overwrite: bool):
        """Valida y aplica los cambios al archivo."""
        if not self._handler.is_loaded():
            messagebox.showwarning("Sin archivo", "Primero cargue un ejecutable.")
            return

        if overwrite:
            confirmed = messagebox.askyesno(
                "Confirmar parcheo",
                "¿Desea sobrescribir el archivo original con los nuevos valores?\n\n"
                "Se creará una copia de seguridad automáticamente.",
            )
            if not confirmed:
                return
        else:
            dest = filedialog.asksaveasfilename(
                title="Guardar archivo parcheado como…",
                defaultextension=".exe",
                filetypes=[("Ejecutable", "*.exe"), ("Todos los archivos", "*.*")],
                initialfile=os.path.basename(self._handler.filepath),
            )
            if not dest:
                return

        # Recopilar y validar todos los valores de la interfaz
        write_ops = []
        errors = []
        for (category, label), (param, control) in self._controls.items():
            try:
                value = control.get()
                # Validar rango
                if value < param["min"] or value > param["max"]:
                    errors.append(
                        f"  • [{category}] {label}: valor {value} fuera de rango "
                        f"[{param['min']}, {param['max']}]"
                    )
                else:
                    write_ops.append((param["offset"], param["type"], value))
            except Exception as exc:
                errors.append(f"  • [{category}] {label}: {exc}")

        if errors:
            messagebox.showerror(
                "Errores de validación",
                "Corrija los siguientes valores antes de guardar:\n" + "\n".join(errors),
            )
            return

        # Aplicar todos los cambios al buffer en memoria
        write_errors = []
        for offset, type_name, value in write_ops:
            try:
                self._handler.write_value(offset, type_name, value)
            except (OffsetOutOfRangeError, struct.error, ValueError) as exc:
                write_errors.append(f"  0x{offset:08X}: {exc}")

        if write_errors:
            if not messagebox.askyesno(
                "Errores de escritura",
                f"Se produjeron {len(write_errors)} errores al escribir:\n"
                + "\n".join(write_errors[:5])
                + "\n\n¿Desea continuar guardando de todas formas?",
            ):
                return

        # Persistir en disco
        try:
            if overwrite:
                backup_path = self._handler.save(backup=True)
                msg = "Archivo parcheado correctamente."
                if backup_path:
                    msg += f"\nBackup guardado en:\n{backup_path}"
                messagebox.showinfo("Guardado", msg)
                self._status("Archivo guardado. Backup: " + os.path.basename(backup_path or ""))
            else:
                self._handler.save_as(dest)
                messagebox.showinfo(
                    "Guardado", f"Archivo guardado como:\n{dest}"
                )
                self._status("Guardado como: " + dest)
        except (BinaryFileError, OSError) as exc:
            messagebox.showerror("Error al guardar", str(exc))

    # ------------------------------------------------------------------
    # Utilidades de interfaz
    # ------------------------------------------------------------------

    def _set_controls_state(self, enabled: bool):
        """Activa o desactiva los botones que requieren un archivo cargado."""
        state = tk.NORMAL if enabled else tk.DISABLED
        self._btn_reload.config(state=state)
        self._btn_patch.config(state=state)
        self._btn_save_as.config(state=state)

    def _status(self, message: str):
        """Actualiza el mensaje de la barra de estado."""
        self._status_var.set(message)

    @staticmethod
    def _add_tooltip(widget: tk.Widget, text: str):
        """Agrega un tooltip simple (ventana emergente) a un widget."""
        if not text:
            return

        tip_window = None

        def show(_event):
            nonlocal tip_window
            if tip_window or not text:
                return
            x = widget.winfo_rootx() + 20
            y = widget.winfo_rooty() + widget.winfo_height() + 4
            tip_window = tw = tk.Toplevel(widget)
            tw.wm_overrideredirect(True)
            tw.wm_geometry(f"+{x}+{y}")
            label = tk.Label(
                tw, text=text, justify=tk.LEFT,
                background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                font=("TkDefaultFont", 8), wraplength=300,
            )
            label.pack(ipadx=4, ipady=2)

        def hide(_event):
            nonlocal tip_window
            if tip_window:
                tip_window.destroy()
                tip_window = None

        widget.bind("<Enter>", show)
        widget.bind("<Leave>", hide)

    def _show_about(self):
        messagebox.showinfo(
            "Acerca de PES EXE Editor",
            "PES EXE Editor / Patcher\n"
            "Versión 1.0\n\n"
            "Editor visual de parámetros internos de ejecutables compatibles con PES6.\n\n"
            "Permite leer y modificar valores de física, balón, sistema de disparo,\n"
            "aleatoriedad (RNG) y estadísticas de jugadores directamente en el binario.\n\n"
            "Los offsets deben configurarse en offsets.py según el ejecutable analizado.",
        )
