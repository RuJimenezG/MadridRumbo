"""Carga de documentos desde data/.

Convierte los archivos del corpus en objetos Document de LangChain.

Formatos soportados:
- .txt y .md → se cargan como documentos de texto.
- .pdf → se carga mediante PyPDFLoader.
- Paradas CRTM.csv → se transforma cada fila en un Document independiente.

Se omiten:
- Archivos .json.
- README.md.
"""

from pathlib import Path

import pandas as pd
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_core.documents import Document

from config import (
    CSV_PARADAS,
    DATA_DIR,
    EXTENSIONES_CSV,
    EXTENSIONES_PDF,
    EXTENSIONES_TEXTO,
    MAX_FILAS_CSV,
)


def valor_celda(fila, columna: str) -> str | None:
    """Obtiene el valor de una columna de una fila del DataFrame.

    Esta función sirve para acceder de forma segura a los valores del CSV.

    Devuelve:
    - El contenido de la celda convertido a texto y sin espacios
      al principio o al final.
    - None si la columna no existe.
    - None si la celda está vacía o contiene NaN.
    """

    # Comprobamos primero que la columna exista y que su valor no sea NaN.
    if columna not in fila or pd.isna(fila[columna]):
        return None

    # Convertimos el valor a string. Esto permite tratar de la misma forma IDs, números, nombres, etc.
    texto = str(fila[columna]).strip()

    # Si después de eliminar espacios queda una cadena vacía, la consideramos como un valor inexistente.
    return texto if texto else None


def fila_parada_a_texto(fila) -> str | None:
    """Convierte una fila de Paradas CRTM.csv en texto legible.

    Cada fila del CSV representa una parada, estación o punto de transporte.

    El objetivo es transformar los campos estructurados del CSV en un texto
    comprensible que posteriormente pueda ser procesado, fragmentado,
    convertido en embeddings y utilizado por el sistema RAG.

    Devuelve None si la fila no contiene los datos mínimos necesarios
    para identificar una parada.
    """

    # stop_id es el identificador interno de la parada dentro de los datos CRTM.
    stop_id = valor_celda(fila, "stop_id")

    # stop_name contiene el nombre legible de la parada.
    nombre = valor_celda(fila, "stop_name")

    # Consideramos que una fila sin ID o sin nombre no representa una parada suficientemente identificable para el RAG.
    if stop_id is None or nombre is None:
        return None

    # Empezamos el texto con los dos datos fundamentales: nombre de la parada e identificador.
    lineas = [
        f"Parada: {nombre}",
        f"ID de parada: {stop_id}",
    ]

    # Relacionamos el nombre que queremos mostrar en el texto con la columna correspondiente del CSV.
    #
    # Estos campos son opcionales porque algunas filas del fichero
    # tienen ciertos valores vacíos.
    campos_opcionales = [
        ("Código de parada", "stop_code"),
        ("Descripción / dirección", "stop_desc"),
        ("Tipo de transporte", "TIPO"),
        ("Zona tarifaria", "zone_id"),
        ("Latitud", "stop_lat"),
        ("Longitud", "stop_lon"),
        ("Tipo de ubicación GTFS", "location_type"),
        ("Estación padre", "parent_station"),
        ("Zona horaria", "stop_timezone"),
        ("Accesibilidad en silla de ruedas (GTFS)", "wheelchair_boarding"),
    ]

    # Añadimos únicamente los campos que realmente contienen información. De esta forma evitamos generar textos como:
    #   Estación padre: ?
    #   Zona horaria: ?
    # cuando esos datos no existen en la fila.
    for etiqueta, columna in campos_opcionales:
        valor = valor_celda(fila, columna)

        if valor is not None:
            lineas.append(f"{etiqueta}: {valor}")

    # Convertimos la lista de líneas en un único string. Ejemplo aproximado:
    # Parada: PLAZA DE CASTILLA
    # ID de parada: par_4_1
    # Código de parada: 1
    # Descripción / dirección: Paseo de la Castellana 189
    # Tipo de transporte: metro
    # Zona tarifaria: A
    # ...
    return "\n".join(lineas)


