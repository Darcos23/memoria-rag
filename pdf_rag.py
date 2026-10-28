"""Utilidades compartidas para cargar PDF y recuperar fragmentos con ChromaDB."""
import hashlib
from pathlib import Path

import pymupdf

from almacen import crear_cliente, obtener_coleccion

RUTA_CHROMA = str(Path(__file__).resolve().parent / "datos" / "chroma")


def id_documento(ruta_pdf: Path) -> str:
    """ID estable por contenido. Evita mezclar PDFs diferentes."""
    sha = hashlib.sha256()
    with ruta_pdf.open("rb") as archivo:
        for bloque in iter(lambda: archivo.read(1024 * 1024), b""):
            sha.update(bloque)
    return "pdf_" + sha.hexdigest()[:20]


def coleccion_pdf(ruta_pdf: Path):
    nombre = id_documento(ruta_pdf)
    return obtener_coleccion(crear_cliente(RUTA_CHROMA), nombre)


def fragmentar(texto: str, tamano: int = 1000, solape: int = 150) -> list[str]:
    texto = " ".join(texto.split())
    if not texto:
        return []
    fragmentos = []
    inicio = 0
    while inicio < len(texto):
        fin = min(inicio + tamano, len(texto))
        if fin < len(texto):
            espacio = texto.rfind(" ", inicio + tamano // 2, fin)
            if espacio > inicio:
                fin = espacio
        fragmentos.append(texto[inicio:fin].strip())
        if fin == len(texto):
            break
        inicio = max(inicio + 1, fin - solape)
    return [frag for frag in fragmentos if frag]


def cargar_pdf(ruta: str) -> tuple[str, int, int]:
    pdf = Path(ruta).expanduser().resolve()
    if not pdf.is_file() or pdf.suffix.lower() != ".pdf":
        raise ValueError(f"No existe un PDF válido: {pdf}")
    coleccion = coleccion_pdf(pdf)
    # Con el mismo archivo no repetimos la indexación.
    if coleccion.count():
        with pymupdf.open(pdf) as documento:
            return coleccion.name, len(documento), coleccion.count()
    ids, textos, metas = [], [], []
    with pymupdf.open(pdf) as documento:
        paginas = len(documento)
        for num_pagina, pagina in enumerate(documento, start=1):
            texto = pagina.get_text("text")
            if not texto.strip():
                print(f"Página {num_pagina}: sin texto digital; intentando OCR...")
                tessdata = Path(r"C:\Program Files\Tesseract-OCR\tessdata")
                ruta_tessdata = str(tessdata) if tessdata.is_dir() else None
                idioma = "spa" if ruta_tessdata and (tessdata / "spa.traineddata").exists() else "eng"
                try:
                    textpage = pagina.get_textpage_ocr(
                        language=idioma, dpi=200, full=True, tessdata=ruta_tessdata
                    )
                    texto = pagina.get_text("text", textpage=textpage)
                except Exception as exc:
                    raise RuntimeError(
                        f"No se pudo aplicar OCR en la página {num_pagina}. "
                        "Instala Tesseract con 'winget install UB-Mannheim.TesseractOCR' "
                        "e incluye el idioma español (spa). "
                        f"Detalle: {exc}"
                    ) from exc
            for n, trozo in enumerate(fragmentar(texto), start=1):
                ids.append(f"p{num_pagina}_c{n}")
                textos.append(trozo)
                metas.append({"pagina": num_pagina, "archivo": pdf.name})
    if not textos:
        raise ValueError("No se pudo extraer texto del PDF, ni mediante OCR. Revisa si las páginas contienen texto legible.")
    for inicio in range(0, len(ids), 100):
        fin = inicio + 100
        coleccion.upsert(ids=ids[inicio:fin], documents=textos[inicio:fin], metadatas=metas[inicio:fin])
    return coleccion.name, paginas, len(textos)


def buscar(ruta: str, consulta: str, k: int = 5) -> list[dict]:
    coleccion = coleccion_pdf(Path(ruta).expanduser().resolve())
    if not coleccion.count():
        return []
    resultados = coleccion.query(
        query_texts=[consulta], n_results=min(k, coleccion.count()),
        include=["documents", "metadatas", "distances"],
    )
    return [
        {"texto": doc, "pagina": meta["pagina"], "distancia": dist}
        for doc, meta, dist in zip(
            resultados["documents"][0],
            resultados["metadatas"][0],
            resultados["distances"][0],
        )
    ]
