"""Logica de deteccion de capas y aplicacion de filtros para UTT Saneamiento."""

from qgis.core import QgsProject, QgsVectorLayer


class LayerFilterManager:
    """Gestiona capas cargadas y aplica filtros administrativos en lote."""

    FIELD_DEPARTAMENTO = "departamento"
    FIELD_PEDANIA = "pedania"
    FIELD_LOCALIDAD = "localidad"

    def __init__(self, iface):
        """Inicializa el gestor de filtros.

        Parameters
        ----------
        iface : qgis.gui.QgisInterface
            Interfaz de QGIS para mostrar mensajes y acceder al proyecto.
        """
        self.iface = iface

    def loaded_vector_layers(self):
        """Retorna capas vectoriales actualmente cargadas en el proyecto."""
        layers = QgsProject.instance().mapLayers().values()
        return [layer for layer in layers if isinstance(layer, QgsVectorLayer)]

    def distinct_values(self, field_name, parent_filters=None):
        """Obtiene valores unicos para un campo segun filtros previos.

        Parameters
        ----------
        field_name : str
            Campo a consultar (departamento, pedania o localidad).
        parent_filters : dict | None
            Filtros de contexto para niveles jerarquicos superiores.
        """
        values = set()
        parent_filters = parent_filters or {}

        for layer in self.loaded_vector_layers():
            if not self._has_field(layer, field_name):
                continue
            for feature in layer.getFeatures():
                if self._feature_matches_parents(feature, parent_filters):
                    value = feature[field_name]
                    if value not in (None, ""):
                        values.add(str(value))

        return sorted(values)

    def apply_filter_to_layers(self, departamento=None, pedania=None, localidad=None):
        """Construye y aplica expresion SQL-like en todas las capas compatibles."""
        filter_expression = self._build_expression(departamento, pedania, localidad)

        updated_layers = []
        for layer in self.loaded_vector_layers():
            applicable = any(
                self._has_field(layer, field)
                for field in (self.FIELD_DEPARTAMENTO, self.FIELD_PEDANIA, self.FIELD_LOCALIDAD)
            )
            if not applicable:
                continue
            layer.setSubsetString(filter_expression)
            updated_layers.append(layer.name())

        return updated_layers, filter_expression

    def clear_filters(self):
        """Limpia filtros en capas vectoriales con campos administrativos."""
        cleared_layers = []
        for layer in self.loaded_vector_layers():
            if any(
                self._has_field(layer, field)
                for field in (self.FIELD_DEPARTAMENTO, self.FIELD_PEDANIA, self.FIELD_LOCALIDAD)
            ):
                layer.setSubsetString("")
                cleared_layers.append(layer.name())
        return cleared_layers

    def _build_expression(self, departamento=None, pedania=None, localidad=None):
        """Arma la expresion de filtro respetando la jerarquia administrativa."""
        conditions = []
        if departamento:
            conditions.append(f'"{self.FIELD_DEPARTAMENTO}" = \'{self._escape(departamento)}\'')
        if pedania:
            conditions.append(f'"{self.FIELD_PEDANIA}" = \'{self._escape(pedania)}\'')
        if localidad:
            conditions.append(f'"{self.FIELD_LOCALIDAD}" = \'{self._escape(localidad)}\'')

        return " AND ".join(conditions)

    @staticmethod
    def _escape(value):
        """Escapa comillas simples para evitar expresiones invalidas."""
        return str(value).replace("'", "''")

    @staticmethod
    def _has_field(layer, field_name):
        """Indica si la capa contiene el campo solicitado."""
        return layer.fields().lookupField(field_name) != -1

    def _feature_matches_parents(self, feature, parent_filters):
        """Verifica que un feature coincida con los filtros de nivel superior."""
        for field_name, expected_value in parent_filters.items():
            if expected_value and str(feature[field_name]) != str(expected_value):
                return False
        return True
