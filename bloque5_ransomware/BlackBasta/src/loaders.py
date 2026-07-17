"""
Loader para los chats filtrados de Black Basta (Matrix, 2023-2024).

Formato de origen: pseudo-JSON con claves sin comillas y valores sin comillas,
objetos concatenados (no array). Ejemplo:

    {
        timestamp: 2023-09-18 13:35:07,
        chat_id: !VdvDXHFZwWDpIAtpCj:matrix.bestflowers247.online,
        sender_alias: @usernamenn:matrix.bestflowers247.online,
        message: texto del mensaje
    }

Schema de salida unificado:
    timestamp  : datetime64[ns, UTC]
    username   : str   — parte local del sender_alias (antes de ':matrix.')
    channel    : str   — parte local del chat_id (sin '!' ni dominio)
    message    : str   — texto del mensaje (puede ser multilínea)
    source     : str   — siempre "blackbasta"
"""

# 're' es el módulo de expresiones regulares de Python.
# Las expresiones regulares son "patrones de búsqueda" que permiten encontrar
# fragmentos de texto con una forma concreta dentro de un texto más grande.
import re

# Path es una herramienta de Python para manejar rutas de archivos de forma
# más cómoda que usando cadenas de texto normales (evita errores con / y \).
# Por ejemplo: Path('data') / 'archivo.json' produce 'data/archivo.json'.
from pathlib import Path

# pandas es la librería más usada para trabajar con tablas de datos en Python.
# Un "DataFrame" de pandas es como una hoja de Excel que podemos manipular con código.
import pandas as pd

# Patrón regex para detectar cada bloque { ... } del fichero.
# r'\{([^{}]*?)\}' significa: busca '{', captura todo lo que haya dentro
# que no sea otro '{' ni '}', y termina en '}'. El flag re.DOTALL hace que
# el punto '.' también capture saltos de línea (necesario para mensajes multilínea).
_RE_BLOCK = re.compile(r'\{([^{}]*?)\}', re.DOTALL)

# Patrón para extraer la fecha y hora del mensaje (el campo 'timestamp').
# \s* significa "cero o más espacios". .+? captura el valor de forma no voraz
# (se detiene en la primera coma seguida de salto de línea que encuentre).
_RE_TS    = re.compile(r'timestamp:\s*(.+?),\s*\n')

# Patrón para extraer el identificador del canal de chat (campo 'chat_id').
_RE_CHAT  = re.compile(r'chat_id:\s*(.+?),\s*\n')

# Patrón para extraer el nombre del usuario que envió el mensaje (campo 'sender_alias').
_RE_ALIAS = re.compile(r'sender_alias:\s*(.+?),\s*\n')

# Patrón para extraer el texto del mensaje (campo 'message').
# re.DOTALL es necesario porque los mensajes pueden ocupar varias líneas.
_RE_MSG   = re.compile(r'message:\s*(.*)', re.DOTALL)


# Función auxiliar (privada, por eso empieza con _) que extrae la parte
# "útil" de un identificador de Matrix, que tiene el formato:
#   @nombreusuario:matrix.servidor.com  →  nombreusuario
#   !IDcanal:matrix.servidor.com        →  IDcanal
def _local_part(matrix_id: str) -> str:
    """
    Extrae la parte local de un identificador de Matrix.

    Parámetros:
        matrix_id (str): Identificador completo de Matrix, por ejemplo
                         '@usernamenn:matrix.bestflowers247.online' o
                         '!VdvDXHFZwWDpIAtpCj:matrix.bestflowers247.online'.

    Devuelve:
        str: La parte antes del ':', sin los prefijos '!' ni '@'.
             Ejemplo: 'usernamenn' o 'VdvDXHFZwWDpIAtpCj'.
    """
    # lstrip('!@') elimina los caracteres '!' y '@' del inicio de la cadena.
    # split(':')[0] divide el texto por ':' y se queda solo con la primera parte.
    local = matrix_id.lstrip('!@').split(':')[0]
    return local


