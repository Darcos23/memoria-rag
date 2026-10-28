"""Prueba independiente de la persistencia de Chroma sin clave de API."""
from almacen import crear_cliente, obtener_coleccion
from memoria_largo import MemoriaLargoPlazo
from memoria_medio import MemoriaMedioPlazo

cliente = crear_cliente()
hechos = MemoriaLargoPlazo(obtener_coleccion(cliente, "hechos"))
sesiones = MemoriaMedioPlazo(obtener_coleccion(cliente, "sesiones"))

hecho = "El usuario está aprendiendo memoria RAG con Python y uv"
hechos.guardar_hecho(hecho, importancia=9)
sesiones.resumen_sesion = "Hoy el usuario creó un sistema de memoria con ChromaDB"
sesiones.cerrar_sesion()

print("\nHechos relacionados:", hechos.recuperar("¿Qué está aprendiendo el usuario?"))
print("Sesiones relacionadas:", sesiones.recuperar("¿Qué hizo hoy el usuario con ChromaDB?"))
print("Prueba finalizada: los registros quedaron guardados en datos/chroma")
