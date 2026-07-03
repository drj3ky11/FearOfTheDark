"""
Loaders para los tres formatos de los chats filtrados de Conti.

Todos devuelven un DataFrame con el schema unificado:
    timestamp  : datetime64[ns, UTC]
    username   : str   — alias del actor (sin dominio)
    to_user    : str   — destinatario (Jabber) o sala (Rocket.Chat)
    message    : str   — texto del mensaje
    source     : str   — "jabber_2020" | "jabber_2021" | "rocketchat"
    channel    : str   — identificador de conversación derivado del nombre de archivo
"""

# Importamos json, que es la librería estándar de Python para leer y escribir
# archivos en formato JSON. JSON es el formato más común para guardar datos
# estructurados en texto (como un diccionario de Python, pero en un archivo).
import json

# Path es una clase que nos permite trabajar con rutas de archivos y carpetas
# de forma más cómoda y segura que usando cadenas de texto. Por ejemplo, en vez
# de escribir "carpeta" + "/" + "archivo.json", hacemos Path("carpeta") / "archivo.json".
# Además funciona igual en Windows, Mac y Linux (sin preocuparnos por / o \).
from pathlib import Path

# Importamos pandas, la librería más usada para trabajar con tablas de datos en Python.
# Un DataFrame de pandas es como una hoja de Excel que podemos manipular con código:
# tiene filas, columnas con nombre, y podemos filtrar, ordenar, agrupar, etc.
import pandas as pd


# ---------------------------------------------------------------------------
# Jabber (Chat Logs 2020 y Jabber Chat Logs 2021-2022)
# ---------------------------------------------------------------------------

def _iter_jabber_objects(text: str):
    """
    Lee un texto que contiene varios objetos JSON pegados uno tras otro
    (sin comas ni corchetes entre ellos) y los devuelve de uno en uno.

    El formato normal de JSON sería una lista: [{...}, {...}, {...}]
    Pero los archivos Jabber de Conti tienen los objetos simplemente
    concatenados: {...}{...}{...} — este generador los separa correctamente.

    Parámetros:
        text (str): El contenido completo del archivo como texto.

    Devuelve:
        Un generador que produce diccionarios Python, uno por cada
        objeto JSON encontrado en el texto.
    """
    # Creamos un "decodificador" de JSON que nos permite leer el texto
    # desde una posición específica, en vez de leerlo todo de una vez.
    decoder = json.JSONDecoder()

    # Empezamos desde el inicio del texto (posición 0).
    pos = 0

    # Eliminamos espacios en blanco al principio y al final del texto.
    text = text.strip()

    # Recorremos el texto de izquierda a derecha hasta llegar al final.
    while pos < len(text):
        # Saltamos cualquier espacio en blanco (espacios, tabulaciones,
        # saltos de línea) que haya entre un objeto JSON y el siguiente.
        while pos < len(text) and text[pos] in " \t\n\r":
            pos += 1

        # Si después de saltar espacios ya llegamos al final, terminamos.
        if pos >= len(text):
            break

        # raw_decode lee UN objeto JSON desde la posición `pos` y devuelve:
        #   obj  → el objeto Python (un diccionario)
        #   end  → la posición donde terminó ese objeto en el texto
        obj, end = decoder.raw_decode(text, pos)

        # Avanzamos nuestra posición hasta donde terminó el objeto que acabamos de leer.
        pos = end

        # "yield" es como un return, pero en vez de terminar la función,
        # pausa y devuelve el valor. La próxima vez que se llame, continúa
        # desde donde se quedó. Esto se llama "generador".
        yield obj


def _username(jid: str) -> str:
    """
    Extrae solo el nombre de usuario de una dirección Jabber (JID).

    En Jabber, los usuarios se identifican con un formato similar al correo:
    "nombre@servidor.com". Esta función devuelve solo la parte del nombre,
    descartando el dominio (@servidor.com).

    Parámetros:
        jid (str): La dirección completa de Jabber, por ejemplo "mango@jabber.org"

    Devuelve:
        str: Solo el nombre, por ejemplo "mango". Si no tiene "@", devuelve
             el texto tal cual.
    """
    # Si el texto contiene "@", lo partimos por ahí y nos quedamos con la parte
    # izquierda (índice 0). Si no tiene "@", devolvemos el texto sin cambios.
    return jid.split("@")[0] if "@" in jid else jid


