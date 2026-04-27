"""Diálogo de Producción/Colindancias basado en flujo operativo UTT."""

import getpass

from qgis.PyQt.QtCore import QDateTime
from qgis.PyQt.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)
from qgis.core import QgsFeature, QgsFeatureRequest, QgsProject
from qgis.utils import iface


class UTTCargaProduccionDialog(QDialog):
    """MVP de carga operativa para Producción y Colindancias."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("UTT | Carga (MVP)")
        self.setMinimumWidth(740)

        self.layer_name = "colindancias_parcelas"
        self.prod_layer_candidates = ["produccion_saneamiento", "produccion", "utt_produccion"]
        self.layer = None
        self.current_feature = None
        self.current_prod_ctx = None

        root = QVBoxLayout()
        self.stack = QStackedWidget()

        self.page_selector = self._build_page_selector()
        self.page_produccion = self._build_page_produccion()
        self.page_colindancias = self._build_page_colindancias()

        self.stack.addWidget(self.page_selector)
        self.stack.addWidget(self.page_produccion)
        self.stack.addWidget(self.page_colindancias)

        root.addWidget(self.stack)
        self.setLayout(root)

        self.layer = self._get_layer(self.layer_name)
        if not self.layer:
            QMessageBox.critical(
                self,
                "Error",
                (
                    f"No se encontró la capa '{self.layer_name}' en el proyecto.\n"
                    "Cargala y reabrí el diálogo."
                ),
            )

    def _build_page_selector(self):
        widget = QWidget()
        layout = QVBoxLayout()

        title = QLabel("¿Qué querés cargar?")
        title.setStyleSheet("font-weight: bold; font-size: 16px;")
        layout.addWidget(title)

        subtitle = QLabel("Seleccioná un módulo:")
        subtitle.setStyleSheet("color: #444;")
        layout.addWidget(subtitle)

        row = QHBoxLayout()
        self.btn_go_prod = QPushButton("PRODUCCIÓN")
        self.btn_go_prod.setMinimumHeight(46)
        self.btn_go_prod.clicked.connect(self._go_produccion)

        self.btn_go_col = QPushButton("COLINDANCIAS")
        self.btn_go_col.setMinimumHeight(46)
        self.btn_go_col.clicked.connect(self._go_colindancias)

        row.addWidget(self.btn_go_prod)
        row.addWidget(self.btn_go_col)
        layout.addLayout(row)

        hint = QLabel("Tip: Producción guarda un registro (log) por intervención.")
        hint.setStyleSheet("color: #666; margin-top: 12px;")
        layout.addWidget(hint)

        layout.addStretch(1)
        widget.setLayout(layout)
        return widget

    def _build_page_produccion(self):
        widget = QWidget()
        root = QVBoxLayout()

        title = QLabel("PRODUCCIÓN (Carga operativa)")
        title.setStyleSheet("font-weight: bold; font-size: 16px;")
        root.addWidget(title)

        id_row = QHBoxLayout()
        self.txt_prod_cuenta = QLineEdit()
        self.txt_prod_cuenta.setPlaceholderText("Ingresá CUENTA (opcional si ingresás Nomenclatura)")

        self.txt_prod_nomen = QLineEdit()
        self.txt_prod_nomen.setPlaceholderText("Ingresá NOMENCLATURA (opcional si ingresás Cuenta)")

        self.btn_prod_buscar = QPushButton("Vincular")
        self.btn_prod_buscar.clicked.connect(self.buscar_para_produccion)

        id_row.addWidget(QLabel("Cuenta:"))
        id_row.addWidget(self.txt_prod_cuenta, 1)
        id_row.addWidget(QLabel("Nomenclatura:"))
        id_row.addWidget(self.txt_prod_nomen, 1)
        id_row.addWidget(self.btn_prod_buscar)
        root.addLayout(id_row)

        self.lbl_prod_vinculo = QLabel("Sin vincular.")
        self.lbl_prod_vinculo.setStyleSheet("color:#666; margin: 6px 0 10px 0;")
        root.addWidget(self.lbl_prod_vinculo)

        grp = QGroupBox("Datos de producción")
        form = QFormLayout()

        self.cmb_casuistica = QComboBox()
        self.cmb_casuistica.addItem("— Seleccionar —", None)

        casuisticas = [
            "Dar de baja",
            "Verificar Alta",
            "Superposicion",
            "Redibujada",
            "Posesion",
            "Dar de alta",
            "Derecho y accion",
            "Modificar nomenclatura",
            "Borrada",
            "Dif de superficie",
            "Unidad Tributaria",
            "Unificar PH",
            "Empatada",
            "A eximir",
            "Graficada",
            "Analizada",
            "Sin informacion",
            "Calle/Canal",
        ]
        for item in sorted(casuisticas, key=lambda s: s.lower()):
            self.cmb_casuistica.addItem(item, item)

        self.spn_nuevas = QSpinBox()
        self.spn_nuevas.setRange(0, 999999)

        self.spn_modif = QSpinBox()
        self.spn_modif.setRange(0, 999999)

        self.txt_prod_obs = QPlainTextEdit()
        self.txt_prod_obs.setPlaceholderText("Observaciones (máx. 250 caracteres)")
        self.txt_prod_obs.setFixedHeight(90)
        self.txt_prod_obs.textChanged.connect(self._enforce_obs_limit)

        self.txt_dom_incorrecto = QLineEdit()
        self.txt_dom_incorrecto.setMaxLength(20)
        self.txt_dom_correcto = QLineEdit()
        self.txt_dom_correcto.setMaxLength(20)
        self.txt_plano_vinc_incorrecto = QLineEdit()
        self.txt_plano_vinc_incorrecto.setMaxLength(20)
        self.txt_plano_sin_vinc = QLineEdit()
        self.txt_plano_sin_vinc.setMaxLength(20)

        form.addRow("Casuística:", self.cmb_casuistica)
        form.addRow("Cantidad parcelas nuevas:", self.spn_nuevas)
        form.addRow("Cantidad parcelas modificadas:", self.spn_modif)
        form.addRow("Observaciones:", self.txt_prod_obs)

        opt = QGroupBox("Opcionales (20 caracteres c/u)")
        opt_form = QFormLayout()
        opt_form.addRow("Dominio incorrecto:", self.txt_dom_incorrecto)
        opt_form.addRow("Dominio correcto:", self.txt_dom_correcto)
        opt_form.addRow("Plano vinculado incorrecto:", self.txt_plano_vinc_incorrecto)
        opt_form.addRow("Plano sin vincular:", self.txt_plano_sin_vinc)
        opt.setLayout(opt_form)

        grp.setLayout(form)
        root.addWidget(grp)
        root.addWidget(opt)

        btns = QHBoxLayout()
        self.btn_prod_guardar = QPushButton("Guardar Producción")
        self.btn_prod_guardar.clicked.connect(self.guardar_produccion)
        self.btn_prod_guardar.setEnabled(False)

        btn_back = QPushButton("Volver")
        btn_back.clicked.connect(self._go_selector)
        btn_close = QPushButton("Cerrar")
        btn_close.clicked.connect(self.close)

        btns.addWidget(btn_back)
        btns.addStretch(1)
        btns.addWidget(self.btn_prod_guardar)
        btns.addWidget(btn_close)

        root.addLayout(btns)
        widget.setLayout(root)
        return widget

    def _build_page_colindancias(self):
        widget = QWidget()
        root = QVBoxLayout()

        title = QLabel("COLINDANCIAS (MVP)")
        title.setStyleSheet("font-weight: bold; font-size: 16px;")
        root.addWidget(title)

        row = QHBoxLayout()
        self.txt_cuenta = QLineEdit()
        self.txt_cuenta.setPlaceholderText("Ingresá CUENTA (texto)")

        self.btn_buscar = QPushButton("Buscar")
        self.btn_buscar.clicked.connect(self.buscar_cuenta)

        row.addWidget(QLabel("Cuenta:"))
        row.addWidget(self.txt_cuenta, 1)
        row.addWidget(self.btn_buscar)
        root.addLayout(row)

        grp = QGroupBox("Campos a actualizar")
        form = QFormLayout()

        self.txt_cn = QLineEdit()
        self.txt_cs = QLineEdit()
        self.txt_ce = QLineEdit()
        self.txt_co = QLineEdit()

        self.txt_obs = QPlainTextEdit()
        self.txt_obs.setPlaceholderText("OBSERVACIONES (campo en mayúscula)")
        self.txt_obs.setFixedHeight(90)

        form.addRow("C_N (Norte):", self.txt_cn)
        form.addRow("C_S (Sur):", self.txt_cs)
        form.addRow("C_E (Este):", self.txt_ce)
        form.addRow("C_O (Oeste):", self.txt_co)
        form.addRow("OBSERVACIONES:", self.txt_obs)

        grp.setLayout(form)
        root.addWidget(grp)

        btns = QHBoxLayout()
        self.btn_guardar = QPushButton("Guardar")
        self.btn_guardar.clicked.connect(self.guardar_colindancias)
        self.btn_guardar.setEnabled(False)

        btn_back = QPushButton("Volver")
        btn_back.clicked.connect(self._go_selector)
        btn_close = QPushButton("Cerrar")
        btn_close.clicked.connect(self.close)

        btns.addWidget(btn_back)
        btns.addStretch(1)
        btns.addWidget(self.btn_guardar)
        btns.addWidget(btn_close)

        root.addLayout(btns)
        widget.setLayout(root)
        return widget

    def _go_selector(self):
        self.stack.setCurrentIndex(0)

    def _go_produccion(self):
        self.stack.setCurrentIndex(1)

    def _go_colindancias(self):
        self.stack.setCurrentIndex(2)

    @staticmethod
    def _get_layer(name):
        layers = QgsProject.instance().mapLayersByName(name)
        return layers[0] if layers else None

    @staticmethod
    def _safe_str(value):
        return "" if value is None else str(value)

    def _enforce_obs_limit(self):
        text = self.txt_prod_obs.toPlainText()
        if len(text) <= 250:
            return

        self.txt_prod_obs.blockSignals(True)
        self.txt_prod_obs.setPlainText(text[:250])
        self.txt_prod_obs.blockSignals(False)

        cursor = self.txt_prod_obs.textCursor()
        cursor.movePosition(cursor.End)
        self.txt_prod_obs.setTextCursor(cursor)

    def _detect_user(self, layer_for_connection=None):
        try:
            if layer_for_connection and layer_for_connection.providerType().lower() == "postgres":
                conn = layer_for_connection.dataProvider().connection()
                rows = conn.executeSql("SELECT current_user;", feedback=None)
                first = next(iter(rows), None)
                if first and len(first) > 0:
                    return str(first[0])
        except Exception:
            pass

        try:
            return getpass.getuser()
        except Exception:
            return "desconocido"

    def _find_prod_layer(self):
        for name in self.prod_layer_candidates:
            layer = self._get_layer(name)
            if layer:
                return layer
        return None

    @staticmethod
    def _set_attr_by_candidates(feat, layer, candidates, value):
        field_names = [field.name() for field in layer.fields()]
        for candidate in candidates:
            if candidate in field_names:
                feat[candidate] = value
                return True
        return False

    def buscar_cuenta(self):
        if not self.layer:
            QMessageBox.critical(self, "Error", "No hay capa cargada. Revisá el nombre de la capa.")
            return

        cuenta = self.txt_cuenta.text().strip()
        if not cuenta:
            QMessageBox.warning(self, "Falta dato", "Ingresá una CUENTA.")
            return

        field_names = [field.name() for field in self.layer.fields()]
        needed = ["cuenta", "C_N", "C_S", "C_E", "C_O", "OBSERVACIONES"]
        missing = [field for field in needed if field not in field_names]
        if missing:
            QMessageBox.critical(self, "Error", f"Faltan campos en la capa: {', '.join(missing)}")
            return

        cuenta_sql = cuenta.replace("'", "''")
        request = QgsFeatureRequest().setFilterExpression(f'"cuenta" = \'{cuenta_sql}\'')
        features = [feature for feature in self.layer.getFeatures(request)]

        if not features:
            QMessageBox.information(self, "No encontrado", f"No existe la cuenta '{cuenta}' en '{self.layer_name}'.")
            self.current_feature = None
            self.btn_guardar.setEnabled(False)
            return

        if len(features) > 1:
            QMessageBox.warning(
                self, "Atención", f"Hay {len(features)} registros para la cuenta '{cuenta}'. Se usará el primero."
            )

        self.current_feature = features[0]
        self.txt_cn.setText(self._safe_str(self.current_feature["C_N"]))
        self.txt_cs.setText(self._safe_str(self.current_feature["C_S"]))
        self.txt_ce.setText(self._safe_str(self.current_feature["C_E"]))
        self.txt_co.setText(self._safe_str(self.current_feature["C_O"]))
        self.txt_obs.setPlainText(self._safe_str(self.current_feature["OBSERVACIONES"]))
        self.btn_guardar.setEnabled(True)

        self.layer.removeSelection()
        self.layer.select([self.current_feature.id()])
        iface.mapCanvas().zoomToSelected(self.layer)

    def guardar_colindancias(self):
        if not self.layer or not self.current_feature:
            QMessageBox.warning(self, "Sin cuenta", "Primero buscá una cuenta.")
            return

        self.layer.startEditing()

        self.current_feature["C_N"] = self.txt_cn.text().strip() or None
        self.current_feature["C_S"] = self.txt_cs.text().strip() or None
        self.current_feature["C_E"] = self.txt_ce.text().strip() or None
        self.current_feature["C_O"] = self.txt_co.text().strip() or None
        self.current_feature["OBSERVACIONES"] = self.txt_obs.toPlainText().strip() or None

        if not self.layer.updateFeature(self.current_feature):
            self.layer.rollBack()
            QMessageBox.critical(self, "Error", "No se pudo actualizar el registro (updateFeature=False).")
            return

        if not self.layer.commitChanges():
            errors = "\n".join(self.layer.commitErrors())
            self.layer.rollBack()
            QMessageBox.critical(self, "Error", f"No se pudo guardar:\n{errors}")
            return

        QMessageBox.information(self, "OK", "Colindancias guardadas correctamente.")
        self.btn_guardar.setEnabled(False)

    def buscar_para_produccion(self):
        if not self.layer:
            QMessageBox.critical(self, "Error", "No hay capa 'colindancias_parcelas' cargada para vincular.")
            return

        cuenta = self.txt_prod_cuenta.text().strip()
        nomenclatura = self.txt_prod_nomen.text().strip()

        if not cuenta and not nomenclatura:
            QMessageBox.warning(self, "Falta dato", "Ingresá CUENTA o NOMENCLATURA (con uno alcanza).")
            return

        fields = [field.name() for field in self.layer.fields()]
        if "cuenta" not in fields or "nomenclatura" not in fields:
            QMessageBox.critical(self, "Error", "La capa base no tiene los campos mínimos 'cuenta' y 'nomenclatura'.")
            return

        expressions = []
        if cuenta:
            cuenta_escaped = cuenta.replace("'", "''")
            expressions.append(f"\"cuenta\" = '{cuenta_escaped}'")
        if nomenclatura:
            nomen_escaped = nomenclatura.replace("'", "''")
            expressions.append(f"\"nomenclatura\" = '{nomen_escaped}'")

        request = QgsFeatureRequest().setFilterExpression(" OR ".join(expressions))
        features = [feature for feature in self.layer.getFeatures(request)]

        if not features:
            self.current_prod_ctx = {
                "cuenta": cuenta or None,
                "nomenclatura": nomenclatura or None,
            }
            self.lbl_prod_vinculo.setText(
                "No encontrado en colindancias_parcelas. Se cargará con lo ingresado (sin zoom)."
            )
            self.lbl_prod_vinculo.setStyleSheet("color:#aa5500; margin: 6px 0 10px 0;")
            self.btn_prod_guardar.setEnabled(True)
            return

        if len(features) > 1:
            QMessageBox.warning(self, "Atención", f"Hay {len(features)} coincidencias. Se usará la primera.")

        feature = features[0]
        cuenta_final = self._safe_str(feature["cuenta"])
        nomen_final = self._safe_str(feature["nomenclatura"])

        self.current_prod_ctx = {
            "cuenta": cuenta_final or None,
            "nomenclatura": nomen_final or None,
        }
        self.lbl_prod_vinculo.setText(f"Vinculado OK → Cuenta: {cuenta_final} | Nomenclatura: {nomen_final}")
        self.lbl_prod_vinculo.setStyleSheet("color:#2b6b2b; margin: 6px 0 10px 0;")
        self.btn_prod_guardar.setEnabled(True)

        self.layer.removeSelection()
        self.layer.select([feature.id()])
        iface.mapCanvas().zoomToSelected(self.layer)

    def guardar_produccion(self):
        if not self.current_prod_ctx:
            QMessageBox.warning(self, "Sin vincular", "Primero vinculá por Cuenta o Nomenclatura.")
            return

        cuenta = self.current_prod_ctx.get("cuenta")
        nomenclatura = self.current_prod_ctx.get("nomenclatura")
        if not cuenta and not nomenclatura:
            QMessageBox.warning(self, "Falta dato", "Debe existir CUENTA o NOMENCLATURA (con uno alcanza).")
            return

        casuistica = self.cmb_casuistica.currentData()
        if not casuistica:
            QMessageBox.warning(self, "Falta dato", "Seleccioná una CASUÍSTICA.")
            return

        obs = self.txt_prod_obs.toPlainText().strip()
        if len(obs) > 250:
            QMessageBox.warning(self, "Observaciones", "Observaciones excede 250 caracteres.")
            return

        dom_inc = self.txt_dom_incorrecto.text().strip()
        dom_cor = self.txt_dom_correcto.text().strip()
        pl_vinc_inc = self.txt_plano_vinc_incorrecto.text().strip()
        pl_sin_vinc = self.txt_plano_sin_vinc.text().strip()

        if any(len(value) > 20 for value in [dom_inc, dom_cor, pl_vinc_inc, pl_sin_vinc]):
            QMessageBox.warning(self, "Opcionales", "Algún campo opcional excede 20 caracteres.")
            return

        prod_layer = self._find_prod_layer()
        if not prod_layer:
            QMessageBox.critical(
                self,
                "Falta capa de producción",
                (
                    "No encontré una capa para guardar producción.\n"
                    "Cargá una tabla/capa llamada 'produccion_saneamiento' (recomendado), "
                    "o 'produccion' o 'utt_produccion' y reintentá."
                ),
            )
            return

        prod_fields = [field.name() for field in prod_layer.fields()]
        if not any(name in prod_fields for name in ["cuenta", "nomenclatura"]):
            QMessageBox.critical(
                self,
                "Estructura inválida",
                (
                    "La capa de producción no tiene ni 'cuenta' ni 'nomenclatura'.\n"
                    "Agregá esos campos o ajustá el mapeo en el script."
                ),
            )
            return

        feature = QgsFeature(prod_layer.fields())

        self._set_attr_by_candidates(feature, prod_layer, ["cuenta", "CUENTA"], cuenta)
        self._set_attr_by_candidates(feature, prod_layer, ["nomenclatura", "NOMENCLATURA"], nomenclatura)
        self._set_attr_by_candidates(
            feature,
            prod_layer,
            ["casuistica", "CASUISTICA", "cusuistica", "casuística"],
            casuistica,
        )

        now = QDateTime.currentDateTime()
        self._set_attr_by_candidates(
            feature,
            prod_layer,
            ["fecha", "FECHA", "fecha_carga", "fecha_prod", "fecha_produccion"],
            now,
        )

        usuario = self._detect_user(prod_layer)
        self._set_attr_by_candidates(
            feature,
            prod_layer,
            ["colaborador", "COLABORADOR", "usuario", "USUARIO", "user", "USERNAME"],
            usuario,
        )

        self._set_attr_by_candidates(
            feature,
            prod_layer,
            ["cant_nuevas", "nuevas", "parcelas_nuevas", "cantidad_nuevas"],
            int(self.spn_nuevas.value()),
        )
        self._set_attr_by_candidates(
            feature,
            prod_layer,
            ["cant_modificadas", "modificadas", "parcelas_modificadas", "cantidad_modificadas"],
            int(self.spn_modif.value()),
        )

        self._set_attr_by_candidates(
            feature,
            prod_layer,
            ["observaciones", "OBSERVACIONES", "obs", "OBS"],
            obs or None,
        )
        self._set_attr_by_candidates(feature, prod_layer, ["dominio_incorrecto", "dom_incorrecto"], dom_inc or None)
        self._set_attr_by_candidates(feature, prod_layer, ["dominio_correcto", "dom_correcto"], dom_cor or None)
        self._set_attr_by_candidates(
            feature,
            prod_layer,
            ["plano_vinculado_incorrecto", "plano_vinc_incorrecto"],
            pl_vinc_inc or None,
        )
        self._set_attr_by_candidates(
            feature,
            prod_layer,
            ["plano_sin_vincular", "plano_sin_vinc"],
            pl_sin_vinc or None,
        )

        prod_layer.startEditing()
        if not prod_layer.addFeature(feature):
            prod_layer.rollBack()
            QMessageBox.critical(
                self, "Error", "No se pudo insertar el registro de producción (addFeature=False)."
            )
            return

        if not prod_layer.commitChanges():
            errors = "\n".join(prod_layer.commitErrors())
            prod_layer.rollBack()
            QMessageBox.critical(self, "Error", f"No se pudo guardar producción:\n{errors}")
            return

        QMessageBox.information(self, "OK", f"Producción guardada. Usuario: {usuario}")
        self.btn_prod_guardar.setEnabled(False)

        self.cmb_casuistica.setCurrentIndex(0)
        self.spn_nuevas.setValue(0)
        self.spn_modif.setValue(0)
        self.txt_prod_obs.setPlainText("")
        self.txt_dom_incorrecto.setText("")
        self.txt_dom_correcto.setText("")
        self.txt_plano_vinc_incorrecto.setText("")
        self.txt_plano_sin_vinc.setText("")
        self.lbl_prod_vinculo.setText("Sin vincular.")
        self.lbl_prod_vinculo.setStyleSheet("color:#666; margin: 6px 0 10px 0;")
        self.current_prod_ctx = None
