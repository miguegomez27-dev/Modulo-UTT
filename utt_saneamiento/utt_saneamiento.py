"""Clase principal del plugin UTT Saneamiento."""

from qgis.PyQt.QtWidgets import QAction, QMenu

from .core.filter_manager import LayerFilterManager
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
        """Constructor del plugin.

        Parameters
        ----------
        iface : qgis.gui.QgisInterface
            Referencia a la interfaz principal de QGIS.
        """
        self.iface = iface
        self.menu = None
        self.main_action = None
        self.dialog = None
        self.filter_manager = LayerFilterManager(iface)
        self.ambito_actions = []

    def initGui(self):
        """Registra menu y acciones al cargar el plugin en QGIS."""
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
        """Limpia recursos UI al desactivar el plugin."""
        if self.menu is not None:
            self.iface.pluginMenu().removeAction(self.menu.menuAction())
            self.menu.deleteLater()
            self.menu = None
        self.main_action = None
        self.dialog = None
        self.ambito_actions = []

    def open_dialog(self):
        """Abre el dialogo principal del MVP."""
        if self.dialog is None:
            self.dialog = UttSaneamientoDialog(self.iface, self.filter_manager)
        self.dialog.refresh_layers_and_filters()
        self.dialog.show()
        self.dialog.raise_()
        self.dialog.activateWindow()