def load_jabber(directory: Path, source_label: str) -> pd.DataFrame:
    """
    Carga todos los archivos JSON de un directorio Jabber y los convierte
    en una tabla unificada.

    Los archivos Jabber de Conti contienen objetos JSON concatenados (no
    una lista estándar), por eso usamos la función _iter_jabber_objects
    para leerlos correctamente.

    Parámetros:
        directory (Path): La carpeta que contiene los archivos .json de Jabber.
        source_label (str): Una etiqueta que identifica de qué fuente vienen
                            los datos, por ejemplo "jabber_2020" o "jabber_2021".

    Devuelve:
        pd.DataFrame: Una tabla con las columnas: timestamp, username, to_user,
                      message, source, channel.
    """
    # Creamos una lista vacía donde iremos guardando cada mensaje como diccionario.
    records = []

    # rglob("*.json") busca TODOS los archivos .json dentro de `directory`
    # y sus subcarpetas. sorted() los ordena alfabéticamente para consistencia.
    for fpath in sorted(directory.rglob("*.json")):
        # El nombre del archivo (sin extensión) lo usamos como identificador
        # de canal o conversación. Por ejemplo: "185.25.51.173-20200622"
        channel = fpath.stem          # ej. "185.25.51.173-20200622"

        # Leemos todo el contenido del archivo como texto.
        # errors="replace" hace que si hay caracteres raros que no se puedan
        # leer en UTF-8, se reemplacen con un símbolo especial en vez de fallar.
        text = fpath.read_text(encoding="utf-8", errors="replace")

        # Usamos nuestro generador para procesar cada objeto JSON del archivo.
        for obj in _iter_jabber_objects(text):
            # obj es un diccionario Python. Usamos .get() para leer cada campo
            # de forma segura: si el campo no existe, devuelve el valor por defecto
            # (cadena vacía "" o None).
            records.append({
                "timestamp": obj.get("ts"),           # fecha y hora del mensaje
                "username":  _username(obj.get("from", "")),  # quién envió el mensaje
                "to_user":   _username(obj.get("to", "")),    # quién lo recibió
                "message":   obj.get("body", ""),     # el texto del mensaje
                "source":    source_label,            # de qué fuente vienen estos datos
                "channel":   channel,                 # identificador de la conversación
            })

    # Convertimos la lista de diccionarios en un DataFrame de pandas.
    # Cada diccionario se convierte en una fila de la tabla.
    df = pd.DataFrame(records)

    # Convertimos la columna "timestamp" a un formato de fecha real que pandas
    # entiende. utc=True indica que las horas están en zona horaria UTC.
    # errors="coerce" hace que si algún valor no se puede convertir (por ejemplo
    # si está vacío o mal formateado), se convierta en NaT (Not a Time, el
    # equivalente de "dato faltante" para fechas).
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    return df


def load_jabber_2020(raw_dir: Path) -> pd.DataFrame:
    """
    Carga los chats de Jabber del año 2020.

    Construye la ruta correcta dentro de raw_dir y llama a load_jabber
    con la etiqueta "jabber_2020" para identificar la fuente.

    Parámetros:
        raw_dir (Path): La carpeta raíz donde están todos los datos sin procesar.

    Devuelve:
        pd.DataFrame: Tabla con los mensajes de Jabber 2020.
    """
    # Construimos la ruta a la subcarpeta específica de los logs de 2020.
    # El operador "/" de Path une carpetas (equivale a os.path.join).
    directory = raw_dir / "Conti Chat Logs 2020" / "Conti Chat Logs 2020"
    return load_jabber(directory, source_label="jabber_2020")


def load_jabber_2021(raw_dir: Path) -> pd.DataFrame:
    """
    Carga los chats de Jabber del año 2021-2022.

    Construye la ruta correcta dentro de raw_dir y llama a load_jabber
    con la etiqueta "jabber_2021" para identificar la fuente.

    Parámetros:
        raw_dir (Path): La carpeta raíz donde están todos los datos sin procesar.

    Devuelve:
        pd.DataFrame: Tabla con los mensajes de Jabber 2021-2022.
    """
    # Construimos la ruta a la subcarpeta de los logs de 2021-2022.
    directory = raw_dir / "Conti Jabber Chat Logs 2021 - 2022" / "Conti Jabber Chat Logs 2021 - 2022"
    return load_jabber(directory, source_label="jabber_2021")


# ---------------------------------------------------------------------------
# Rocket.Chat
# ---------------------------------------------------------------------------

