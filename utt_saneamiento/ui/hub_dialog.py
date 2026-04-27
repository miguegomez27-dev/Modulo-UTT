"""Panel principal de navegación del plugin UTT Saneamiento."""

from qgis.PyQt.QtWidgets import QDialog, QGridLayout, QLabel, QPushButton, QVBoxLayout


class UttSaneamientoHubDialog(QDialog):
    """Menú principal con acceso a submódulos."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("UTT | Carga (MVP)")
        self.setMinimumWidth(980)
        self.setMinimumHeight(520)

        self.btn_produccion = QPushButton("PRODUCCIÓN")
        self.btn_colindancias = QPushButton("COLINDANCIAS")
        self.btn_informes = QPushButton("INFORMES")
        self.btn_tracto = QPushButton("TRACTO SUCESIVO")
        self.btn_registro = QPushButton("REGISTRO GRÁFICO")
        self.btn_genealogia = QPushButton("GENEALOGÍA")
        self.btn_hrg = QPushButton("HRG")
        self.btn_proyecto = QPushButton("PROYECTO POR PEDANÍA")
        self.btn_filtros = QPushButton("FILTROS")

        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel("¿Qué querés cargar?")
        title.setStyleSheet("font-weight: bold; font-size: 32px;")
        subtitle = QLabel("Seleccioná un módulo:")
        subtitle.setStyleSheet("font-size: 18px;")

        layout.addWidget(title)
        layout.addWidget(subtitle)

        grid = QGridLayout()
        buttons = [
            (self.btn_produccion, 0, 0),
            (self.btn_colindancias, 0, 1),
            (self.btn_informes, 1, 0),
            (self.btn_tracto, 1, 1),
            (self.btn_registro, 2, 0),
            (self.btn_genealogia, 2, 1),
            (self.btn_hrg, 3, 0),
            (self.btn_proyecto, 3, 1),
            (self.btn_filtros, 4, 0),
        ]

        for btn, row, col in buttons:
            btn.setMinimumHeight(56)
            btn.setStyleSheet(
                "QPushButton {background:#0F4DA0; color:white; font-size:20px; font-weight:600; border-radius:12px; padding:10px;}"
                "QPushButton:disabled {background:#9BA3AF; color:#F3F4F6;}"
            )
            grid.addWidget(btn, row, col)

        # MVP aún no implementados
        self.btn_tracto.setEnabled(False)
        self.btn_genealogia.setEnabled(False)
        self.btn_hrg.setEnabled(False)
        self.btn_proyecto.setEnabled(False)

        layout.addLayout(grid)