def cargar_paradas_csv(ruta: Path) -> list[Document]:
    """Carga Paradas CRTM.csv y crea un Document por cada fila válida."""
    # Leemos el CSV con pandas.
    # sep=";"
    # El fichero utiliza punto y coma como separador de columnas.
    # encoding="latin-1"
    #   El CSV adjunto no está codificado como UTF-8. latin-1 permite interpretar correctamente los caracteres españoles.
    # dtype=str
    #   Fuerza a pandas a conservar todos los valores como texto.
    #   Esto es especialmente útil para identificadores, códigos y coordenadas, ya que no queremos que pandas los convierta automáticamente a int o float.
    df = pd.read_csv(
        ruta,
        sep=";",
        encoding="latin-1",
        dtype=str,
    )

    # Durante desarrollo puede ser útil procesar solamente las primeras
    # filas del CSV para acelerar las pruebas. Si MAX_FILAS_CSV es None, se procesará el fichero completo.
    if MAX_FILAS_CSV is not None:
        df = df.head(MAX_FILAS_CSV)

    # Aquí almacenaremos todos los Document generados.
    documentos: list[Document] = []

    # iterrows() permite recorrer el DataFrame fila por fila.
    # En este caso tiene sentido porque queremos que cada fila del CSV se convierta en un Document independiente de LangChain.
    for _, fila in df.iterrows():

        # Convertimos la fila estructurada del CSV en texto legible.
        texto = fila_parada_a_texto(fila)

        # Si la fila no tenía los datos mínimos necesarios, fila_parada_a_texto() devuelve None y la descartamos.
        if texto is None:
            continue

        # Los metadatos contienen información estructurada asociada al Document.
        # A diferencia de page_content, estos datos no forman parte directamente del texto que se utilizará para los embeddings, pero posteriormente pueden ser útiles para:
        # - identificar el origen del documento;
        # - saber qué parada produjo un resultado;
        # - filtrar por zona;
        # - filtrar por tipo de transporte;
        # - mostrar información adicional en las respuestas del RAG.
        metadata: dict = {
            "source": str(ruta),
            "tipo": "parada_crtm",
            "stop_id": valor_celda(fila, "stop_id"),
            "stop_code": valor_celda(fila, "stop_code"),
            "stop_name": valor_celda(fila, "stop_name"),
            "tipo_transporte": valor_celda(fila, "TIPO"),
            "zona": valor_celda(fila, "zone_id"),
            "parent_station": valor_celda(fila, "parent_station"),
        }

        # Creamos finalmente el objeto Document de LangChain.
        # page_content:
        #   texto que posteriormente podrá procesarse y convertirse en embeddings.
        # metadata:
        #   información estructurada relacionada con ese texto.
        documentos.append(
            Document(
                page_content=texto,
                metadata=metadata,
            )
        )

    # Devolvemos todos los Document creados a partir del CSV.
    return documentos


def cargar_archivo(ruta: Path) -> list[Document]:
    """Selecciona el loader adecuado según el tipo de archivo."""

    # Obtenemos la extensión en minúsculas. Por ejemplo:
    #   documento.PDF → ".pdf"
    #   datos.CSV     → ".csv"
    sufijo = ruta.suffix.lower()

    # Los PDF se cargan mediante PyPDFLoader.Normalmente se genera un Document por página.
    if sufijo in EXTENSIONES_PDF:
        return PyPDFLoader(str(ruta)).load()

    # Los archivos de texto (.txt, .md, etc.) se cargan completos mediante TextLoader.
    if sufijo in EXTENSIONES_TEXTO:
        return TextLoader(
            str(ruta),
            encoding="utf-8",
        ).load()

    # El CSV de paradas necesita un tratamiento específico.
    # No utilizamos un CSVLoader genérico porque queremos controlar exactamente cómo se transforma cada parada en texto y qué información se guarda en los metadatos.
    if sufijo in EXTENSIONES_CSV and ruta.name == CSV_PARADAS:
        return cargar_paradas_csv(ruta)

    # Si el archivo no pertenece a ninguno de los formatos soportados, devolvemos una lista vacía.
    return []


def cargar_documentos() -> list[Document]:
    """Recorre data/ y carga todos los documentos soportados del corpus."""

    # Antes de hacer nada comprobamos que exista la carpeta data/.
    if not DATA_DIR.exists():
        raise FileNotFoundError(
            f"No existe la carpeta de datos: {DATA_DIR}"
        )

    # Construimos la ruta en la que esperamos encontrar Paradas CRTM.csv.
    csv_path = DATA_DIR / CSV_PARADAS

    # El CSV de paradas forma parte obligatoria del corpus.
    # Si no existe, detenemos la ejecución mostrando un error claro.
    if not csv_path.is_file():
        raise FileNotFoundError(
            f"Falta {CSV_PARADAS} en data/. "
            "Comprueba que el corpus está en la carpeta data/."
        )

    # Lista en la que acumularemos los Document procedentes  de todos los archivos del corpus.
    documentos: list[Document] = []

    # rglob("*") recorre de forma recursiva DATA_DIR.
    # Esto significa que también encontrará archivos almacenados dentro de subdirectorios de data/.
    # sorted() hace que el orden de procesamiento sea reproducible.
    for ruta in sorted(DATA_DIR.rglob("*")):
        # Ignoramos directorios y nos quedamos únicamente con archivos.
        if not ruta.is_file():
            continue
        # Los JSON no forman parte del corpus que queremos cargar.
        if ruta.suffix.lower() == ".json":
            continue
        # README.md contiene documentación del proyecto, no información que deba formar parte del RAG.
        if ruta.name == "README.md":
            continue

        # Delegamos en cargar_archivo() la elección del loader.
        docs = cargar_archivo(ruta)

        # Si se han generado Document, los añadimos al corpus.
        if docs:
            print(
                f"  Cargado: {ruta.name} "
                f"({len(docs)} documento(s))"
            )
            documentos.extend(docs)
        # Si el archivo tiene extensión pero no existe un loader adecuado para él, mostramos un mensaje informativo.
        elif ruta.suffix:
            print(
                f"  [omitido] archivo no soportado: {ruta.name}"
            )

    # La función devuelve una única lista con todos los Document:
    # PDF + texto + paradas CRTM.
    return documentos