def load_rocketchat(raw_dir: Path) -> pd.DataFrame:
    """
    Carga todos los archivos JSON de los chats de Rocket.Chat de Conti.

    Rocket.Chat es una aplicación de mensajería grupal (parecida a Slack).
    Los archivos exportados tienen el formato: {"messages": [{...}, {...}, ...]}
    Es decir, un diccionario con una clave "messages" que contiene una lista
    de mensajes.

    Esta función filtra los mensajes de sistema (como "usuario se unió al canal")
    porque no contienen texto relevante para el análisis.

    El nombre de cada archivo sigue el patrón: YYYY-MM-DD-{nombre_canal}.json
    por ejemplo: "2022-02-17-general.json"

    Parámetros:
        raw_dir (Path): La carpeta raíz donde están todos los datos sin procesar.

    Devuelve:
        pd.DataFrame: Tabla con los mensajes de Rocket.Chat, con las mismas
                      columnas que los loaders de Jabber.
    """
    # Construimos la ruta a la carpeta de Rocket.Chat.
    root = raw_dir / "Conti Rocket Chat Leaks" / "Conti Rocket Chat Leaks"

    # Lista vacía donde iremos acumulando los mensajes.
    records = []

    # Recorremos todos los archivos .json dentro de la carpeta y subcarpetas.
    for fpath in sorted(root.rglob("*.json")):
        # Extraer nombre de canal del archivo: "2022-02-17-general" → "general"
        # split("-", maxsplit=3) parte el nombre en máximo 4 trozos usando "-" como separador.
        # Por ejemplo: "2022-02-17-general" → ["2022", "02", "17", "general"]
        # Nos quedamos con el último trozo (índice 3), que es el nombre del canal.
        parts = fpath.stem.split("-", maxsplit=3)
        channel = parts[3] if len(parts) == 4 else fpath.stem

        # Intentamos leer y parsear el archivo JSON.
        # Si el archivo tiene un error de formato JSON (JSONDecodeError),
        # lo saltamos con "continue" y pasamos al siguiente archivo.
        try:
            data = json.loads(fpath.read_text(encoding="utf-8", errors="replace"))
        except json.JSONDecodeError:
            continue

        # data.get("messages", []) nos da la lista de mensajes del archivo.
        # Si por algún motivo no tiene la clave "messages", usamos una lista vacía.
        for msg in data.get("messages", []):
            # Los mensajes de sistema tienen un campo "t" (type) con valores
            # como "uj" (user joined), "ul" (user left), etc.
            # Nos los saltamos porque no son mensajes de texto reales.
            if msg.get("t"):          # system event (uj = user joined, etc.)
                continue

            # El campo "u" contiene información del usuario que envió el mensaje.
            # Usamos "or {}" para que si "u" es None, tengamos un diccionario vacío
            # y evitemos un error al intentar hacer .get() sobre None.
            user_obj = msg.get("u") or {}

            records.append({
                "timestamp": msg.get("ts"),               # fecha y hora del mensaje
                "username":  user_obj.get("username", ""), # nombre del usuario
                "to_user":   msg.get("rid", ""),           # id de la sala o canal
                "message":   msg.get("msg", ""),           # texto del mensaje
                "source":    "rocketchat",                 # etiqueta de la fuente
                "channel":   channel,                     # nombre del canal derivado del archivo
            })

    # Convertimos la lista de diccionarios en un DataFrame de pandas.
    df = pd.DataFrame(records)

    # Convertimos los timestamps a formato de fecha real en zona horaria UTC.
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    return df


# ---------------------------------------------------------------------------
# Loader unificado
# ---------------------------------------------------------------------------

def load_all(raw_dir: Path) -> pd.DataFrame:
    """
    Carga las tres fuentes de datos (Jabber 2020, Jabber 2021, Rocket.Chat)
    y las une en una sola tabla ordenada cronológicamente.

    Este es el loader principal que usarán los notebooks: en vez de llamar
    a cada loader por separado, llaman solo a esta función y obtienen todos
    los mensajes en un único DataFrame.

    Parámetros:
        raw_dir (Path): La carpeta raíz donde están todos los datos sin procesar.
                        Puede ser un objeto Path o una cadena de texto (str);
                        la función lo convierte a Path automáticamente.

    Devuelve:
        pd.DataFrame: Una tabla con TODOS los mensajes de las tres fuentes,
                      ordenada de más antiguo a más reciente.
    """
    # Nos aseguramos de que raw_dir sea un objeto Path aunque nos pasen un string.
    raw_dir = Path(raw_dir)

    # Llamamos a cada loader y guardamos los tres DataFrames en una lista.
    frames = [
        load_jabber_2020(raw_dir),
        load_jabber_2021(raw_dir),
        load_rocketchat(raw_dir),
    ]

    # pd.concat une varios DataFrames apilándolos verticalmente (uno encima del otro),
    # como si pegaras tres hojas de Excel una debajo de la otra.
    # ignore_index=True hace que se re-numeren las filas desde 0 (en vez de mantener
    # los índices originales de cada DataFrame por separado).
    df = pd.concat(frames, ignore_index=True)

    # Ordenamos todos los mensajes por fecha, del más antiguo al más reciente.
    # reset_index(drop=True) vuelve a numerar las filas después de ordenar.
    df = df.sort_values("timestamp").reset_index(drop=True)
    return df
