from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QDoubleSpinBox, QSpinBox, QPushButton,
    QGroupBox, QGridLayout, QSizePolicy, QFrame,
)
import matplotlib
matplotlib.use("Qt5Agg")
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class CalcWindow(QWidget):
    def __init__(self, api_client, parent=None):
        super().__init__(parent)
        self.api = api_client
        self._build_ui()

    def _build_ui(self):
        main = QHBoxLayout(self)

        # Left panel — inputs
        left = QVBoxLayout()
        left.setContentsMargins(0, 0, 10, 0)

        inp_group = QGroupBox("Параметры расчёта")
        form = QFormLayout()
        form.setVerticalSpacing(8)

        self.load_spin = QDoubleSpinBox()
        self.load_spin.setRange(1, 10000)
        self.load_spin.setValue(600)
        self.load_spin.setSuffix(" МВт")
        form.addRow("Нагрузка ТЭС:", self.load_spin)

        self.blocks_spin = QSpinBox()
        self.blocks_spin.setRange(1, 20)
        self.blocks_spin.setValue(2)
        form.addRow("Кол-во блоков:", self.blocks_spin)

        self.temp_spin = QDoubleSpinBox()
        self.temp_spin.setRange(-50, 60)
        self.temp_spin.setValue(15)
        self.temp_spin.setSuffix(" °C")
        form.addRow("Температура воздуха:", self.temp_spin)

        self.hum_spin = QDoubleSpinBox()
        self.hum_spin.setRange(0, 100)
        self.hum_spin.setValue(60)
        self.hum_spin.setSuffix(" %")
        form.addRow("Влажность:", self.hum_spin)

        self.wind_speed_spin = QDoubleSpinBox()
        self.wind_speed_spin.setRange(0, 50)
        self.wind_speed_spin.setValue(3)
        self.wind_speed_spin.setSuffix(" м/с")
        form.addRow("Скорость ветра:", self.wind_speed_spin)

        self.wind_dir_spin = QDoubleSpinBox()
        self.wind_dir_spin.setRange(0, 360)
        self.wind_dir_spin.setValue(180)
        self.wind_dir_spin.setSuffix(" °")
        form.addRow("Направление ветра:", self.wind_dir_spin)

        inp_group.setLayout(form)
        left.addWidget(inp_group)

        adv_group = QGroupBox("Дополнительно")
        adv_form = QFormLayout()
        adv_form.setVerticalSpacing(6)

        self.nom_power_spin = QDoubleSpinBox()
        self.nom_power_spin.setRange(1, 2000)
        self.nom_power_spin.setValue(300)
        self.nom_power_spin.setSuffix(" МВт")
        adv_form.addRow("Номинальная мощность блока:", self.nom_power_spin)

        self.nom_eff_spin = QDoubleSpinBox()
        self.nom_eff_spin.setRange(0.01, 1.0)
        self.nom_eff_spin.setSingleStep(0.01)
        self.nom_eff_spin.setDecimals(3)
        self.nom_eff_spin.setValue(0.38)
        adv_form.addRow("Номинальный КПД:", self.nom_eff_spin)

        self.own_needs_spin = QDoubleSpinBox()
        self.own_needs_spin.setRange(0, 0.3)
        self.own_needs_spin.setSingleStep(0.01)
        self.own_needs_spin.setDecimals(3)
        self.own_needs_spin.setValue(0.05)
        adv_form.addRow("Коэфф. собственных нужд:", self.own_needs_spin)

        adv_group.setLayout(adv_form)
        left.addWidget(adv_group)

        self.calc_btn = QPushButton("Рассчитать")
        self.calc_btn.setStyleSheet("font-size:14px; padding:8px; background:#1a6faf; color:white; border-radius:4px;")
        self.calc_btn.clicked.connect(self._run_calc)
        left.addWidget(self.calc_btn)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: red;")
        self.status_label.setWordWrap(True)
        left.addWidget(self.status_label)

        left.addStretch()
        main.addLayout(left, 2)

        # Right panel — results + chart
        right = QVBoxLayout()

        res_group = QGroupBox("Результаты расчёта")
        grid = QGridLayout()
        grid.setVerticalSpacing(6)
        grid.setHorizontalSpacing(16)

        labels = [
            ("Нагрузка на блок:", "load_per_block", " МВт"),
            ("КПД блока:", "block_efficiency_pct", " %"),
            ("КПД ТЭС брутто:", "efficiency_brutto_pct", " %"),
            ("Собственные нужды:", "own_needs_power_mw", " МВт"),
            ("Собственные нужды:", "own_needs_pct", " %"),
            ("КПД ТЭС нетто:", "efficiency_netto_pct", " %"),
            ("Удельный расход топлива:", "fuel_consumption", " г у.т./кВт·ч"),
        ]
        self._result_labels = {}
        for i, (name, key, suffix) in enumerate(labels):
            lbl = QLabel(name)
            lbl.setStyleSheet("font-weight: bold;")
            val = QLabel("—")
            val.setStyleSheet("font-size:13px;")
            grid.addWidget(lbl, i, 0)
            grid.addWidget(val, i, 1)
            self._result_labels[key] = (val, suffix)

        res_group.setLayout(grid)
        right.addWidget(res_group)

        # Chart
        chart_group = QGroupBox("График зависимости КПД нетто от температуры")
        chart_layout = QVBoxLayout()
        self.figure = Figure(figsize=(6, 3.5), tight_layout=True)
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        chart_layout.addWidget(self.canvas)
        chart_group.setLayout(chart_layout)
        right.addWidget(chart_group, 1)

        main.addLayout(right, 3)

    def _run_calc(self):
        self.status_label.setText("")
        self.calc_btn.setEnabled(False)

        params = {
            "total_load_mw": self.load_spin.value(),
            "num_blocks": self.blocks_spin.value(),
            "temp_c": self.temp_spin.value(),
            "humidity": self.hum_spin.value(),
            "wind_speed": self.wind_speed_spin.value(),
            "wind_dir": self.wind_dir_spin.value(),
            "nominal_power_per_block": self.nom_power_spin.value(),
            "nominal_efficiency": self.nom_eff_spin.value(),
            "own_needs_coeff": self.own_needs_spin.value(),
        }
        result = self.api.calculate(params)
        self.calc_btn.setEnabled(True)

        if not result["ok"]:
            self.status_label.setText(f"Ошибка: {result['error']}")
            return

        data = result["data"]
        for key, (label_widget, suffix) in self._result_labels.items():
            val = data.get(key, "—")
            label_widget.setText(f"{val}{suffix}")

        self._draw_chart(data.get("chart_data", []))

    def _draw_chart(self, chart_data: list):
        if not chart_data:
            return
        temps = [p["temp_c"] for p in chart_data]
        etas = [p["efficiency_netto_pct"] for p in chart_data]
        fuels = [p["fuel_consumption"] for p in chart_data]

        self.figure.clear()
        ax1 = self.figure.add_subplot(111)
        ax1.plot(temps, etas, "b-o", markersize=4, label="КПД нетто, %")
        ax1.set_xlabel("Температура воздуха, °C")
        ax1.set_ylabel("КПД нетто, %", color="blue")
        ax1.tick_params(axis="y", labelcolor="blue")
        ax1.grid(True, linestyle="--", alpha=0.5)

        ax2 = ax1.twinx()
        ax2.plot(temps, fuels, "r--s", markersize=4, label="Расход топлива")
        ax2.set_ylabel("Уд. расход топлива, г у.т./кВт·ч", color="red")
        ax2.tick_params(axis="y", labelcolor="red")

        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper right", fontsize=8)

        self.canvas.draw()
