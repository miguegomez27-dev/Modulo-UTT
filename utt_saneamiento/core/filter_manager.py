"""Logica de deteccion de capas y aplicacion de filtros para UTT Saneamiento."""

from qgis.core import QgsProject, QgsVectorLayer


class LayerFilterManager:
    """Gestiona capas cargadas y aplica filtros administrativos en lote.

    Diseño basado en capas reales del esquema de saneamiento:
    - `san_cuentas`
    - `otax`

    En ambas pueden existir variantes de nombres de campo por mayúsculas/minúsculas,
    y combinaciones de código numérico + denominación textual.
    """

    FIELD_DEPARTAMENTO = "departamento"
    FIELD_PEDANIA = "pedania"
    FIELD_LOCALIDAD = "localidad"

    LEVEL_CANDIDATES = {
        "departamento": ["nombredepartamento", "departamento"],
        "pedania": ["nombrepedania", "pedania"],
        "localidad": ["nombrelocalidad", "localidad"],
    }

    def __init__(self, iface):
        """Inicializa el gestor de filtros."""
        self.iface = iface

    def loaded_vector_layers(self):
        """Retorna capas vectoriales actualmente cargadas en el proyecto."""
        layers = QgsProject.instance().mapLayers().values()
        return [layer for layer in layers if isinstance(layer, QgsVectorLayer)]

    def compatible_layers(self):
        """Capas vectoriales que tienen al menos un campo administrativo."""
        return [layer for layer in self.loaded_vector_layers() if any(self._resolve_admin_fields(layer).values())]

    def distinct_values(self, level, parent_filters=None):
        """Obtiene valores unicos por nivel administrativo."""
        if level not in self.LEVEL_CANDIDATES:
            return []

        parent_filters = parent_filters or {}
        values = set()

        for layer in self.compatible_layers():
            field_map = self._resolve_admin_fields(layer)
            if not field_map.get(level):
                continue

            for feature in layer.getFeatures():
                feature_values = self._extract_feature_admin_values(feature, field_map)
                if not self._matches_parent_filters(feature_values, parent_filters):
                    continue

                value = feature_values.get(level)
                if value not in (None, ""):
                    values.add(str(value))

        return sorted(values)

    def apply_filter_to_layers(self, departamento=None, pedania=None, localidad=None):
        """Aplica filtros administrativos en todas las capas compatibles."""
        criteria = {
            "departamento": departamento,
            "pedania": pedania,
            "localidad": localidad,
        }

        updated_layers = []
        sample_expression = ""

        for layer in self.compatible_layers():
            expression = self._build_expression_for_layer(layer, criteria)
            if expression is None:
                continue

            layer.setSubsetString(expression)
            updated_layers.append(layer.name())
            if expression and not sample_expression:
                sample_expression = expression

        return updated_layers, sample_expression

    def clear_filters(self):
        """Limpia filtros en capas compatibles."""
        cleared_layers = []
        for layer in self.compatible_layers():
            layer.setSubsetString("")
            cleared_layers.append(layer.name())
        return cleared_layers

    def _build_expression_for_layer(self, layer, criteria):
        """Arma expresión de filtro según campos existentes en la capa."""
        field_map = self._resolve_admin_fields(layer)
        if not any(field_map.values()):
            return None

        conditions = []
        for level, selected_value in criteria.items():
            if selected_value in (None, ""):
                continue

            field_name = field_map.get(level)
            if not field_name:
                continue

            rendered = self._format_value_for_layer_field(layer, field_name, selected_value)
            conditions.append(f'"{field_name}" = {rendered}')

        return " AND ".join(conditions)

    def _resolve_admin_fields(self, layer):
        """Determina el campo real por nivel administrativo en una capa."""
        resolved = {}
        for level, candidates in self.LEVEL_CANDIDATES.items():
            actual = None
            for candidate in candidates:
                actual = self._resolve_field_name(layer, candidate)
                if actual:
                    break
            resolved[level] = actual
        return resolved

    def _extract_feature_admin_values(self, feature, field_map):
        """Extrae valores normalizados por nivel desde un feature."""
        values = {}
        for level, field_name in field_map.items():
            if not field_name:
                values[level] = None
                continue
            raw = feature[field_name]
            values[level] = None if raw in (None, "") else str(raw)
        return values

    @staticmethod
    def _matches_parent_filters(feature_values, parent_filters):
        """Valida jerarquía Departamento -> Pedanía -> Localidad."""
        for level, expected in parent_filters.items():
            if expected and str(feature_values.get(level)) != str(expected):
                return False
        return True

    def _format_value_for_layer_field(self, layer, field_name, value):
        """Formatea valor para expresión según tipo real del campo."""
        index = layer.fields().lookupField(field_name)
        if index == -1:
            return f"'{self._escape(value)}'"

        field = layer.fields().field(index)
        is_numeric = getattr(field, "isNumeric", None)

        if callable(is_numeric) and is_numeric():
            return str(value)

        if str(field.typeName()).lower() in {"integer", "int", "numeric", "double", "real", "float"}:
            return str(value)

        return f"'{self._escape(value)}'"

    def _resolve_field_name(self, layer, requested_name):
        """Resuelve nombre real de campo de manera case-insensitive."""
        if self._has_field(layer, requested_name):
            return requested_name

        lower_map = {f.name().lower(): f.name() for f in layer.fields()}
        return lower_map.get(requested_name.lower())

    @staticmethod
    def _escape(value):
        """Escapa comillas simples para evitar expresiones inválidas."""
        return str(value).replace("'", "''")

    @staticmethod
    def _has_field(layer, field_name):
        """Indica si la capa contiene el campo solicitado."""
        return layer.fields().lookupField(field_name) != -1
