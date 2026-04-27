import os

"""Diálogo de Informes para UTT Saneamiento (basado en flujo MVP operativo)."""

from qgis.PyQt.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QMessageBox,
    QStackedWidget,
    QWidget,
    QLineEdit,
    QGroupBox,
)
from qgis.core import QgsFeatureRequest, QgsProject
from qgis.utils import iface

from .informe_service import run_informe_calle


class UTTInformesDialog(QDialog):
    """Módulo de informes: selección de tipo y método de búsqueda/selección."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("UTT | Informes")
        self.setMinimumWidth(720)

        self.informe_tipo = None
        self.layer_name_default = "colindancias_parcelas"
        self.layer = self._get_layer(self.layer_name_default)
        plugin_root = os.path.dirname(os.path.dirname(__file__))
        self.ruta_plantilla_calle = os.path.join(
            plugin_root,
            "plantillas",
            "Plantilla_informe_baja_Calle.docx",
        )

        root = QVBoxLayout()
        self.stack = QStackedWidget()

        self.page_tipo = self._page_selector_tipo()
        self.page_metodo = self._page_selector_metodo()

        self.stack.addWidget(self.page_tipo)
        self.stack.addWidget(self.page_metodo)

        root.addWidget(self.stack)
        self.setLayout(root)

    def _page_selector_tipo(self):
        widget = QWidget()
        layout = QVBoxLayout()

        title = QLabel("¿Qué tipo de informe querés realizar?")
        title.setStyleSheet("font-weight: bold; font-size: 16px;")
        layout.addWidget(title)

        buttons = QHBoxLayout()
        col1 = QVBoxLayout()
        col2 = QVBoxLayout()

        b1 = QPushButton("Doble empadronamiento")
        b1.clicked.connect(lambda: self._set_tipo_y_continuar("doble_empadronamiento"))
        col1.addWidget(b1)

        b2 = QPushButton("Calle")
        b2.clicked.connect(lambda: self._set_tipo_y_continuar("calle"))
        col1.addWidget(b2)

        b3 = QPushButton("Plano origen")
        b3.clicked.connect(lambda: self._set_tipo_y_continuar("plano_origen"))
        col2.addWidget(b3)

        b4 = QPushButton("Prescripción adquisitiva")
        b4.clicked.connect(lambda: self._set_tipo_y_continuar("prescripcion_adquisitiva"))
        col2.addWidget(b4)

        b5 = QPushButton("FFCC")
        b5.clicked.connect(lambda: self._set_tipo_y_continuar("ffcc"))
        col2.addWidget(b5)

        col1.addStretch(1)
        col2.addStretch(1)

        buttons.addLayout(col1)
        buttons.addLayout(col2)
        layout.addLayout(buttons)

        layout.addStretch(1)

        row = QHBoxLayout()
        row.addStretch(1)
        close_btn = QPushButton("Cerrar")
        close_btn.clicked.connect(self.close)
        row.addWidget(close_btn)
        layout.addLayout(row)

        widget.setLayout(layout)
        return widget

    def _page_selector_metodo(self):
        widget = QWidget()
        layout = QVBoxLayout()

        self.lbl_header = QLabel("Informe: -")
        self.lbl_header.setStyleSheet("font-weight: bold; font-size: 16px;")
        layout.addWidget(self.lbl_header)

        info = QLabel("¿Cómo querés seleccionar las parcelas?")
        info.setStyleSheet("color: #444;")
        layout.addWidget(info)

        grp_buscar = QGroupBox("Buscar por CUENTA")
        grp_layout = QVBoxLayout()
        row = QHBoxLayout()

        self.txt_cuenta = QLineEdit()
        self.txt_cuenta.setPlaceholderText("Ingresá cuenta y presioná Buscar")

        self.btn_buscar = QPushButton("Buscar")
        self.btn_buscar.clicked.connect(self._buscar_por_cuenta)

        row.addWidget(self.txt_cuenta, 1)
        row.addWidget(self.btn_buscar)

        grp_layout.addLayout(row)
        grp_buscar.setLayout(grp_layout)
        layout.addWidget(grp_buscar)

        grp_sel = QGroupBox("Seleccionar en mapa")
        grp_sel_layout = QVBoxLayout()
        grp_sel_layout.addWidget(QLabel("Seleccioná las parcelas en el mapa y presioná Continuar."))

        self.btn_continuar_sel = QPushButton("Continuar (usar selección actual)")
        self.btn_continuar_sel.clicked.connect(self._usar_seleccion_actual)
        grp_sel_layout.addWidget(self.btn_continuar_sel)

        grp_sel.setLayout(grp_sel_layout)
        layout.addWidget(grp_sel)

        footer = QHBoxLayout()
        back = QPushButton("Volver")
        back.clicked.connect(self._volver_tipo)
        footer.addWidget(back)

        footer.addStretch(1)

        close_btn = QPushButton("Cerrar")
        close_btn.clicked.connect(self.close)
        footer.addWidget(close_btn)

        layout.addLayout(footer)
        layout.addStretch(1)

        widget.setLayout(layout)
        return widget

    def _set_tipo_y_continuar(self, tipo):
        self.informe_tipo = tipo
        self.lbl_header.setText(f"Informe: {self._tipo_label(tipo)}")
        self.stack.setCurrentIndex(1)

    def _volver_tipo(self):
        self.stack.setCurrentIndex(0)

    @staticmethod
    def _tipo_label(tipo):
        labels = {
            "doble_empadronamiento": "Doble empadronamiento",
            "calle": "Calle",
            "plano_origen": "Plano origen",
            "prescripcion_adquisitiva": "Prescripción adquisitiva",
            "ffcc": "FFCC",
        }
        return labels.get(tipo, tipo)

    @staticmethod
    def _get_layer(name):
        layers = QgsProject.instance().mapLayersByName(name)
        return layers[0] if layers else None

    def _ejecutar_informe(self, layer, seleccion):
        if not self.informe_tipo:
            QMessageBox.warning(self, "Aviso", "Primero elegí un tipo de informe.")
            return

        if self.informe_tipo == "calle":
            run_informe_calle(
                iface=iface,
                layer=layer,
                seleccion=seleccion,
                ruta_plantilla=self.ruta_plantilla_calle,
            )
            return

        QMessageBox.information(
            self,
            "Pendiente",
            (
                f"El informe '{self._tipo_label(self.informe_tipo)}' quedó seteado en la interfaz, "
                "pero en este MVP solo está implementado 'Calle'."
            ),
        )

    def _buscar_por_cuenta(self):
        if not self.layer:
            self.layer = self._get_layer(self.layer_name_default)

        if not self.layer:
            QMessageBox.critical(self, "Error", f"No encontré la capa '{self.layer_name_default}' cargada.")
            return

        cuenta = self.txt_cuenta.text().strip()
        if not cuenta:
            QMessageBox.warning(self, "Falta dato", "Ingresá una cuenta.")
            return

        cuenta_sql = cuenta.replace("'", "''")
        request = QgsFeatureRequest().setFilterExpression(f'"cuenta" = \'{cuenta_sql}\'')
        features = [feature for feature in self.layer.getFeatures(request)]

        if not features:
            QMessageBox.information(
                self,
                "No encontrado",
                f"No encontré la cuenta '{cuenta}' en '{self.layer_name_default}'.",
            )
            return

        self.layer.removeSelection()
        self.layer.select([feature.id() for feature in features])
        self._ejecutar_informe(self.layer, features)

    def _usar_seleccion_actual(self):
        layer = iface.activeLayer()
        if not layer:
            QMessageBox.warning(self, "Aviso", "No hay capa activa.")
            return

        selected = layer.selectedFeatures()
        if not selected:
            QMessageBox.warning(self, "Aviso", "No hay parcelas seleccionadas. Seleccioná y reintentá.")
            return

        self._ejecutar_informe(layer, selected)
