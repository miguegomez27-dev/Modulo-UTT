# UTT Saneamiento (Plugin QGIS 3.x)

MVP del plugin **UTT Saneamiento** para trabajar con capas de saneamiento en PostgreSQL/PostGIS desde QGIS.

## Alcance de esta versión

- Menú principal con ámbitos de trabajo (solo estructura visual):
  - Producción
  - Genealogía
  - Filtros
  - HRG
  - Informes
  - Estudio de títulos
  - Colindancias
  - Historial de registro gráfico
- Detección de capas vectoriales cargadas en QGIS.
- Filtro jerárquico por:
  - Departamento
  - Pedanía (dentro de Departamento)
  - Localidad (dentro de Pedanía)
- Aplicación automática del filtro a múltiples capas compatibles.
- Botón para limpiar filtros.

> No se agregaron funcionalidades fuera del MVP solicitado.

## Estructura

- `metadata.txt`: metadatos del plugin para QGIS.
- `__init__.py`: punto de entrada (`classFactory`).
- `utt_saneamiento.py`: inicialización del menú/acciones y apertura de diálogo.
- `core/filter_manager.py`: lógica de detección de capas y filtros.
- `ui/main_dialog.py`: interfaz PyQGIS/PyQt para el flujo del usuario.
- `icon.png`: icono placeholder.

## Instalación manual en QGIS

1. Copiar la carpeta `utt_saneamiento` al directorio de plugins de QGIS.
2. Reiniciar QGIS.
3. Activar el plugin desde `Complementos > Administrar e instalar complementos`.

## Campos esperados para filtros

El MVP asume nombres de campos exactos en las capas:

- `departamento`
- `pedania`
- `localidad`

Si una capa no tiene esos campos, no se incluye en el filtrado.
