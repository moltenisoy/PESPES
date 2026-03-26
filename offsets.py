"""
offsets.py – Definición centralizada de offsets y estructuras del ejecutable PES6.

Cada entrada en OFFSET_DEFINITIONS describe un parámetro editable con los campos:
  - offset (int)   : Offset en bytes desde el inicio del archivo binario.
  - type   (str)   : Tipo de dato: 'float', 'int8', 'int16', 'int32',
                                   'uint8', 'uint16', 'uint32', 'bool'.
  - label  (str)   : Nombre descriptivo que se mostrará en la interfaz.
  - min    (num)   : Valor mínimo permitido (validación de rango).
  - max    (num)   : Valor máximo permitido.
  - step   (num)   : Incremento por defecto para controles de tipo float.
  - description (str): Descripción breve del parámetro.

NOTAS SOBRE OFFSETS:
  Los offsets listados corresponden a las posiciones en el ARCHIVO (file offset),
  no a las direcciones virtuales de tiempo de ejecución. Para convertir una
  dirección virtual (VA) al offset de archivo se usa:
      file_offset = VA - ImageBase - section_VA + section_raw_offset
  Para PES6.EXE (ImageBase = 0x00400000) los offsets se calcularon a partir
  del análisis de la sección .data del ejecutable.

  Los valores marcados con "# [EJEMPLO]" son offsets de referencia; ajustar
  con los valores reales del ejecutable analizado.

ADVERTENCIA:
  Los offsets marcados como [EJEMPLO] son valores de referencia extraídos del
  análisis técnico y deben verificarse contra el ejecutable concreto antes de
  utilizarlos. Aplicar patches con offsets incorrectos puede corromper el
  ejecutable. Se recomienda trabajar siempre con una copia del archivo original.
"""

