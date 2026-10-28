"""Carga un PDF: uv run cargar_pdf.py ARCHIVO.pdf"""
import argparse
from pdf_rag import cargar_pdf


def main():
    parser = argparse.ArgumentParser(description="Indexar PDF en ChromaDB")
    parser.add_argument("pdf", help="Ruta del PDF")
    ruta = parser.parse_args().pdf
    nombre, paginas, fragmentos = cargar_pdf(ruta)
    print(f"PDF indexado: {paginas} páginas, {fragmentos} fragmentos. Colección: {nombre}")


if __name__ == "__main__":
    main()
