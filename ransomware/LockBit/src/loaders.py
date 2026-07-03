"""
Parser for the LockBit panel DB SQL dump (MySQL 8.0 / phpMyAdmin format).
Returns a dict of DataFrames, one per target table, with no MySQL server required.

En términos sencillos: este archivo sabe leer un volcado de base de datos SQL
(un archivo de texto gigante con instrucciones SQL) y convertirlo en tablas de
pandas que podemos analizar en Python, sin necesitar instalar MySQL.
"""

# "re" es el módulo de expresiones regulares. Nos permite buscar patrones de texto,
# por ejemplo, encontrar todas las líneas que empiecen con "CREATE TABLE".
import re

# "zipfile" nos permite abrir archivos .zip directamente desde Python,
# sin necesidad de descomprimirlos antes a mano.
import zipfile

# "pandas" es la librería más importante para análisis de datos en Python.
# La abreviamos como "pd" por convención. Con ella crearemos tablas (DataFrames)
# que funcionan como hojas de cálculo.
import pandas as pd

# "Path" de pathlib es una forma moderna y cómoda de trabajar con rutas de archivos.
# Por ejemplo, Path('datos') / 'archivo.sql' construye la ruta correcta
# sin preocuparnos por usar / o \ según el sistema operativo.
from pathlib import Path

# Este conjunto (set) contiene los nombres de las tablas que nos interesan
# extraer del volcado SQL de LockBit. Solo procesaremos estas tablas y
# descartaremos el resto para ahorrar tiempo y memoria.
# - 'users': los usuarios del panel (afiliados / operadores de LockBit)
# - 'clients': las víctimas del ransomware
# - 'chats': los mensajes de negociación entre operadores y víctimas
# - 'builds': los ejecutables maliciosos compilados
# - 'btc_addresses': las billeteras Bitcoin para cobrar rescates
# - 'invites': códigos de invitación para reclutar afiliados
# - 'pkeys': claves criptográficas de las víctimas
TABLES_OF_INTEREST = {
    'users', 'clients', 'chats', 'builds', 'btc_addresses', 'invites', 'pkeys'
}


