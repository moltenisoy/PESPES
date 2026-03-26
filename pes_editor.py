"""
pes_editor.py – Punto de entrada principal del Editor/Patcher de PES EXE.

Uso:
    python pes_editor.py

Requisitos:
    - Python 3.7+
    - Tkinter (incluido en la instalación estándar de Python en Windows/Linux/macOS)
    - Módulos del proyecto: offsets.py, binary_handler.py, gui_app.py

Estructura del proyecto:
    pes_editor.py       ← este archivo (punto de entrada)
    gui_app.py          ← interfaz gráfica Tkinter
    binary_handler.py   ← lectura/escritura binaria del ejecutable
    offsets.py          ← definición de offsets y tipos de datos

Configuración de offsets:
    Edite offsets.py para actualizar los offsets reales del ejecutable que
    desea parchear. Los valores incluidos son ejemplos basados en el análisis
    técnico de PES6.EXE y deben verificarse contra el ejecutable específico.

Notas de seguridad:
    - Se crea una copia de seguridad automática antes de sobrescribir el archivo.
    - Los valores se validan contra rangos definidos en offsets.py antes de escribirse.
    - Los datos se procesan en memoria hasta que el usuario confirma el guardado.
"""

import sys
import tkinter as tk


def check_python_version():
    """Verifica que la versión de Python sea 3.7 o superior."""
    if sys.version_info < (3, 7):
        print(
            f"Error: Se requiere Python 3.7 o superior. "
            f"Versión actual: {sys.version_info.major}.{sys.version_info.minor}"
        )
        sys.exit(1)


def check_tkinter():
    """Verifica que Tkinter esté disponible."""
    try:
        import tkinter  # noqa: F401
    except ImportError:
        print(
            "Error: Tkinter no está disponible.\n"
            "En Linux instálelo con: sudo apt-get install python3-tk\n"
            "En Windows/macOS suele estar incluido con Python."
        )
        sys.exit(1)


def main():
    """Inicializa y ejecuta la aplicación."""
    check_python_version()
    check_tkinter()

    # Importación diferida para capturar errores de módulo con mensaje claro.
    try:
        from gui_app import PESEditorApp
    except ImportError as exc:
        print(
            f"Error al importar módulos del proyecto: {exc}\n"
            "Asegúrese de que gui_app.py, binary_handler.py y offsets.py "
            "estén en el mismo directorio que pes_editor.py."
        )
        sys.exit(1)

    app = PESEditorApp()

    # Centrar la ventana en la pantalla al iniciar.
    app.update_idletasks()
    screen_w = app.winfo_screenwidth()
    screen_h = app.winfo_screenheight()
    win_w = app.winfo_width()
    win_h = app.winfo_height()
    x = (screen_w - win_w) // 2
    y = (screen_h - win_h) // 2
    app.geometry(f"{win_w}x{win_h}+{x}+{y}")

    app.mainloop()


if __name__ == "__main__":
    main()
