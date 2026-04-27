"""Consulta de historial gráfico desde tablas PostGIS cargadas en QGIS."""

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import (
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)
from qgis.core import QgsFeatureRequest, QgsProject


class HistorialRegistroGraficoDialog(QDialog):
    """Consulta auditoría de operaciones gráficas y producción histórica."""

    AUD_LAYER_CANDIDATES = [
        "auditorias_operaciones_graficas",
        "auditoria_operaciones_graficas",
        "saneamiento.auditorias_operaciones_graficas",
        "saneamiento.auditoria_operaciones_graficas",
    ]
    PROD_LAYER_CANDIDATES = [
        "produccion_historica",
        "saneamiento.produccion_historica",
    ]

    AUD_FIELDS_TO_SHOW = ["pg_url", "pg_key", "log_operacion", "origen", "fecha", "nombre"]
    PROD_FIELDS_TO_SHOW = ["casuisticas", "observaciones"]

    FILTER_CUENTA_CANDIDATES = ["cuenta", "pg_url"]
    FILTER_NOMEN_CANDIDATES = ["nomenclatura", "pg_key"]

    MAX_RESULTS = 500

    def __init__(self, iface, parent=None):
        super().__init__(parent)
        self.iface = iface
        self.setWindowTitle("UTT | Historial de registro gráfico")
        self.resize(1050, 620)

        self.audit_layer = None
        self.prod_layer = None

        self.txt_cuenta = QLineEdit()
        self.txt_nomen = QLineEdit()
        self.lbl_estado = QLabel("")

        self.table_prod = QTableWidget(0, 2)
        self.table_aud = QTableWidget(0, 6)

        self._build_ui()
        self._wire_events()
        self._resolve_layers()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        form = QFormLayout()
        self.txt_cuenta.setPlaceholderText("Pegá Cuenta (opcional)")
        self.txt_nomen.setPlaceholderText("Pegá Nomenclatura (opcional)")
        form.addRow("Cuenta:", self.txt_cuenta)
        form.addRow("Nomenclatura:", self.txt_nomen)
        layout.addLayout(form)

        btns = QHBoxLayout()
        self.btn_buscar = QPushButton("Buscar")
        self.btn_limpiar = QPushButton("Limpiar")
        btns.addWidget(self.btn_buscar)
        btns.addWidget(self.btn_limpiar)
        btns.addStretch(1)
        layout.addLayout(btns)

        self.lbl_estado.setWordWrap(True)
        layout.addWidget(self.lbl_estado)

        layout.addWidget(QLabel("Producción histórica (Casuísticas / Observaciones):"))
        self.table_prod.setHorizontalHeaderLabels(["CASUISTICAS", "OBSERVACIONES"])
        self.table_prod.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_prod.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_prod.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table_prod)

        layout.addWidget(QLabel("Auditoría operaciones gráficas:"))
        self.table_aud.setHorizontalHeaderLabels([c.upper() for c in self.AUD_FIELDS_TO_SHOW])
        self.table_aud.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_aud.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_aud.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table_aud)

    def _wire_events(self):
        self.btn_buscar.clicked.connect(self.search)
        self.btn_limpiar.clicked.connect(self.clear_all)
        self.txt_cuenta.returnPressed.connect(self.search)
        self.txt_nomen.returnPressed.connect(self.search)

    def _resolve_layers(self):
        self.audit_layer = self._find_layer(self.AUD_LAYER_CANDIDATES)
        self.prod_layer = self._find_layer(self.PROD_LAYER_CANDIDATES)

        missing = []
        if not self.audit_layer:
            missing.append("auditorias_operaciones_graficas")
        if not self.prod_layer:
            missing.append("produccion_historica")

        if missing:
            self.lbl_estado.setText(
                "No se encontraron capas esperadas cargadas en QGIS: " + ", ".join(missing)
            )

    def _find_layer(self, name_candidates):
        all_layers = QgsProject.instance().mapLayers().values()
        normalized = {layer.name().lower(): layer for layer in all_layers}
        for candidate in name_candidates:
            if candidate.lower() in normalized:
                return normalized[candidate.lower()]
        return None

    def clear_all(self):
        self.txt_cuenta.clear()
        self.txt_nomen.clear()
        self.table_prod.setRowCount(0)
        self.table_aud.setRowCount(0)
        self.lbl_estado.setText("")

    def search(self):
        cuenta = self._norm_input(self.txt_cuenta.text())
        nomen = self._norm_input(self.txt_nomen.text())

        if not cuenta and not nomen:
            self.lbl_estado.setText("Ingresá al menos Cuenta o Nomenclatura.")
            return

        self._resolve_layers()
        if not self.audit_layer and not self.prod_layer:
            return

        try:
            prod_rows = self._query_prod(cuenta, nomen)
            aud_rows = self._query_aud(cuenta, nomen)

            self._populate_table(self.table_prod, self.PROD_FIELDS_TO_SHOW, prod_rows)
            self._populate_table(self.table_aud, self.AUD_FIELDS_TO_SHOW, aud_rows)

            self.lbl_estado.setText(
                f"Auditoría: {len(aud_rows)} fila(s) | Producción histórica: {len(prod_rows)} fila(s)"
            )
        except Exception as err:
            self.table_prod.setRowCount(0)
            self.table_aud.setRowCount(0)
            self.lbl_estado.setText(str(err))

    def _query_prod(self, cuenta, nomen):
        if not self.prod_layer:
            return []

        cuenta_field = self._resolve_existing_field(self.prod_layer, self.FILTER_CUENTA_CANDIDATES)
        nomen_field = self._resolve_existing_field(self.prod_layer, self.FILTER_NOMEN_CANDIDATES)

        expression = self._build_filter_expression(cuenta_field, nomen_field, cuenta, nomen)
        request = QgsFeatureRequest()
        if expression:
            request.setFilterExpression(expression)
        request.setLimit(self.MAX_RESULTS)

        rows = []
        prod_casu_field = self._resolve_existing_field(self.prod_layer, ["casuisticas", "casuistica"])
        prod_obs_field = self._resolve_existing_field(self.prod_layer, ["observaciones", "observacion", "obs"])

        for feature in self.prod_layer.getFeatures(request):
            rows.append(
                {
                    "casuisticas": self._display_val(feature[prod_casu_field]) if prod_casu_field else "",
                    "observaciones": self._display_val(feature[prod_obs_field]) if prod_obs_field else "",
                }
            )
        return rows

    def _query_aud(self, cuenta, nomen):
        if not self.audit_layer:
            return []

        cuenta_field = self._resolve_existing_field(self.audit_layer, ["pg_url", "cuenta"])
        nomen_field = self._resolve_existing_field(self.audit_layer, ["pg_key", "nomenclatura"])

        expression = self._build_filter_expression(cuenta_field, nomen_field, cuenta, nomen)
        request = QgsFeatureRequest()
        if expression:
            request.setFilterExpression(expression)
        request.setLimit(self.MAX_RESULTS)

        rows = []
        field_map = {f.name().lower(): f.name() for f in self.audit_layer.fields()}

        for feature in self.audit_layer.getFeatures(request):
            item = {}
            for desired in self.AUD_FIELDS_TO_SHOW:
                actual = field_map.get(desired.lower())
                item[desired] = self._display_val(feature[actual]) if actual else ""
            rows.append(item)

        if "fecha" in [f.lower() for f in self.audit_layer.fields().names()]:
            rows.sort(key=lambda r: r.get("fecha", ""), reverse=True)

        return rows

    def _build_filter_expression(self, cuenta_field, nomen_field, cuenta, nomen):
        clauses = []
        if cuenta and cuenta_field:
            cta = cuenta.replace("'", "''")
            clauses.append(f'("{cuenta_field}" = \'{cta}\' OR "{cuenta_field}" = \'\'{cta}\')')
        if nomen and nomen_field:
            nom = nomen.replace("'", "''")
            clauses.append(f'("{nomen_field}" = \'{nom}\' OR "{nomen_field}" = \'\'{nom}\')')
        return " AND ".join(clauses)

    @staticmethod
    def _norm_input(text):
        return text.strip().strip("'").strip('"')

    @staticmethod
    def _display_val(value):
        return "" if value is None else str(value)

    @staticmethod
    def _populate_table(table, columns, rows):
        table.setRowCount(0)
        table.setColumnCount(len(columns))
        table.setHorizontalHeaderLabels([c.upper() for c in columns])
        table.setRowCount(len(rows))

        for row_idx, row in enumerate(rows):
            for col_idx, col in enumerate(columns):
                value = row.get(col, "")
                item = QTableWidgetItem(value)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                table.setItem(row_idx, col_idx, item)

        table.resizeColumnsToContents()

    @staticmethod
    def _resolve_existing_field(layer, candidates):
        existing = {f.name().lower(): f.name() for f in layer.fields()}
        for candidate in candidates:
            found = existing.get(candidate.lower())
            if found:
                return found
        return None