def _tokenize_row(row_str: str) -> list:
    """
    Convierte una fila SQL del tipo '(valor1, 'texto', NULL, 0x4142...)' en una lista Python.

    Un volcado SQL guarda cada fila de datos como una cadena de texto con este formato:
        (1, 'nombre', NULL, 0xABCD)
    Esta función la "traduce" a una lista de Python:
        [1, 'nombre', None, 'AB']

    Parámetros:
        row_str (str): Una cadena de texto con una fila en formato SQL, incluyendo paréntesis.

    Devuelve:
        list: Una lista con los valores de la fila, ya convertidos al tipo Python adecuado
              (int, float, str o None según corresponda).
    """
    # Eliminamos los espacios en blanco al principio y al final de la cadena
    s = row_str.strip()

    # El formato SQL empieza siempre con '(' — lo quitamos para procesar el interior
    if s.startswith('('):
        s = s[1:]

    # Cada fila SQL puede terminar con ');' o '),' o simplemente ')'.
    # Probamos cada posibilidad y eliminamos el sufijo que corresponda.
    for suffix in (');', '),', ')'):
        if s.endswith(suffix):
            s = s[:-len(suffix)]
            break

    # Aquí iremos acumulando los valores de la fila ya separados
    values = []
    # "current" almacena los caracteres del valor que estamos leyendo en este momento
    current = []
    # Estas dos variables controlan en qué "modo" está el lector:
    # - in_string=True significa que estamos dentro de un texto entre comillas simples
    # - escaped=True significa que el siguiente carácter es especial (viene tras una \)
    in_string = False
    escaped = False

    # Recorremos la cadena carácter a carácter para separar los valores correctamente.
    # No podemos simplemente separar por comas porque los textos pueden contener comas.
    for ch in s:
        if escaped:
            # Si el carácter anterior era '\', este carácter es literal (ej: \' no termina el string)
            current.append(ch)
            escaped = False
        elif in_string:
            # Estamos dentro de un texto entre comillas simples
            if ch == '\\':
                # La barra invertida indica que el siguiente carácter es especial
                current.append(ch)
                escaped = True
            elif ch == "'":
                # La comilla cierra el texto
                in_string = False
                current.append(ch)
            else:
                # Cualquier otro carácter va directo al valor actual
                current.append(ch)
        else:
            # Estamos fuera de un texto entre comillas
            if ch == "'":
                # Una comilla abre un nuevo texto
                in_string = True
                current.append(ch)
            elif ch == ',':
                # Una coma separa valores: guardamos el que acabamos de leer y empezamos otro
                values.append(''.join(current).strip())
                current = []
            else:
                # Cualquier otro carácter (número, letra, etc.) va al valor actual
                current.append(ch)

    # No olvidamos el último valor (que no tiene coma al final)
    if current:
        values.append(''.join(current).strip())

    # Ahora convertimos cada valor de texto a su tipo Python correcto
    cleaned = []
    for v in values:
        v = v.strip()
        if v.upper() == 'NULL':
            # NULL en SQL equivale a None en Python (ausencia de valor)
            cleaned.append(None)
        elif v.startswith("'") and v.endswith("'"):
            # Es un texto entre comillas: quitamos las comillas y procesamos
            # las secuencias de escape de MySQL (como \n para nueva línea, \t para tabulación)
            inner = v[1:-1]
            inner = (inner
                     .replace("\\'", "'")      # \' → comilla simple literal
                     .replace('\\n', '\n')     # \n → salto de línea real
                     .replace('\\r', '\r')     # \r → retorno de carro
                     .replace('\\\\', '\\')   # \\ → barra invertida literal
                     .replace('\\"', '"')      # \" → comilla doble literal
                     .replace('\\t', '\t')     # \t → tabulación real
                     .replace('\\0', '\x00'))  # \0 → carácter nulo
            cleaned.append(inner)
        elif v.upper().startswith('0X'):
            # Hex BLOB — decode to UTF-8 string (public keys, etc.)
            # Los BLOBs hexadecimales (ej: 0x4D5A) son datos binarios en formato hexadecimal.
            # Los convertimos a texto UTF-8 para poder leerlos (por ejemplo, claves públicas).
            try:
                cleaned.append(bytes.fromhex(v[2:]).decode('utf-8', errors='replace'))
            except Exception:
                # Si la conversión falla, dejamos el valor hexadecimal tal cual
                cleaned.append(v)
        else:
            # Intentamos convertir a número entero primero, luego a decimal, y si no podemos,
            # lo dejamos como texto. Esto maneja números como 42 o precios como 1500.50.
            try:
                cleaned.append(int(v))
            except ValueError:
                try:
                    cleaned.append(float(v))
                except ValueError:
                    # Si no es ni entero ni decimal, lo guardamos como texto (o None si está vacío)
                    cleaned.append(v if v else None)

    return cleaned