# Función principal del módulo: lee el archivo de chats y devuelve una tabla limpia.
def load_blackbasta(raw_dir: Path) -> pd.DataFrame:
    """
    Carga el fichero blackbasta_chats.json y lo convierte en un DataFrame de pandas.

    El fichero usa un formato pseudo-JSON (las claves no tienen comillas) con
    múltiples objetos concatenados. Esta función los parsea uno a uno con regex.

    Parámetros:
        raw_dir (Path | str): Puede ser:
            - La ruta directa al fichero blackbasta_chats.json, o
            - La ruta a un directorio que contenga ese fichero (se busca recursivamente).

    Devuelve:
        pd.DataFrame: Tabla con las columnas:
            - timestamp (datetime con zona horaria UTC)
            - username  (nombre del usuario, sin prefijos ni dominio)
            - channel   (identificador del canal, sin prefijos ni dominio)
            - message   (texto del mensaje)
            - source    (siempre 'blackbasta', para identificar el origen)

    Lanza:
        FileNotFoundError: Si no se encuentra el fichero en el directorio indicado.
    """
    # Convertimos raw_dir a objeto Path por si se pasó como cadena de texto.
    raw_dir = Path(raw_dir)

    # Si la ruta apunta directamente a un fichero, lo usamos tal cual.
    # Si apunta a un directorio, buscamos el fichero dentro de él (y subcarpetas).
    if raw_dir.is_file():
        fpath = raw_dir
    else:
        # rglob busca recursivamente en todas las subcarpetas el fichero indicado.
        candidates = list(raw_dir.rglob('blackbasta_chats.json'))
        if not candidates:
            raise FileNotFoundError(f'No se encontró blackbasta_chats.json en {raw_dir}')
        # Si hay varios ficheros con ese nombre, tomamos el primero encontrado.
        fpath = candidates[0]

    # Leemos todo el contenido del fichero como una cadena de texto.
    # errors='replace' hace que los caracteres raros (no UTF-8) no causen error,
    # sino que se reemplacen por un símbolo de sustitución (el típico '?').
    content = fpath.read_text(encoding='utf-8', errors='replace')

    # Lista vacía donde iremos guardando los mensajes extraídos como diccionarios.
    records = []

    # Iteramos sobre cada bloque { ... } que encuentre el patrón _RE_BLOCK.
    # Cada bloque corresponde a un mensaje del chat.
    for m in _RE_BLOCK.finditer(content):
        # m.group(1) devuelve el contenido capturado dentro de los paréntesis
        # del patrón, es decir, el texto entre '{' y '}' (sin las llaves).
        block = m.group(1)

        # Aplicamos cada sub-patrón al bloque para extraer los campos del mensaje.
        ts_m    = _RE_TS.search(block)    # fecha y hora
        chat_m  = _RE_CHAT.search(block)  # identificador del canal
        alias_m = _RE_ALIAS.search(block) # nombre del usuario
        msg_m   = _RE_MSG.search(block)   # texto del mensaje

        # Si alguno de los cuatro campos no se encontró, este bloque está
        # incompleto o es inválido → lo ignoramos y pasamos al siguiente.
        if not (ts_m and chat_m and alias_m and msg_m):
            continue

        # Construimos un diccionario con los datos limpios del mensaje.
        # .group(1) obtiene lo que capturó el patrón; .strip() elimina espacios
        # y saltos de línea sobrantes al principio y al final.
        records.append({
            'timestamp': ts_m.group(1).strip(),
            'username':  _local_part(alias_m.group(1).strip()),
            'channel':   _local_part(chat_m.group(1).strip()),
            'message':   msg_m.group(1).strip(),
            # Etiquetamos la fuente siempre como 'blackbasta' para poder
            # combinar más adelante con otros datasets (p.ej. Conti).
            'source':    'blackbasta',
        })

    # Convertimos la lista de diccionarios en un DataFrame de pandas.
    # Cada diccionario se convierte en una fila; las claves son los nombres de columna.
    df = pd.DataFrame(records)

    # Convertimos la columna 'timestamp' de texto a tipo fecha-hora real de Python.
    # utc=True fuerza que todos los timestamps se interpreten en la zona horaria UTC.
    # errors='coerce' hace que los timestamps mal formados se conviertan en NaT
    # (equivalente a "fecha desconocida") en lugar de causar un error.
    df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True, errors='coerce')
    return df