# ---------------------------------------------------------------------------
# Estructura de categorías y parámetros
# ---------------------------------------------------------------------------
OFFSET_DEFINITIONS = {

    # -----------------------------------------------------------------------
    # Física de jugadores
    # -----------------------------------------------------------------------
    "Física de Jugadores": [
        {
            "label": "Velocidad máxima (base)",
            "offset": 0x03BE09D8,   # VA: _DAT_03be09d8 [EJEMPLO]
            "type": "float",
            "min": 0.0,
            "max": 32000.0,
            "step": 0.5,
            "description": "Velocidad máxima base de un jugador (en unidades internas ~cm/s).",
        },
        {
            "label": "Aceleración inicial",
            "offset": 0x03BE09E0,   # VA: _DAT_03be09e0 [EJEMPLO]
            "type": "float",
            "min": 0.0,
            "max": 16000.0,
            "step": 0.5,
            "description": "Tasa de aceleración inicial del jugador.",
        },
        {
            "label": "Umbral velocidad sprint",
            "offset": 0x03BE09E4,   # [EJEMPLO]
            "type": "float",
            "min": 0.0,
            "max": 32000.0,
            "step": 0.5,
            "description": "Velocidad a partir de la cual el jugador entra en modo sprint.",
        },
        {
            "label": "Fricción jugador (suelo)",
            "offset": 0x03BE09E8,   # [EJEMPLO]
            "type": "float",
            "min": 0.0,
            "max": 1.0,
            "step": 0.01,
            "description": "Coeficiente de fricción del jugador sobre el suelo.",
        },
        {
            "label": "Altura de salto",
            "offset": 0x03BE0A10,   # [EJEMPLO]
            "type": "float",
            "min": 0.0,
            "max": 500.0,
            "step": 0.5,
            "description": "Altura máxima alcanzada en el salto.",
        },
        {
            "label": "Gravedad jugador",
            "offset": 0x03BE0A14,   # [EJEMPLO]
            "type": "float",
            "min": -5000.0,
            "max": 0.0,
            "step": 0.5,
            "description": "Fuerza gravitatoria aplicada al jugador (valor negativo = hacia abajo).",
        },
        {
            "label": "Equilibrio corporal (balance)",
            "offset": 0x03BE0A18,   # [EJEMPLO]
            "type": "float",
            "min": 0.0,
            "max": 100.0,
            "step": 0.1,
            "description": "Resistencia base al derribo por contacto.",
        },
        {
            "label": "Radio de colisión jugador",
            "offset": 0x03BE0A1C,   # [EJEMPLO]
            "type": "float",
            "min": 0.0,
            "max": 200.0,
            "step": 0.5,
            "description": "Radio de la cápsula de colisión del jugador.",
        },
    ],

    # -----------------------------------------------------------------------
    # Física del balón
    # -----------------------------------------------------------------------
    "Física del Balón": [
        {
            "label": "Posición X del balón (runtime)",
            "offset": 0x03BE09EC,   # VA: _DAT_03be09ec [EJEMPLO]
            "type": "float",
            "min": -20000.0,
            "max": 20000.0,
            "step": 1.0,
            "description": "Coordenada X actual del balón en el campo.",
        },
        {
            "label": "Posición Y del balón (runtime)",
            "offset": 0x03BE09F0,   # VA: _DAT_03be09f0 [EJEMPLO]
            "type": "float",
            "min": -20000.0,
            "max": 20000.0,
            "step": 1.0,
            "description": "Coordenada Y actual del balón en el campo.",
        },
        {
            "label": "Posición Z del balón (runtime)",
            "offset": 0x03BE09F4,   # VA: _DAT_03be09f4 [EJEMPLO]
            "type": "float",
            "min": 0.0,
            "max": 5000.0,
            "step": 1.0,
            "description": "Coordenada Z (altura) del balón.",
        },
        {
            "label": "Gravedad del balón",
            "offset": 0x03BE0A30,   # [EJEMPLO]
            "type": "float",
            "min": -5000.0,
            "max": 0.0,
            "step": 0.5,
            "description": "Aceleración gravitatoria aplicada al balón.",
        },
        {
            "label": "Coeficiente de rebote",
            "offset": 0x03BE0A34,   # [EJEMPLO]
            "type": "float",
            "min": 0.0,
            "max": 1.0,
            "step": 0.01,
            "description": "Energía conservada en cada rebote (0 = sin rebote, 1 = rebote perfecto).",
        },
        {
            "label": "Resistencia del aire (drag)",
            "offset": 0x03BE0A38,   # [EJEMPLO]
            "type": "float",
            "min": 0.0,
            "max": 1.0,
            "step": 0.001,
            "description": "Coeficiente de resistencia aerodinámica del balón.",
        },
        {
            "label": "Fricción balón (suelo)",
            "offset": 0x03BE0A3C,   # [EJEMPLO]
            "type": "float",
            "min": 0.0,
            "max": 1.0,
            "step": 0.01,
            "description": "Fricción del balón con la superficie del campo.",
        },
        {
            "label": "Radio del balón",
            "offset": 0x03BE0A40,   # [EJEMPLO]
            "type": "float",
            "min": 1.0,
            "max": 200.0,
            "step": 0.5,
            "description": "Radio físico del balón (en unidades internas).",
        },
        {
            "label": "Masa del balón",
            "offset": 0x03BE0A44,   # [EJEMPLO]
            "type": "float",
            "min": 0.01,
            "max": 10.0,
            "step": 0.01,
            "description": "Masa del balón utilizada en cálculos de impulso.",
        },
    ],

    # -----------------------------------------------------------------------
    # Sistema de disparo
    # -----------------------------------------------------------------------
    "Sistema de Disparo": [
        {
            "label": "Multiplicador de potencia de disparo",
            "offset": 0x03BE0A60,   # [EJEMPLO]
            "type": "float",
            "min": 0.1,
            "max": 10.0,
            "step": 0.05,
            "description": "Factor que escala la potencia máxima de un disparo.",
        },
        {
            "label": "Efecto de curva",
            "offset": 0x03BE0A64,   # [EJEMPLO]
            "type": "float",
            "min": 0.0,
            "max": 5.0,
            "step": 0.05,
            "description": "Magnitud del efecto de rotación (curva) aplicado al disparo.",
        },
        {
            "label": "Precisión base de disparo",
            "offset": 0x03BE0A68,   # [EJEMPLO]
            "type": "float",
            "min": 0.0,
            "max": 100.0,
            "step": 0.5,
            "description": "Precisión de referencia antes de aplicar atributos del jugador.",
        },
        {
            "label": "Potencia de cabezazo",
            "offset": 0x03BE0A6C,   # [EJEMPLO]
            "type": "float",
            "min": 0.0,
            "max": 5.0,
            "step": 0.05,
            "description": "Multiplicador de potencia aplicado en cabezazos.",
        },
        {
            "label": "Distancia máxima de disparo",
            "offset": 0x03BE0A70,   # [EJEMPLO]
            "type": "float",
            "min": 0.0,
            "max": 50000.0,
            "step": 10.0,
            "description": "Distancia máxima que puede recorrer el balón tras un disparo.",
        },
        {
            "label": "Tiempo de carga de disparo",
            "offset": 0x03BE0A74,   # [EJEMPLO]
            "type": "int32",
            "min": 1,
            "max": 120,
            "step": 1,
            "description": "Fotogramas necesarios para cargar el disparo al máximo.",
        },
        {
            "label": "Umbral disparo potente (frames)",
            "offset": 0x03BE0A78,   # [EJEMPLO]
            "type": "int32",
            "min": 1,
            "max": 60,
            "step": 1,
            "description": "Fotogramas mínimos para activar el modo de disparo potente.",
        },
    ],

    # -----------------------------------------------------------------------
    # Aleatoriedad (RNG)
    # -----------------------------------------------------------------------
    "Aleatoriedad (RNG)": [
        {
            "label": "Semilla RNG inicial",
            "offset": 0x03BE1484,   # VA: _DAT_03be1484 [EJEMPLO]
            "type": "uint32",
            "min": 0,
            "max": 0xFFFFFFFF,
            "step": 1,
            "description": "Semilla utilizada por el generador de números pseudo-aleatorios.",
        },
        {
            "label": "Variación aleatoria de disparo",
            "offset": 0x03BE0A90,   # [EJEMPLO]
            "type": "float",
            "min": 0.0,
            "max": 50.0,
            "step": 0.1,
            "description": "Rango de error aleatorio en la dirección del disparo.",
        },
        {
            "label": "Variación aleatoria de pase",
            "offset": 0x03BE0A94,   # [EJEMPLO]
            "type": "float",
            "min": 0.0,
            "max": 50.0,
            "step": 0.1,
            "description": "Rango de error aleatorio en la precisión del pase.",
        },
        {
            "label": "Variación aleatoria de control",
            "offset": 0x03BE0A98,   # [EJEMPLO]
            "type": "float",
            "min": 0.0,
            "max": 50.0,
            "step": 0.1,
            "description": "Margen de error en el control/recepción del balón.",
        },
        {
            "label": "Factor de imprevisibilidad IA",
            "offset": 0x03BE0A9C,   # VA: _DAT_03be0a9c [EJEMPLO]
            "type": "float",
            "min": 0.0,
            "max": 10.0,
            "step": 0.05,
            "description": "Nivel de impredecibilidad en las acciones de la IA.",
        },
        {
            "label": "Modo determinista",
            "offset": 0x03BE09FC,   # VA: _DAT_03be09fc [EJEMPLO]
            "type": "bool",
            "min": 0,
            "max": 1,
            "step": 1,
            "description": "Si está activado, desactiva la aleatoriedad (simulación determinista).",
        },
    ],

    # -----------------------------------------------------------------------
    # Stats de jugadores (estructura base)
    # -----------------------------------------------------------------------
    "Stats de Jugadores": [
        {
            "label": "Velocidad (stat)",
            "offset": 0x03BCF5AC,   # VA: DAT_03bcf5ac [EJEMPLO]
            "type": "uint8",
            "min": 1,
            "max": 99,
            "step": 1,
            "description": "Atributo de velocidad del jugador (1-99).",
        },
        {
            "label": "Resistencia física",
            "offset": 0x03BCF5AD,   # [EJEMPLO]
            "type": "uint8",
            "min": 1,
            "max": 99,
            "step": 1,
            "description": "Atributo de resistencia / stamina del jugador (1-99).",
        },
        {
            "label": "Potencia de disparo (stat)",
            "offset": 0x03BCF5AE,   # [EJEMPLO]
            "type": "uint8",
            "min": 1,
            "max": 99,
            "step": 1,
            "description": "Atributo de potencia de disparo del jugador (1-99).",
        },
        {
            "label": "Precisión de disparo (stat)",
            "offset": 0x03BCF5AF,   # [EJEMPLO]
            "type": "uint8",
            "min": 1,
            "max": 99,
            "step": 1,
            "description": "Atributo de precisión de disparo del jugador (1-99).",
        },
        {
            "label": "Habilidad de pase (stat)",
            "offset": 0x03BCF5B0,   # [EJEMPLO]
            "type": "uint8",
            "min": 1,
            "max": 99,
            "step": 1,
            "description": "Atributo de precisión de pase del jugador (1-99).",
        },
        {
            "label": "Control de balón (stat)",
            "offset": 0x03BCF5B1,   # [EJEMPLO]
            "type": "uint8",
            "min": 1,
            "max": 99,
            "step": 1,
            "description": "Atributo de control / técnica del jugador (1-99).",
        },
        {
            "label": "Altura del jugador (cm)",
            "offset": 0x03BCF5C2,   # VA: DAT_03bcf5c2 [EJEMPLO]
            "type": "uint8",
            "min": 140,
            "max": 210,
            "step": 1,
            "description": "Altura del jugador en centímetros.",
        },
        {
            "label": "Número de camiseta",
            "offset": 0x03BCF5CC,   # VA: DAT_03bcf5cc [EJEMPLO]
            "type": "uint8",
            "min": 1,
            "max": 99,
            "step": 1,
            "description": "Número de camiseta asignado al jugador.",
        },
    ],
}