def _extract_columns(line_iter) -> dict[str, list[str]]:
    """
    Escanea las líneas del archivo SQL buscando bloques CREATE TABLE y extrae
    los nombres de columnas de las tablas que nos interesan.

    En un volcado SQL, la estructura de cada tabla aparece así:
        CREATE TABLE `clients` (
          `id` int NOT NULL,
          `name` varchar(255),
          ...
        ) ENGINE=InnoDB;

    Esta función lee esas definiciones y devuelve un diccionario con el nombre
    de cada tabla y la lista de sus columnas.

    Parámetros:
        line_iter: Un iterador que devuelve líneas del archivo SQL una a una.
                   Puede ser un archivo abierto u otro objeto iterable.

    Devuelve:
        dict[str, list[str]]: Un diccionario donde la clave es el nombre de la tabla
                              y el valor es la lista de nombres de columna en orden.
                              Ejemplo: {'clients': ['id', 'name', 'email'], ...}
    """
    # Aquí guardaremos los esquemas (estructuras) de las tablas que vayamos encontrando
    schemas: dict[str, list[str]] = {}
    # Nombre de la tabla que estamos procesando en este momento (None si no estamos dentro de ninguna)
    current_table = None
    # Lista de columnas que vamos acumulando para la tabla actual
    cols = []

    for line in line_iter:
        # Quitamos el salto de línea al final para procesar el texto limpio
        line = line.rstrip('\n')
        stripped = line.strip()

        # Buscamos una línea que empiece por "CREATE TABLE `nombre_tabla`"
        # re.match() busca el patrón solo al principio de la cadena
        # El patrón r"CREATE TABLE `(\w+)`" captura el nombre de la tabla entre comillas invertidas
        m = re.match(r"CREATE TABLE `(\w+)`", stripped)
        if m:
            # Encontramos una nueva tabla: guardamos su nombre y reiniciamos la lista de columnas
            current_table = m.group(1)  # group(1) extrae lo que capturó (\w+)
            cols = []
            continue  # Pasamos a la siguiente línea

        if current_table:
            # Estamos dentro de un bloque CREATE TABLE, buscando las definiciones de columnas
            # Las columnas aparecen como: `nombre_columna` tipo_dato opciones...
            col_m = re.match(r'`(\w+)`', stripped)
            if col_m:
                # Encontramos una columna: guardamos su nombre
                cols.append(col_m.group(1))
            elif stripped.startswith(') ENGINE='):
                # Llegamos al final de la definición de la tabla
                # Guardamos las columnas encontradas y reiniciamos el estado
                schemas[current_table] = cols
                current_table = None
                cols = []

    return schemas


def _parse_sql(path: Path) -> dict[str, pd.DataFrame]:
    """
    Lee el volcado SQL completo (archivo .sql o .zip con un .sql dentro)
    y devuelve un diccionario de DataFrames, uno por tabla.

    Esta es la función principal de análisis del archivo. Realiza dos pasadas:
    1. Primera pasada: extrae la estructura (nombres de columnas) de cada tabla
    2. Segunda pasada: extrae los datos (filas) de cada tabla

    Parámetros:
        path (Path): Ruta al archivo .sql o al archivo .zip que contiene el .sql.

    Devuelve:
        dict[str, pd.DataFrame]: Un diccionario donde la clave es el nombre de la
                                 tabla y el valor es un DataFrame de pandas con sus datos.
    """

    # Esta función interna decide cómo abrir el archivo según su extensión.
    # Si es .zip, abre el ZIP y busca el primer archivo .sql dentro.
    # Si no es .zip, lo abre directamente como archivo binario ('rb').
    def open_sql():
        if path.suffix == '.zip':
            zf = zipfile.ZipFile(path)
            # Buscamos el primer archivo dentro del ZIP que termine en .sql
            # next() devuelve el primer elemento de un iterador
            name = next(n for n in zf.namelist() if n.endswith('.sql'))
            return zf.open(name)
        return open(path, 'rb')

    # --- Pasada 1: extraer esquemas (estructura de columnas) ---
    # Abrimos el archivo y lo leemos línea a línea para encontrar los CREATE TABLE
    with open_sql() as fh:
        schemas = _extract_columns(
            # Convertimos cada línea de bytes a texto UTF-8
            # errors='replace' significa que si hay un carácter inválido, lo sustituimos por ?
            line.decode('utf-8', errors='replace') for line in fh
        )

    # --- Pasada 2: extraer filas de datos ---
    # Creamos un diccionario donde cada tabla de interés empieza con una lista vacía
    raw_rows: dict[str, list] = {t: [] for t in TABLES_OF_INTEREST}
    # Tabla actual que estamos procesando (None si no estamos dentro de un INSERT)
    current_table: str | None = None
    # Bandera que indica si estamos dentro de un bloque INSERT INTO
    in_insert = False

    with open_sql() as fh:
        for raw_line in fh:
            # Decodificamos la línea de bytes a texto
            line = raw_line.decode('utf-8', errors='replace').rstrip('\n')
            stripped = line.strip()

            # Buscamos líneas que comiencen con "INSERT INTO `nombre_tabla` VALUES"
            # Esto indica el inicio de los datos de una tabla
            m = re.match(r"INSERT INTO `(\w+)` VALUES", stripped)
            if m:
                current_table = m.group(1)
                in_insert = True
                continue

            if in_insert:
                if stripped.startswith('(') and current_table in TABLES_OF_INTEREST:
                    # Esta línea contiene una fila de datos de una tabla que nos interesa
                    # _tokenize_row() convierte el texto SQL en una lista de valores Python
                    raw_rows[current_table].append(_tokenize_row(stripped))
                elif not stripped.startswith('('):
                    # La línea ya no empieza con '(' → el bloque INSERT terminó
                    in_insert = False
                    current_table = None

    # --- Construir los DataFrames de pandas ---
    # Un DataFrame es una tabla con filas y columnas, como una hoja de Excel
    tables: dict[str, pd.DataFrame] = {}
    for table, rows in raw_rows.items():
        if not rows:
            # Si no encontramos filas para esta tabla, creamos un DataFrame vacío
            # con las columnas correctas según el esquema que extrajimos antes
            tables[table] = pd.DataFrame(columns=schemas.get(table, []))
            continue
        cols = schemas.get(table, [])
        # Alineamos cada fila para que tenga exactamente el mismo número de columnas que el esquema.
        # Si una fila tiene menos valores, rellenamos con None. Si tiene más, los recortamos.
        aligned = [r[:len(cols)] + [None] * max(0, len(cols) - len(r)) for r in rows]
        # Creamos el DataFrame pasando la lista de filas y los nombres de columnas
        tables[table] = pd.DataFrame(aligned, columns=cols)

    return tables


