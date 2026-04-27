"""Clase principal del plugin UTT Saneamiento."""

from qgis.PyQt.QtWidgets import QAction, QMenu

from .core.filter_manager import LayerFilterManager
from .ui.hub_dialog import UttSaneamientoHubDialog
from .ui.main_dialog import UttSaneamientoDialog


class UttSaneamientoPlugin:
    """Inicializa UI, acciones y ciclo de vida del plugin."""

    AMBITOS = [
        "Produccion",
        "Genealogia",
        "Filtros",
        "HRG",
        "Informes",
        "Estudio de titulos",
        "Colindancias",
        "Historial de registro grafico",
    ]

    def __init__(self, iface):
        self.iface = iface
        self.menu = None
        self.main_action = None
        self.dialog = None
        self.hub_dialog = None
        self.filter_manager = LayerFilterManager(iface)
        self.ambito_actions = []
        self.informes_dialog = None
        self.produccion_dialog = None
        self.historial_dialog = None

    def initGui(self):
        self.main_action = QAction("UTT Saneamiento", self.iface.mainWindow())
        self.main_action.triggered.connect(self.open_dialog)

        self.menu = QMenu("UTT Saneamiento", self.iface.mainWindow())
        self.menu.addAction(self.main_action)
        self.menu.addSeparator()

        for ambito in self.AMBITOS:
            action = QAction(ambito, self.iface.mainWindow())
            action.setEnabled(False)
            self.menu.addAction(action)
            self.ambito_actions.append(action)

        self.iface.pluginMenu().addMenu(self.menu)

    def unload(self):
        if self.menu is not None:
            self.iface.pluginMenu().removeAction(self.menu.menuAction())
            self.menu.deleteLater()
            self.menu = None

        self.main_action = None
        self.dialog = None
        self.hub_dialog = None
        self.informes_dialog = None
        self.produccion_dialog = None
        self.historial_dialog = None
        self.ambito_actions = []

    def open_dialog(self):
        """Abre el panel principal de módulos."""
        if self.hub_dialog is None:
            self.hub_dialog = UttSaneamientoHubDialog(self.iface.mainWindow())
            self._wire_hub_buttons()

        self.hub_dialog.show()
        self.hub_dialog.raise_()
        self.hub_dialog.activateWindow()

    def _wire_hub_buttons(self):
        self.hub_dialog.btn_produccion.clicked.connect(self.open_produccion_dialog)
        self.hub_dialog.btn_colindancias.clicked.connect(self.open_produccion_dialog)
        self.hub_dialog.btn_informes.clicked.connect(self.open_informes_dialog)
        self.hub_dialog.btn_registro.clicked.connect(self.open_historial_dialog)
        self.hub_dialog.btn_filtros.clicked.connect(self.open_filter_dialog)

    def _open_child_dialog(self, get_or_create_dialog):
        if self.hub_dialog is not None:
            self.hub_dialog.hide()

        dlg = get_or_create_dialog()
        dlg.finished.connect(self._show_hub_dialog)
        dlg.show()
        dlg.raise_()
        dlg.activateWindow()

    def _show_hub_dialog(self, *_):
        if self.hub_dialog is not None:
            self.hub_dialog.show()
            self.hub_dialog.raise_()
            self.hub_dialog.activateWindow()

    def open_filter_dialog(self):
        def factory():
            if self.dialog is None:
                self.dialog = UttSaneamientoDialog(self.iface, self.filter_manager)
            self.dialog.refresh_layers_and_filters()
            return self.dialog

        self._open_child_dialog(factory)

    def open_informes_dialog(self):
        def factory():
            if self.informes_dialog is None:
                from .informes.informes_dialog import UTTInformesDialog

                self.informes_dialog = UTTInformesDialog(self.iface.mainWindow())
            return self.informes_dialog

        self._open_child_dialog(factory)

    def open_produccion_dialog(self):
        def factory():
            if self.produccion_dialog is None:
                from .produccion.produccion_dialog import UTTCargaProduccionDialog

                self.produccion_dialog = UTTCargaProduccionDialog(self.iface.mainWindow())
            return self.produccion_dialog

        self._open_child_dialog(factory)

    def open_historial_dialog(self):
        def factory():
            if self.historial_dialog is None:
                from .historial.historial_dialog import HistorialRegistroGraficoDialog

                self.historial_dialog = HistorialRegistroGraficoDialog(
                    self.iface, self.iface.mainWindow()
                )
            return self.historial_dialog

        self._open_child_dialog(factory)
