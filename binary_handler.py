"""
binary_handler.py – Módulo de manejo de archivos binarios para PES EXE Editor.

Proporciona funciones para:
  - Abrir y cerrar el ejecutable.
  - Leer valores tipados desde un offset del archivo.
  - Escribir valores tipados en un offset del archivo.
  - Crear copias de seguridad automáticas.
  - Guardar como nuevo archivo o sobrescribir el original.
"""

import os
import shutil
import struct
from datetime import datetime
from offsets import TYPE_FORMAT


class BinaryFileError(Exception):
    """Excepción base para errores de manejo de archivos binarios."""


class OffsetOutOfRangeError(BinaryFileError):
    """El offset solicitado está fuera del rango del archivo."""


class BinaryHandler:
    """
    Gestiona la lectura y escritura de valores binarios en un ejecutable PE.

    Attributes:
        filepath (str): Ruta al archivo binario cargado.
        data (bytearray): Copia del contenido del archivo en memoria.
    """

    # Tamaño mínimo aceptable del ejecutable (en bytes).
    MIN_FILE_SIZE = 1024 * 10  # 10 KB

    def __init__(self):
        self.filepath: str = ""
        self.data: bytearray = bytearray()

    # ------------------------------------------------------------------
    # Carga y validación del archivo
    # ------------------------------------------------------------------

    def load(self, filepath: str) -> None:
        """
        Carga el ejecutable en memoria.

        Args:
            filepath: Ruta absoluta al archivo .exe.

        Raises:
            FileNotFoundError: Si el archivo no existe.
            BinaryFileError: Si el archivo no cumple la validación mínima.
        """
        if not os.path.isfile(filepath):
            raise FileNotFoundError(f"Archivo no encontrado: {filepath}")

        file_size = os.path.getsize(filepath)
        if file_size < self.MIN_FILE_SIZE:
            raise BinaryFileError(
                f"El archivo es demasiado pequeño ({file_size} bytes). "
                f"Se esperan al menos {self.MIN_FILE_SIZE} bytes."
            )

        with open(filepath, "rb") as fh:
            raw = fh.read()

        # Validar firma MZ (todos los ejecutables PE comienzan con 'MZ').
        if len(raw) < 2 or raw[:2] != b"MZ":
            raise BinaryFileError(
                "El archivo no parece ser un ejecutable PE válido (falta firma 'MZ')."
            )

        # Validar firma PE ("PE\0\0") a partir del offset indicado en el DOS header.
        # El campo e_lfanew (offset del PE header) está en los bytes 0x3C-0x3F del DOS header.
        if len(raw) >= 0x40:
            pe_offset = struct.unpack_from("<I", raw, 0x3C)[0]
            if pe_offset + 4 <= len(raw):
                pe_sig = raw[pe_offset : pe_offset + 4]
                if pe_sig != b"PE\x00\x00":
                    raise BinaryFileError(
                        f"El archivo no contiene una cabecera PE válida "
                        f"(se esperaba 'PE\\0\\0' en offset 0x{pe_offset:X})."
                    )

        self.filepath = filepath
        self.data = bytearray(raw)

    def is_loaded(self) -> bool:
        """Devuelve True si hay un archivo cargado en memoria."""
        return len(self.data) > 0

    # ------------------------------------------------------------------
    # Lectura de valores
    # ------------------------------------------------------------------

    def read_value(self, offset: int, type_name: str):
        """
        Lee un valor desde el offset indicado del archivo en memoria.

        Args:
            offset:    Offset en bytes desde el inicio del archivo.
            type_name: Nombre del tipo de dato (ver TYPE_FORMAT en offsets.py).

        Returns:
            El valor interpretado según el tipo de dato.

        Raises:
            KeyError:             Si type_name no es reconocido.
            OffsetOutOfRangeError: Si el offset está fuera del rango del archivo.
        """
        fmt, size = self._resolve_type(type_name)
        self._validate_range(offset, size)

        raw = bytes(self.data[offset : offset + size])
        value = struct.unpack(fmt, raw)[0]

        # Normalizar booleano a True/False puro.
        if type_name == "bool":
            return bool(value)
        return value

    # ------------------------------------------------------------------
    # Escritura de valores
    # ------------------------------------------------------------------

    def write_value(self, offset: int, type_name: str, value) -> None:
        """
        Escribe un valor en el offset indicado del buffer en memoria.

        Los cambios no se persisten hasta llamar a save() o save_as().

        Args:
            offset:    Offset en bytes desde el inicio del archivo.
            type_name: Nombre del tipo de dato.
            value:     Valor a escribir; debe ser compatible con type_name.

        Raises:
            KeyError:             Si type_name no es reconocido.
            OffsetOutOfRangeError: Si el offset está fuera del rango del archivo.
            ValueError:           Si value no puede convertirse al tipo indicado.
        """
        fmt, size = self._resolve_type(type_name)
        self._validate_range(offset, size)

        # Conversión de tipos para compatibilidad con struct.pack.
        if type_name == "bool":
            value = int(bool(value))
        elif type_name in ("float",):
            value = float(value)
        else:
            value = int(value)

        packed = struct.pack(fmt, value)
        self.data[offset : offset + size] = packed

    # ------------------------------------------------------------------
    # Guardado del archivo
    # ------------------------------------------------------------------

    def save(self, backup: bool = True) -> str:
        """
        Sobrescribe el archivo original con el contenido modificado.

        Args:
            backup: Si True, crea una copia de seguridad antes de guardar.

        Returns:
            Ruta del archivo de backup creado (o cadena vacía si backup=False).

        Raises:
            BinaryFileError: Si no hay archivo cargado.
        """
        self._require_loaded()
        backup_path = ""
        if backup:
            backup_path = self._create_backup()
        with open(self.filepath, "wb") as fh:
            fh.write(self.data)
        return backup_path

    def save_as(self, dest_filepath: str) -> None:
        """
        Guarda el contenido modificado en un nuevo archivo.

        Args:
            dest_filepath: Ruta del archivo de destino.

        Raises:
            BinaryFileError: Si no hay archivo cargado.
        """
        self._require_loaded()
        with open(dest_filepath, "wb") as fh:
            fh.write(self.data)

    # ------------------------------------------------------------------
    # Backup
    # ------------------------------------------------------------------

    def _create_backup(self) -> str:
        """
        Crea una copia de seguridad del archivo original.

        La copia se guarda en el mismo directorio con un sufijo de timestamp.

        Returns:
            Ruta completa del archivo de backup.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base, ext = os.path.splitext(self.filepath)
        backup_path = f"{base}_backup_{timestamp}{ext}"
        shutil.copy2(self.filepath, backup_path)
        return backup_path

    # ------------------------------------------------------------------
    # Utilidades internas
    # ------------------------------------------------------------------

    def _resolve_type(self, type_name: str):
        """Devuelve (fmt, size) para el tipo dado, o lanza KeyError."""
        if type_name not in TYPE_FORMAT:
            raise KeyError(
                f"Tipo de dato desconocido: '{type_name}'. "
                f"Tipos válidos: {list(TYPE_FORMAT.keys())}"
            )
        return TYPE_FORMAT[type_name]

    def _validate_range(self, offset: int, size: int) -> None:
        """Verifica que [offset, offset+size) esté dentro del buffer."""
        end = offset + size
        if offset < 0 or end > len(self.data):
            raise OffsetOutOfRangeError(
                f"Offset 0x{offset:08X} + {size} bytes está fuera del rango del archivo "
                f"(tamaño: {len(self.data)} bytes)."
            )

    def _require_loaded(self) -> None:
        """Lanza BinaryFileError si no hay archivo cargado."""
        if not self.is_loaded():
            raise BinaryFileError("No hay ningún archivo cargado. Use load() primero.")

    # ------------------------------------------------------------------
    # Información del archivo
    # ------------------------------------------------------------------

    def file_size(self) -> int:
        """Tamaño del archivo en bytes (0 si no está cargado)."""
        return len(self.data)

    def read_bytes_hex(self, offset: int, count: int = 16) -> str:
        """
        Devuelve una representación hexadecimal de 'count' bytes desde 'offset'.

        Útil para depuración.
        """
        if not self.is_loaded():
            return ""
        end = min(offset + count, len(self.data))
        raw = self.data[offset:end]
        return " ".join(f"{b:02X}" for b in raw)