def _post_process(tables: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """
    Aplica conversiones de tipo y crea columnas derivadas en las tablas cargadas.

    En el volcado SQL, las fechas se guardan como números enteros (timestamps Unix):
    el número de segundos transcurridos desde el 1 de enero de 1970.
    Esta función convierte esos números a fechas legibles por humanos.
    También añade columnas útiles como 'sender' en los chats.

    Parámetros:
        tables (dict[str, pd.DataFrame]): El diccionario de tablas tal como salió de _parse_sql().

    Devuelve:
        dict[str, pd.DataFrame]: El mismo diccionario con los tipos de datos corregidos
                                 y las columnas adicionales añadidas.
    """
    import pandas as pd

    # --- Procesar la tabla 'clients' (víctimas del ransomware) ---
    clients = tables.get('clients')
    if clients is not None and 'date_first' in clients.columns:
        # pd.to_numeric() convierte los valores a número (por si hay textos mezclados)
        # errors='coerce' convierte los valores no numéricos a NaN (no disponible) en lugar de error
        # pd.to_datetime(..., unit='s', utc=True) convierte el timestamp Unix a fecha UTC legible
        clients['date_first'] = pd.to_datetime(
            pd.to_numeric(clients['date_first'], errors='coerce'), unit='s', utc=True
        )
        # Convertimos la fecha del último contacto con la víctima
        clients['date_last'] = pd.to_datetime(
            pd.to_numeric(clients['date_last'], errors='coerce'), unit='s', utc=True
        )
        # Convertimos la fecha de la última descarga del ransomware por la víctima
        # El 0 lo reemplazamos por None porque significa "nunca descargó"
        clients['last_download'] = pd.to_datetime(
            pd.to_numeric(clients['last_download'], errors='coerce').replace(0, None), unit='s', utc=True
        )
        # Guardamos la tabla modificada de vuelta en el diccionario
        tables['clients'] = clients

    # --- Procesar la tabla 'chats' (mensajes de negociación) ---
    chats = tables.get('chats')
    if chats is not None and 'created_at' in chats.columns:
        # 'created_at' ya viene en formato de texto ISO, pandas puede convertirlo directamente
        chats['created_at'] = pd.to_datetime(chats['created_at'], errors='coerce', utc=True)
        # 'date' viene como timestamp Unix, lo convertimos igual que antes
        chats['date'] = pd.to_datetime(
            pd.to_numeric(chats['date'], errors='coerce'), unit='s', utc=True
        )
        # Sender label: flag=1 → operator, flag=0 → victim
        # Creamos una columna 'sender' más legible a partir de la columna 'flag':
        # si flag=1, el mensaje lo envió el operador (criminal); si flag=0, lo envió la víctima.
        # .map() aplica esta transformación a cada valor de la columna 'flag'
        chats['sender'] = chats['flag'].map({1: 'operator', 0: 'victim'})
        tables['chats'] = chats

    # --- Procesar la tabla 'builds' (ejecutables de malware compilados) ---
    builds = tables.get('builds')
    if builds is not None and 'date' in builds.columns:
        # Convertimos la fecha de compilación de cada build de ransomware
        builds['date'] = pd.to_datetime(
            pd.to_numeric(builds['date'], errors='coerce'), unit='s', utc=True
        )
        tables['builds'] = builds

    # --- Procesar la tabla 'users' (operadores y afiliados de LockBit) ---
    users = tables.get('users')
    if users is not None and 'last_online' in users.columns:
        # Creamos columnas nuevas con el sufijo '_dt' para las versiones en formato fecha
        # 'last_online_dt': cuándo estuvo activo por última vez el operador
        users['last_online_dt'] = pd.to_datetime(
            pd.to_numeric(users['last_online'], errors='coerce'), unit='s', utc=True
        )
        # 'reg_date_dt': cuándo se registró el operador en el panel de LockBit
        users['reg_date_dt'] = pd.to_datetime(
            pd.to_numeric(users['reg_date'], errors='coerce'), unit='s', utc=True
        )
        tables['users'] = users

    # --- Procesar la tabla 'invites' (códigos de invitación para reclutar afiliados) ---
    invites = tables.get('invites')
    if invites is not None and 'created_at' in invites.columns:
        # Convertimos la fecha de creación de cada código de invitación
        invites['created_at'] = pd.to_datetime(invites['created_at'], errors='coerce', utc=True)
        tables['invites'] = invites

    return tables


def load_lockbit(path) -> dict[str, pd.DataFrame]:
    """
    Carga el volcado de la base de datos del panel de LockBit y devuelve sus tablas.

    Esta es la función pública del módulo: la única que se llama desde los notebooks.
    Internamente coordina el análisis del SQL (_parse_sql) y la corrección de tipos
    (_post_process) para devolver tablas listas para el análisis.

    Parámetros:
        path (str o Path): Ruta al archivo .sql o .zip que contiene el volcado de LockBit.

    Devuelve:
        dict[str, pd.DataFrame]: Un diccionario con las siguientes tablas como DataFrames:
            - 'users':        Operadores y afiliados del panel de LockBit
            - 'clients':      Víctimas del ransomware
            - 'chats':        Mensajes de negociación entre operadores y víctimas
            - 'builds':       Ejecutables de ransomware compilados para cada víctima
            - 'btc_addresses':Billeteras Bitcoin para recibir pagos de rescate
            - 'invites':      Códigos de invitación para reclutar nuevos afiliados
            - 'pkeys':        Claves criptográficas asociadas a las víctimas
    """
    # Nos aseguramos de que la ruta sea un objeto Path para poder usar sus métodos
    # (como .suffix para ver la extensión del archivo)
    path = Path(path)

    # Primera fase: leer y analizar el archivo SQL, extrayendo las tablas como DataFrames crudos
    tables = _parse_sql(path)

    # Segunda fase: mejorar los tipos de datos (convertir fechas, añadir columnas útiles)
    tables = _post_process(tables)

    # Devolvemos el diccionario completo con todas las tablas listas para usar
    return tables
