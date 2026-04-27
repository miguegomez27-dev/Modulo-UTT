"""Punto de entrada del plugin UTT Saneamiento para QGIS."""


def classFactory(iface):
    """Crea la instancia principal del plugin.

    Parameters
    ----------
    iface : qgis.gui.QgisInterface
        Interfaz de QGIS que permite registrar menus, acciones y capas.
    """
    from .utt_saneamiento import UttSaneamientoPlugin

    return UttSaneamientoPlugin(iface)
