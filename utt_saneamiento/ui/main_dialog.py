"""Dialogo principal del plugin UTT Saneamiento (MVP)."""

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QVBoxLayout,
)


class UttSaneamientoDialog(QDialog):
    """Interfaz para detectar capas cargadas y filtrar por ambito administrativo."""

    def __init__(self, iface, filter_manager):
        """Construye el dialogo y conecta eventos.

        Parameters
        ----------
        iface : qgis.gui.QgisInterface
            Interfaz de QGIS para mensajeria al usuario.
        filter_manager : LayerFilterManager
            Componente con la logica de filtros multi-capa.
        """
        super().__init__(iface.mainWindow())
        self.iface = iface
        self.filter_manager = filter_manager

        self.setWindowTitle("UTT Saneamiento")
        self.resize(560, 460)

        self.layers_list = QListWidget()
        self.layers_list.setSelectionMode(QListWidget.NoSelection)

        self.departamento_combo = QComboBox()
        self.pedania_combo = QComboBox()
        self.localidad_combo = QComboBox()

        self.apply_button = QPushButton("Aplicar filtros")
        self.clear_button = QPushButton("Limpiar filtros")

        self._build_ui()
        self._connect_signals()

    def _build_ui(self):
        """Arma la estructura visual del dialogo."""
        main_layout = QVBoxLayout(self)

        main_layout.addWidget(QLabel("Capas vectoriales cargadas en QGIS:"))
        main_layout.addWidget(self.layers_list)

        filter_group = QGroupBox("Filtros administrativos")
        form_layout = QFormLayout(filter_group)

        self.departamento_combo.addItem("-- Seleccionar Departamento --", None)
        self.pedania_combo.addItem("-- Seleccionar Pedanía --", None)
        self.localidad_combo.addItem("-- Seleccionar Localidad --", None)

        form_layout.addRow("Departamento", self.departamento_combo)
        form_layout.addRow("Pedanía", self.pedania_combo)
        form_layout.addRow("Localidad", self.localidad_combo)

        main_layout.addWidget(filter_group)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.apply_button)
        button_layout.addWidget(self.clear_button)
        main_layout.addLayout(button_layout)

        note = QLabel(
            "Nota: Pedanía depende del Departamento, y Localidad depende de Pedanía."
        )
        note.setWordWrap(True)
        note.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        main_layout.addWidget(note)

    def _connect_signals(self):
        """Conecta cambios de combo y clicks de botones."""
        self.departamento_combo.currentIndexChanged.connect(self._on_departamento_changed)
        self.pedania_combo.currentIndexChanged.connect(self._on_pedania_changed)
        self.apply_button.clicked.connect(self.apply_filters)
        self.clear_button.clicked.connect(self.clear_filters)

    def refresh_layers_and_filters(self):
        """Actualiza lista de capas y reinicia combos de filtro."""
        self.layers_list.clear()
        compatible_layers = self.filter_manager.compatible_layers()
        for layer in compatible_layers:
            self.layers_list.addItem(layer.name())

        if not compatible_layers:
            self.layers_list.addItem("(No hay capas compatibles con filtros administrativos)")

        self._load_departamentos()
        self._reset_combo(self.pedania_combo, "-- Seleccionar Pedanía --")
        self._reset_combo(self.localidad_combo, "-- Seleccionar Localidad --")

    def _load_departamentos(self):
        """Carga departamentos disponibles desde capas detectadas."""
        self._reset_combo(self.departamento_combo, "-- Seleccionar Departamento --")
        values = self.filter_manager.distinct_values(self.filter_manager.FIELD_DEPARTAMENTO)
        for value in values:
            self.departamento_combo.addItem(value, value)

    def _on_departamento_changed(self):
        """Actualiza Pedanias cuando cambia Departamento."""
        departamento = self.departamento_combo.currentData()
        self._reset_combo(self.pedania_combo, "-- Seleccionar Pedanía --")
        self._reset_combo(self.localidad_combo, "-- Seleccionar Localidad --")

        if not departamento:
            return

        values = self.filter_manager.distinct_values(
            self.filter_manager.FIELD_PEDANIA,
            parent_filters={self.filter_manager.FIELD_DEPARTAMENTO: departamento},
        )
        for value in values:
            self.pedania_combo.addItem(value, value)

    def _on_pedania_changed(self):
        """Actualiza Localidades cuando cambia Pedania."""
        departamento = self.departamento_combo.currentData()
        pedania = self.pedania_combo.currentData()

        self._reset_combo(self.localidad_combo, "-- Seleccionar Localidad --")

        if not pedania:
            return

        values = self.filter_manager.distinct_values(
            self.filter_manager.FIELD_LOCALIDAD,
            parent_filters={
                self.filter_manager.FIELD_DEPARTAMENTO: departamento,
                self.filter_manager.FIELD_PEDANIA: pedania,
            },
        )
        for value in values:
            self.localidad_combo.addItem(value, value)

    def apply_filters(self):
        """Aplica filtro en todas las capas compatibles y muestra resultado."""
        departamento = self.departamento_combo.currentData()
        pedania = self.pedania_combo.currentData()
        localidad = self.localidad_combo.currentData()

        updated_layers, expression = self.filter_manager.apply_filter_to_layers(
            departamento=departamento,
            pedania=pedania,
            localidad=localidad,
        )

        message = (
            f"Filtro aplicado en {len(updated_layers)} capa(s)."
            if expression
            else "Sin criterios seleccionados: filtros vaciados en capas compatibles."
        )
        self.iface.messageBar().pushInfo("UTT Saneamiento", message)

    def clear_filters(self):
        """Limpia filtros en capas compatibles y reinicia combos."""
        cleared = self.filter_manager.clear_filters()
        self.refresh_layers_and_filters()
        self.iface.messageBar().pushInfo(
            "UTT Saneamiento", f"Filtros limpiados en {len(cleared)} capa(s)."
        )

    @staticmethod
    def _reset_combo(combo, placeholder):
        """Resetea un combo con opcion placeholder sin valor."""
        combo.blockSignals(True)
        combo.clear()
        combo.addItem(placeholder, None)
        combo.blockSignals(False)