# ---------------------------------------------------------------------------
# Constantes globales del juego
# ---------------------------------------------------------------------------
GLOBAL_CONSTANTS = {
    "Versión del juego (flag)": {
        "offset": 0x03BE12C9,   # VA: DAT_03be12c9 [EJEMPLO]
        "type": "uint8",
        "min": 0,
        "max": 10,
        "step": 1,
        "description": "Flag de versión del ejecutable.",
    },
    "Modo de cámara": {
        "offset": 0x03BE12CC,   # VA: _DAT_03be12cc [EJEMPLO]
        "type": "int32",
        "min": 0,
        "max": 10,
        "step": 1,
        "description": "Código del modo de cámara activo.",
    },
}

# ---------------------------------------------------------------------------
# Mapeo de tipos de datos a formato struct de Python
# ---------------------------------------------------------------------------
TYPE_FORMAT = {
    "float":  ("<f", 4),
    "int8":   ("<b", 1),
    "int16":  ("<h", 2),
    "int32":  ("<i", 4),
    "uint8":  ("<B", 1),
    "uint16": ("<H", 2),
    "uint32": ("<I", 4),
    "bool":   ("<B", 1),
}

# ---------------------------------------------------------------------------
# Advertencia de offsets de ejemplo
# ---------------------------------------------------------------------------
# Todos los offsets en este archivo están marcados con [EJEMPLO] e indican
# direcciones virtuales del análisis técnico. Deben convertirse a file offsets
# reales del ejecutable específico antes de usarse en producción.
USING_EXAMPLE_OFFSETS = True  # Establecer en False cuando los offsets estén verificados.


def warn_if_example_offsets() -> str:
    """
    Devuelve un mensaje de advertencia si se están usando offsets de ejemplo.

    Returns:
        Cadena con la advertencia, o cadena vacía si USING_EXAMPLE_OFFSETS es False.
    """
    if USING_EXAMPLE_OFFSETS:
        return (
            "ADVERTENCIA: Los offsets configurados en offsets.py son valores de ejemplo.\n"
            "Deben verificarse y actualizarse con los offsets reales del ejecutable\n"
            "analizado antes de aplicar cualquier parche.\n\n"
            "Aplicar cambios con offsets incorrectos puede corromper el ejecutable."
        )
    return ""
