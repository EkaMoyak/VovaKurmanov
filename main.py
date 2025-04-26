from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QComboBox, QDateEdit, QTableWidget,
    QTableWidgetItem, QTabWidget, QMessageBox, QAction, QMenuBar, QInputDialog,
    QFormLayout, QGraphicsOpacityEffect, QSizePolicy, QScrollArea, QFrame,
    QFileDialog
)
from PyQt5.QtGui import QColor, QFont, QDoubleValidator, QIcon, QPixmap, QPainter, QLinearGradient
from PyQt5.QtCore import (
    Qt, QDate, QPropertyAnimation, QEasingCurve, QSize, QPoint, QTimer,
    QSequentialAnimationGroup, QPauseAnimation
)
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.patches import Wedge
from datetime import datetime, timedelta
import json
import os
import sys
import random
from collections import defaultdict


class AnimatedButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
        self._animation = QPropertyAnimation(self, b"geometry")
        self._animation.setDuration(200)
        self._animation.setEasingCurve(QEasingCurve.OutQuad)

    def enterEvent(self, event):
        self._animation.stop()
        self._animation.setStartValue(self.geometry())
        self._animation.setEndValue(self.geometry().adjusted(-2, -2, 4, 4))
        self._animation.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._animation.stop()
        self._animation.setStartValue(self.geometry())
        self._animation.setEndValue(self.geometry().adjusted(2, 2, -4, -4))
        self._animation.start()
        super().leaveEvent(event)


class GradientLabel(QLabel):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self._gradient = QLinearGradient(0, 0, 0, 1)
        self._gradient.setColorAt(0, QColor("#6200EA"))
        self._gradient.setColorAt(1, QColor("#03DAC6"))
        self._gradient.setCoordinateMode(QLinearGradient.ObjectMode)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setPen(Qt.NoPen)
        self._gradient.setFinalStop(0, self.height())
        painter.setBrush(self._gradient)
        painter.drawRect(self.rect())
        painter.end()
        super().paintEvent(event)


class BudgetCard(QFrame):
    def __init__(self, title, value, color, icon=None, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            BudgetCard {{
                background-color: {color};
                border-radius: 15px;
                padding: 15px;
                border: none;
            }}
            QLabel {{
                color: white;
            }}
        """)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("font-size: 14px;")

        self.value_label = QLabel(value)
        self.value_label.setStyleSheet("font-size: 24px; font-weight: bold;")

        if icon:
            self.icon_label = QLabel()
            self.icon_label.setPixmap(QPixmap(icon).scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            self.icon_label.setStyleSheet("background-color: transparent;")

            title_layout = QHBoxLayout()
            title_layout.addWidget(self.icon_label)
            title_layout.addWidget(self.title_label)
            title_layout.addStretch()

            self.layout.addLayout(title_layout)
        else:
            self.layout.addWidget(self.title_label)

        self.layout.addWidget(self.value_label)

        # Анимация появления
        self.setGraphicsEffect(QGraphicsOpacityEffect())
        self.animation = QPropertyAnimation(self.graphicsEffect(), b"opacity")
        self.animation.setDuration(800)
        self.animation.setStartValue(0)
        self.animation.setEndValue(1)
        self.animation.setEasingCurve(QEasingCurve.OutBack)
        self.animation.start()


class SmartBudgetApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Умный Бюджет")
        self.setGeometry(100, 100, 1200, 800)

        # Цветовая палитра
        self.primary_color = QColor("#6200EA")  # Фиолетовый
        self.accent_color = QColor("#03DAC6")  # Бирюзовый
        self.background_color = QColor("#1E1E2E")  # Темно-синий
        self.card_color = QColor("#2A2A3A")  # Серо-синий
        self.text_color = QColor("#E4E6EB")  # Светло-серый
        self.positive_color = QColor("#4CAF50")  # Зеленый
        self.negative_color = QColor("#F44336")  # Красный

        # Основные данные
        self.transactions = []
        self.budget_categories = {
            "Доход": ["Зарплата", "Фриланс", "Инвестиции", "Подарки", "Другое"],
            "Расход": ["Еда", "Транспорт", "Жилье", "Развлечения", "Здоровье",
                       "Одежда", "Образование", "Другое"]
        }
        self.budget_limits = {}
        self.saving_goals = []
        self.regular_payments = []

        # Загрузка данных
        self.load_data()

        # Инициализация интерфейса
        self.init_ui()
        self.setup_animations()

    def init_ui(self):
        # Главный виджет
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)
        main_widget.setStyleSheet(f"""
            background-color: {self.background_color.name()};
            color: {self.text_color.name()};
        """)
        self.setCentralWidget(main_widget)

        # Заголовок с градиентом
        title = GradientLabel("Умный Бюджет")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            font-size: 32px; 
            font-weight: bold; 
            padding: 20px;
            border-bottom: 2px solid #03DAC6;
            color: white;
        """)
        main_layout.addWidget(title)

        # Вкладки
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabBar::tab {{
                background: {self.card_color.name()};
                color: {self.text_color.name()};
                padding: 15px;
                border: none;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
                margin-right: 2px;
            }}
            QTabBar::tab:selected {{
                background: {self.accent_color.name()};
                color: black;
                font-weight: bold;
            }}
            QTabWidget::pane {{
                border: none;
                background: {self.card_color.name()};
            }}
        """)

        # Создание вкладок
        self.create_dashboard_tab()
        self.create_transaction_tab()
        self.create_budget_tab()
        self.create_stats_tab()
        self.create_goals_tab()
        self.create_regular_payments_tab()

        main_layout.addWidget(self.tabs)

        # Меню
        self.create_menu()

        # Обновление данных
        self.update_all_tabs()

    def setup_animations(self):
        # Анимация для главного окна
        self.opacity_effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(self.opacity_effect)
        self.fade_in = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_in.setDuration(1000)
        self.fade_in.setStartValue(0)
        self.fade_in.setEndValue(1)
        self.fade_in.setEasingCurve(QEasingCurve.InOutQuad)
        self.fade_in.start()

    def create_menu(self):
        menubar = self.menuBar()
        menubar.setStyleSheet(f"""
            QMenuBar {{
                background-color: {self.card_color.name()};
                color: {self.text_color.name()};
                border: none;
                padding: 5px;
            }}
            QMenuBar::item {{
                padding: 5px 10px;
                background-color: transparent;
                border-radius: 4px;
            }}
            QMenuBar::item:selected {{
                background-color: {self.accent_color.name()};
                color: black;
            }}
            QMenu {{
                background-color: {self.card_color.name()};
                border: 1px solid {self.accent_color.name()};
                padding: 5px;
            }}
            QMenu::item:selected {{
                background-color: {self.accent_color.name()};
                color: black;
            }}
        """)

        # Меню Файл
        file_menu = menubar.addMenu("Файл")

        export_action = QAction("Экспорт в CSV", self)
        export_action.triggered.connect(self.export_to_csv)
        file_menu.addAction(export_action)

        import_action = QAction("Импорт из CSV", self)
        import_action.triggered.connect(self.import_from_csv)
        file_menu.addAction(import_action)

        file_menu.addSeparator()

        exit_action = QAction("Выход", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Меню Сервис
        service_menu = menubar.addMenu("Сервис")

        balance_action = QAction("Показать баланс", self)
        balance_action.triggered.connect(self.show_balance_notification)
        service_menu.addAction(balance_action)

        add_income_action = QAction("Быстрый доход", self)
        add_income_action.triggered.connect(self.quick_add_income)
        service_menu.addAction(add_income_action)

        add_expense_action = QAction("Быстрый расход", self)
        add_expense_action.triggered.connect(self.quick_add_expense)
        service_menu.addAction(add_expense_action)

        # Меню Справка
        help_menu = menubar.addMenu("Справка")

        about_action = QAction("О программе", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

        tips_action = QAction("Советы по экономии", self)
        tips_action.triggered.connect(self.show_tips)
        help_menu.addAction(tips_action)

    def create_dashboard_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)
        tab.setStyleSheet(f"background-color: {self.card_color.name()}; padding: 20px;")

        # Прокручиваемая область
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none;")
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)

        # Карты с информацией
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(20)

        self.balance_card = BudgetCard("💰 Баланс", "0.00 ₽", "#6200EA")
        self.income_card = BudgetCard("📈 Доходы", "0.00 ₽", "#03DAC6")
        self.expense_card = BudgetCard("📉 Расходы", "0.00 ₽", "#CF6679")

        cards_layout.addWidget(self.balance_card)
        cards_layout.addWidget(self.income_card)
        cards_layout.addWidget(self.expense_card)
        scroll_layout.addLayout(cards_layout)

        # График доходов/расходов
        self.chart_canvas = FigureCanvas(plt.Figure(figsize=(10, 5)))
        self.chart_ax = self.chart_canvas.figure.subplots()
        self.chart_ax.set_facecolor("#1E1E2E")
        self.chart_canvas.setStyleSheet("background-color: transparent;")
        scroll_layout.addWidget(self.chart_canvas)

        # Круговые диаграммы по категориям
        self.pie_charts_layout = QHBoxLayout()

        self.income_pie_canvas = FigureCanvas(plt.Figure(figsize=(5, 5)))
        self.income_pie_ax = self.income_pie_canvas.figure.subplots()
        self.income_pie_ax.set_facecolor("#1E1E2E")
        self.income_pie_canvas.setStyleSheet("background-color: transparent;")
        self.income_pie_canvas.mpl_connect('button_press_event', self.on_pie_click)

        self.expense_pie_canvas = FigureCanvas(plt.Figure(figsize=(5, 5)))
        self.expense_pie_ax = self.expense_pie_canvas.figure.subplots()
        self.expense_pie_ax.set_facecolor("#1E1E2E")
        self.expense_pie_canvas.setStyleSheet("background-color: transparent;")
        self.expense_pie_canvas.mpl_connect('button_press_event', self.on_pie_click)

        self.pie_charts_layout.addWidget(self.income_pie_canvas)
        self.pie_charts_layout.addWidget(self.expense_pie_canvas)
        scroll_layout.addLayout(self.pie_charts_layout)

        # Кнопки быстрого доступа
        quick_actions_layout = QHBoxLayout()

        self.quick_income_btn = AnimatedButton("Добавить доход")
        self.quick_income_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.positive_color.name()};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #388E3C;
            }}
        """)
        self.quick_income_btn.clicked.connect(self.quick_add_income)

        self.quick_expense_btn = AnimatedButton("Добавить расход")
        self.quick_expense_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.negative_color.name()};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #D32F2F;
            }}
        """)
        self.quick_expense_btn.clicked.connect(self.quick_add_expense)

        quick_actions_layout.addWidget(self.quick_income_btn)
        quick_actions_layout.addWidget(self.quick_expense_btn)
        scroll_layout.addLayout(quick_actions_layout)

        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

        self.tabs.addTab(tab, "Главная")

    def on_pie_click(self, event):
        if event.inaxes == self.income_pie_ax:
            if hasattr(self, 'income_pie_patches'):
                for patch in self.income_pie_patches:
                    if patch.contains(event)[0]:
                        category = patch.label.get_text()
                        self.show_category_transactions("Доход", category)
                        break
        elif event.inaxes == self.expense_pie_ax:
            if hasattr(self, 'expense_pie_patches'):
                for patch in self.expense_pie_patches:
                    if patch.contains(event)[0]:
                        category = patch.label.get_text()
                        self.show_category_transactions("Расход", category)
                        break

    def show_category_transactions(self, trans_type, category):
        transactions = [t for t in self.transactions if t['type'] == trans_type and t['category'] == category]
        if not transactions:
            QMessageBox.information(self, "Транзакции", f"Нет транзакций в категории '{category}'")
            return

        msg = QMessageBox()
        msg.setWindowTitle(f"Транзакции: {category}")
        msg.setIcon(QMessageBox.Information)

        text = f"<h3>{category} ({trans_type})</h3><ul>"
        for t in sorted(transactions, key=lambda x: x['date'], reverse=True)[:10]:
            text += f"<li>{t['date']}: {t['amount']:.2f} ₽"
            if t['description']:
                text += f" - {t['description']}"
            text += "</li>"
        text += "</ul>"

        msg.setText(text)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()

    def create_transaction_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)
        tab.setStyleSheet(f"background-color: {self.card_color.name()}; padding: 20px;")

        # Форма добавления транзакции
        form_widget = QWidget()
        form_widget.setStyleSheet("background-color: #3A3A4A; border-radius: 10px; padding: 15px;")
        form_layout = QFormLayout(form_widget)

        self.transaction_type_combo = QComboBox()
        self.transaction_type_combo.addItems(["Доход", "Расход"])
        self.transaction_type_combo.currentTextChanged.connect(self.update_categories)
        self.transaction_type_combo.setStyleSheet("""
            QComboBox {
                background-color: #2A2A3A;
                color: white;
                border: 1px solid #03DAC6;
                border-radius: 5px;
                padding: 5px;
            }
        """)

        self.category_combo = QComboBox()
        self.category_combo.setStyleSheet("""
            QComboBox {
                background-color: #2A2A3A;
                color: white;
                border: 1px solid #03DAC6;
                border-radius: 5px;
                padding: 5px;
            }
        """)

        self.amount_input = QLineEdit()
        self.amount_input.setValidator(QDoubleValidator(0.00, 9999999.99, 2))
        self.amount_input.setStyleSheet("""
            QLineEdit {
                background-color: #2A2A3A;
                color: white;
                border: 1px solid #03DAC6;
                border-radius: 5px;
                padding: 5px;
            }
        """)

        self.date_edit = QDateEdit(calendarPopup=True)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setStyleSheet("""
            QDateEdit {
                background-color: #2A2A3A;
                color: white;
                border: 1px solid #03DAC6;
                border-radius: 5px;
                padding: 5px;
            }
            QCalendarWidget {
                background-color: #2A2A3A;
                color: white;
            }
        """)

        self.description_input = QLineEdit()
        self.description_input.setStyleSheet("""
            QLineEdit {
                background-color: #2A2A3A;
                color: white;
                border: 1px solid #03DAC6;
                border-radius: 5px;
                padding: 5px;
            }
        """)

        add_button = AnimatedButton("Добавить транзакцию")
        add_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.accent_color.name()};
                color: black;
                border: none;
                border-radius: 5px;
                padding: 10px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #00BFA5;
            }}
        """)
        add_button.clicked.connect(self.add_transaction)

        form_layout.addRow("Тип:", self.transaction_type_combo)
        form_layout.addRow("Категория:", self.category_combo)
        form_layout.addRow("Сумма:", self.amount_input)
        form_layout.addRow("Дата:", self.date_edit)
        form_layout.addRow("Описание:", self.description_input)
        form_layout.addRow(add_button)

        # Таблица транзакций
        self.transactions_table = QTableWidget()
        self.transactions_table.setColumnCount(5)
        self.transactions_table.setHorizontalHeaderLabels(["Тип", "Категория", "Сумма", "Дата", "Описание"])
        self.transactions_table.setStyleSheet("""
            QTableWidget {
                background-color: #2A2A3A;
                color: white;
                border: none;
                gridline-color: #3A3A4A;
            }
            QHeaderView::section {
                background-color: #6200EA;
                color: white;
                padding: 5px;
                border: none;
            }
            QTableWidget::item {
                padding: 5px;
            }
        """)
        self.transactions_table.verticalHeader().setVisible(False)
        self.update_transactions_table()

        layout.addWidget(form_widget)
        layout.addWidget(self.transactions_table)

        self.tabs.addTab(tab, "Транзакции")

    def update_categories(self):
        transaction_type = self.transaction_type_combo.currentText()
        categories = self.budget_categories.get(transaction_type, [])
        self.category_combo.clear()
        self.category_combo.addItems(categories)

        effect = QGraphicsOpacityEffect(self.category_combo)
        self.category_combo.setGraphicsEffect(effect)

        anim = QPropertyAnimation(effect, b"opacity")
        anim.setDuration(300)
        anim.setStartValue(0)
        anim.setEndValue(1)
        anim.setEasingCurve(QEasingCurve.InOutQuad)
        anim.start()

    def add_transaction(self):
        category = self.category_combo.currentText()
        try:
            amount = float(self.amount_input.text().replace(',', '.'))
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, введите корректную сумму")
            return

        date = self.date_edit.date().toString("yyyy-MM-dd")
        description = self.description_input.text()
        transaction_type = self.transaction_type_combo.currentText()

        transaction = {
            "type": transaction_type,
            "category": category,
            "amount": amount,
            "date": date,
            "description": description
        }

        self.transactions.append(transaction)
        self.save_data()
        self.update_transactions_table()
        self.update_dashboard()

        self.show_transaction_added_animation(transaction_type)

        self.amount_input.clear()
        self.description_input.clear()
        self.date_edit.setDate(QDate.currentDate())

    def show_transaction_added_animation(self, trans_type):
        notification = QLabel(self)
        notification.setText(f"Транзакция ({trans_type}) добавлена!")
        notification.setAlignment(Qt.AlignCenter)
        notification.setStyleSheet(f"""
            QLabel {{
                background-color: {self.accent_color.name()};
                color: black;
                border-radius: 10px;
                padding: 10px;
                font-weight: bold;
            }}
        """)
        notification.setFixedSize(200, 50)
        notification.move(self.width() - 220, 50)
        notification.show()

        effect = QGraphicsOpacityEffect(notification)
        notification.setGraphicsEffect(effect)

        anim_group = QSequentialAnimationGroup()

        fade_in = QPropertyAnimation(effect, b"opacity")
        fade_in.setDuration(300)
        fade_in.setStartValue(0)
        fade_in.setEndValue(1)

        delay = QPauseAnimation(1500)

        fade_out = QPropertyAnimation(effect, b"opacity")
        fade_out.setDuration(300)
        fade_out.setStartValue(1)
        fade_out.setEndValue(0)

        anim_group.addAnimation(fade_in)
        anim_group.addAnimation(delay)
        anim_group.addAnimation(fade_out)

        anim_group.finished.connect(notification.deleteLater)
        anim_group.start()

    def update_transactions_table(self):
        self.transactions_table.setRowCount(len(self.transactions))

        for row, transaction in enumerate(self.transactions):
            type_item = QTableWidgetItem(transaction["type"])
            category_item = QTableWidgetItem(transaction["category"])
            amount_item = QTableWidgetItem(f"{transaction['amount']:.2f}")
            date_item = QTableWidgetItem(transaction["date"])
            desc_item = QTableWidgetItem(transaction["description"])

            if transaction["type"] == "Доход":
                amount_item.setForeground(QColor("#03DAC6"))
            else:
                amount_item.setForeground(QColor("#CF6679"))

            self.transactions_table.setItem(row, 0, type_item)
            self.transactions_table.setItem(row, 1, category_item)
            self.transactions_table.setItem(row, 2, amount_item)
            self.transactions_table.setItem(row, 3, date_item)
            self.transactions_table.setItem(row, 4, desc_item)

        self.transactions_table.resizeColumnsToContents()

        effect = QGraphicsOpacityEffect(self.transactions_table)
        self.transactions_table.setGraphicsEffect(effect)

        anim = QPropertyAnimation(effect, b"opacity")
        anim.setDuration(500)
        anim.setStartValue(0)
        anim.setEndValue(1)
        anim.setEasingCurve(QEasingCurve.InOutQuad)
        anim.start()

    def create_budget_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)
        tab.setStyleSheet(f"background-color: {self.card_color.name()}; padding: 20px;")

        title = QLabel("Управление бюджетом")
        title.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #03DAC6;
            padding-bottom: 10px;
            border-bottom: 1px solid #03DAC6;
        """)
        layout.addWidget(title)

        form_widget = QWidget()
        form_widget.setStyleSheet("background-color: #3A3A4A; border-radius: 10px; padding: 15px;")
        form_layout = QFormLayout(form_widget)

        self.budget_category_combo = QComboBox()
        self.budget_category_combo.addItems(self.budget_categories["Расход"])
        self.budget_category_combo.setStyleSheet("""
            QComboBox {
                background-color: #2A2A3A;
                color: white;
                border: 1px solid #03DAC6;
                border-radius: 5px;
                padding: 5px;
            }
        """)

        self.budget_limit_input = QLineEdit()
        self.budget_limit_input.setValidator(QDoubleValidator(0.00, 9999999.99, 2))
        self.budget_limit_input.setStyleSheet("""
            QLineEdit {
                background-color: #2A2A3A;
                color: white;
                border: 1px solid #03DAC6;
                border-radius: 5px;
                padding: 5px;
            }
        """)

        set_budget_button = AnimatedButton("Установить лимит")
        set_budget_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.accent_color.name()};
                color: black;
                border: none;
                border-radius: 5px;
                padding: 10px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #00BFA5;
            }}
        """)
        set_budget_button.clicked.connect(self.set_budget_limit)

        form_layout.addRow("Категория расходов:", self.budget_category_combo)
        form_layout.addRow("Лимит:", self.budget_limit_input)
        form_layout.addRow(set_budget_button)

        self.budget_limits_table = QTableWidget()
        self.budget_limits_table.setColumnCount(3)
        self.budget_limits_table.setHorizontalHeaderLabels(["Категория", "Лимит", "Использовано"])
        self.budget_limits_table.setStyleSheet("""
            QTableWidget {
                background-color: #2A2A3A;
                color: white;
                border: none;
                gridline-color: #3A3A4A;
            }
            QHeaderView::section {
                background-color: #6200EA;
                color: white;
                padding: 5px;
                border: none;
            }
            QTableWidget::item {
                padding: 5px;
            }
        """)
        self.budget_limits_table.verticalHeader().setVisible(False)
        self.update_budget_limits_table()

        layout.addWidget(form_widget)
        layout.addWidget(self.budget_limits_table)

        self.tabs.addTab(tab, "Бюджет")

    def set_budget_limit(self):
        category = self.budget_category_combo.currentText()
        try:
            limit = float(self.budget_limit_input.text().replace(',', '.'))
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, введите корректную сумму")
            return

        self.budget_limits[category] = limit
        self.save_data()
        self.update_budget_limits_table()
        self.show_notification(f"Лимит для '{category}' установлен: {limit:.2f} ₽")

    def update_budget_limits_table(self):
        self.budget_limits_table.setRowCount(len(self.budget_limits))

        for row, (category, limit) in enumerate(self.budget_limits.items()):
            spent = sum(t['amount'] for t in self.transactions
                        if t['type'] == 'Расход' and t['category'] == category)

            category_item = QTableWidgetItem(category)
            limit_item = QTableWidgetItem(f"{limit:.2f} ₽")
            spent_item = QTableWidgetItem(f"{spent:.2f} ₽")

            if spent > limit:
                spent_item.setForeground(QColor("#F44336"))

            self.budget_limits_table.setItem(row, 0, category_item)
            self.budget_limits_table.setItem(row, 1, limit_item)
            self.budget_limits_table.setItem(row, 2, spent_item)

        self.budget_limits_table.resizeColumnsToContents()

    def create_stats_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)
        tab.setStyleSheet(f"background-color: {self.card_color.name()}; padding: 20px;")

        title = QLabel("Статистика")
        title.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #03DAC6;
            padding-bottom: 10px;
            border-bottom: 1px solid #03DAC6;
        """)
        layout.addWidget(title)

        period_layout = QHBoxLayout()
        period_label = QLabel("Период:")
        period_label.setStyleSheet("font-size: 16px;")

        self.stats_period_combo = QComboBox()
        self.stats_period_combo.addItems(["За все время", "За месяц", "За год"])
        self.stats_period_combo.setCurrentText("За месяц")
        self.stats_period_combo.setStyleSheet("""
            QComboBox {
                background-color: #2A2A3A;
                color: white;
                border: 1px solid #03DAC6;
                border-radius: 5px;
                padding: 5px;
            }
        """)
        self.stats_period_combo.currentTextChanged.connect(self.update_stats)

        period_layout.addWidget(period_label)
        period_layout.addWidget(self.stats_period_combo)
        period_layout.addStretch()
        layout.addLayout(period_layout)

        self.stats_canvas = FigureCanvas(plt.Figure(figsize=(10, 8)))
        self.stats_ax = self.stats_canvas.figure.subplots(2, 1)
        self.stats_canvas.setStyleSheet("background-color: transparent;")
        layout.addWidget(self.stats_canvas)

        self.tabs.addTab(tab, "Статистика")

    def update_stats(self):
        period = self.stats_period_combo.currentText()
        now = datetime.now()

        if period == "За месяц":
            start_date = now.replace(day=1)
            transactions = [t for t in self.transactions
                            if datetime.strptime(t['date'], "%Y-%m-%d") >= start_date]
        elif period == "За год":
            start_date = now.replace(month=1, day=1)
            transactions = [t for t in self.transactions
                            if datetime.strptime(t['date'], "%Y-%m-%d") >= start_date]
        else:
            transactions = self.transactions

        for ax in self.stats_ax:
            ax.clear()

        income_by_day = defaultdict(float)
        expense_by_day = defaultdict(float)

        for t in transactions:
            date = datetime.strptime(t['date'], "%Y-%m-%d")
            if t['type'] == 'Доход':
                income_by_day[date] += t['amount']
            else:
                expense_by_day[date] += t['amount']

        dates = sorted(set(income_by_day.keys()).union(set(expense_by_day.keys())))
        income_values = [income_by_day.get(d, 0) for d in dates]
        expense_values = [expense_by_day.get(d, 0) for d in dates]

        if dates:
            self.stats_ax[0].plot(dates, income_values, label='Доходы', color='#03DAC6')
            self.stats_ax[0].plot(dates, expense_values, label='Расходы', color='#CF6679')
            self.stats_ax[0].set_title('Доходы и расходы по дням')
            self.stats_ax[0].legend()
            self.stats_ax[0].grid(True, alpha=0.3)
            self.stats_ax[0].set_facecolor("#1E1E2E")
            self.stats_ax[0].tick_params(axis='x', colors='white')
            self.stats_ax[0].tick_params(axis='y', colors='white')
            self.stats_ax[0].spines['bottom'].set_color('white')
            self.stats_ax[0].spines['left'].set_color('white')
            self.stats_ax[0].spines['top'].set_visible(False)
            self.stats_ax[0].spines['right'].set_visible(False)
            self.stats_ax[0].figure.set_facecolor("#1E1E2E")

            income_categories = defaultdict(float)
            expense_categories = defaultdict(float)

            for t in transactions:
                if t['type'] == 'Доход':
                    income_categories[t['category']] += t['amount']
                else:
                    expense_categories[t['category']] += t['amount']

            if income_categories:
                self.stats_ax[1].pie(
                    income_categories.values(),
                    labels=income_categories.keys(),
                    autopct='%1.1f%%',
                    colors=plt.cm.Pastel1.colors,
                    wedgeprops={'width': 0.4}
                )
                self.stats_ax[1].set_title('Доходы по категориям')

            self.stats_canvas.draw()

    def create_goals_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)
        tab.setStyleSheet(f"background-color: {self.card_color.name()}; padding: 20px;")

        title = QLabel("Финансовые цели")
        title.setStyleSheet("""
                font-size: 24px;
                font-weight: bold;
                color: #03DAC6;
                padding-bottom: 10px;
                border-bottom: 1px solid #03DAC6;
            """)
        layout.addWidget(title)

        # Форма добавления цели
        form_widget = QWidget()
        form_widget.setStyleSheet("background-color: #3A3A4A; border-radius: 10px; padding: 15px;")
        form_layout = QFormLayout(form_widget)

        self.goal_name_input = QLineEdit()
        self.goal_name_input.setStyleSheet("""
                QLineEdit {
                    background-color: #2A2A3A;
                    color: white;
                    border: 1px solid #03DAC6;
                    border-radius: 5px;
                    padding: 5px;
                }
            """)

        self.goal_amount_input = QLineEdit()
        self.goal_amount_input.setValidator(QDoubleValidator(0.00, 9999999.99, 2))
        self.goal_amount_input.setStyleSheet("""
                QLineEdit {
                    background-color: #2A2A3A;
                    color: white;
                    border: 1px solid #03DAC6;
                    border-radius: 5px;
                    padding: 5px;
                }
            """)

        self.goal_date_edit = QDateEdit(calendarPopup=True)
        self.goal_date_edit.setDate(QDate.currentDate().addMonths(1))
        self.goal_date_edit.setStyleSheet("""
                QDateEdit {
                    background-color: #2A2A3A;
                    color: white;
                    border: 1px solid #03DAC6;
                    border-radius: 5px;
                    padding: 5px;
                }
            """)

        add_goal_button = AnimatedButton("Добавить цель")
        add_goal_button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {self.accent_color.name()};
                    color: black;
                    border: none;
                    border-radius: 5px;
                    padding: 10px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: #00BFA5;
                }}
            """)
        add_goal_button.clicked.connect(self.add_saving_goal)

        form_layout.addRow("Название цели:", self.goal_name_input)
        form_layout.addRow("Сумма:", self.goal_amount_input)
        form_layout.addRow("Дата достижения:", self.goal_date_edit)
        form_layout.addRow(add_goal_button)

        # Таблица целей
        self.goals_table = QTableWidget()
        self.goals_table.setColumnCount(4)
        self.goals_table.setHorizontalHeaderLabels(["Цель", "Сумма", "Дата", "Прогресс"])
        self.goals_table.setStyleSheet("""
                QTableWidget {
                    background-color: #2A2A3A;
                    color: white;
                    border: none;
                    gridline-color: #3A3A4A;
                }
                QHeaderView::section {
                    background-color: #6200EA;
                    color: white;
                    padding: 5px;
                    border: none;
                }
                QTableWidget::item {
                    padding: 5px;
                }
            """)
        self.goals_table.verticalHeader().setVisible(False)
        self.update_goals_table()

        layout.addWidget(form_widget)
        layout.addWidget(self.goals_table)

        self.tabs.addTab(tab, "Цели")

    def add_saving_goal(self):
        name = self.goal_name_input.text()
        try:
            amount = float(self.goal_amount_input.text().replace(',', '.'))
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, введите корректную сумму")
            return

        date = self.goal_date_edit.date().toString("yyyy-MM-dd")

        goal = {
            "name": name,
            "amount": amount,
            "target_date": date,
            "saved": 0.0
        }

        self.saving_goals.append(goal)
        self.save_data()
        self.update_goals_table()

        self.goal_name_input.clear()
        self.goal_amount_input.clear()
        self.goal_date_edit.setDate(QDate.currentDate().addMonths(1))
        self.show_notification(f"Цель '{name}' добавлена!")

    def update_goals_table(self):
        self.goals_table.setRowCount(len(self.saving_goals))

        for row, goal in enumerate(self.saving_goals):
            name_item = QTableWidgetItem(goal["name"])
            amount_item = QTableWidgetItem(f"{goal['amount']:.2f} ₽")
            date_item = QTableWidgetItem(goal["target_date"])

            progress = (goal["saved"] / goal["amount"]) * 100 if goal["amount"] > 0 else 0
            progress_item = QTableWidgetItem(f"{progress:.1f}%")

            if progress >= 100:
                progress_item.setForeground(QColor("#4CAF50"))
            elif progress >= 75:
                progress_item.setForeground(QColor("#FFC107"))
            else:
                progress_item.setForeground(QColor("#F44336"))

            self.goals_table.setItem(row, 0, name_item)
            self.goals_table.setItem(row, 1, amount_item)
            self.goals_table.setItem(row, 2, date_item)
            self.goals_table.setItem(row, 3, progress_item)

        self.goals_table.resizeColumnsToContents()

    def create_regular_payments_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)
        tab.setStyleSheet(f"background-color: {self.card_color.name()}; padding: 20px;")

        title = QLabel("Регулярные платежи")
        title.setStyleSheet("""
                font-size: 24px;
                font-weight: bold;
                color: #03DAC6;
                padding-bottom: 10px;
                border-bottom: 1px solid #03DAC6;
            """)
        layout.addWidget(title)

        # Форма добавления платежа
        form_widget = QWidget()
        form_widget.setStyleSheet("background-color: #3A3A4A; border-radius: 10px; padding: 15px;")
        form_layout = QFormLayout(form_widget)

        self.payment_name_input = QLineEdit()
        self.payment_name_input.setStyleSheet("""
                QLineEdit {
                    background-color: #2A2A3A;
                    color: white;
                    border: 1px solid #03DAC6;
                    border-radius: 5px;
                    padding: 5px;
                }
            """)

        self.payment_amount_input = QLineEdit()
        self.payment_amount_input.setValidator(QDoubleValidator(0.00, 9999999.99, 2))
        self.payment_amount_input.setStyleSheet("""
                QLineEdit {
                    background-color: #2A2A3A;
                    color: white;
                    border: 1px solid #03DAC6;
                    border-radius: 5px;
                    padding: 5px;
                }
            """)

        self.payment_category_combo = QComboBox()
        self.payment_category_combo.addItems(self.budget_categories["Расход"])
        self.payment_category_combo.setStyleSheet("""
                QComboBox {
                    background-color: #2A2A3A;
                    color: white;
                    border: 1px solid #03DAC6;
                    border-radius: 5px;
                    padding: 5px;
                }
            """)

        self.payment_frequency_combo = QComboBox()
        self.payment_frequency_combo.addItems(["Ежемесячно", "Ежеквартально", "Ежегодно"])
        self.payment_frequency_combo.setStyleSheet("""
                QComboBox {
                    background-color: #2A2A3A;
                    color: white;
                    border: 1px solid #03DAC6;
                    border-radius: 5px;
                    padding: 5px;
                }
            """)

        add_payment_button = AnimatedButton("Добавить платеж")
        add_payment_button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {self.accent_color.name()};
                    color: black;
                    border: none;
                    border-radius: 5px;
                    padding: 10px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: #00BFA5;
                }}
            """)
        add_payment_button.clicked.connect(self.add_regular_payment)

        form_layout.addRow("Название платежа:", self.payment_name_input)
        form_layout.addRow("Сумма:", self.payment_amount_input)
        form_layout.addRow("Категория:", self.payment_category_combo)
        form_layout.addRow("Периодичность:", self.payment_frequency_combo)
        form_layout.addRow(add_payment_button)

        # Таблица платежей
        self.payments_table = QTableWidget()
        self.payments_table.setColumnCount(4)
        self.payments_table.setHorizontalHeaderLabels(["Платеж", "Сумма", "Категория", "Периодичность"])
        self.payments_table.setStyleSheet("""
                QTableWidget {
                    background-color: #2A2A3A;
                    color: white;
                    border: none;
                    gridline-color: #3A3A4A;
                }
                QHeaderView::section {
                    background-color: #6200EA;
                    color: white;
                    padding: 5px;
                    border: none;
                }
                QTableWidget::item {
                    padding: 5px;
                }
            """)
        self.payments_table.verticalHeader().setVisible(False)
        self.update_payments_table()

        layout.addWidget(form_widget)
        layout.addWidget(self.payments_table)

        self.tabs.addTab(tab, "Регулярные платежи")

    def add_regular_payment(self):
        name = self.payment_name_input.text()
        try:
            amount = float(self.payment_amount_input.text().replace(',', '.'))
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, введите корректную сумму")
            return

        category = self.payment_category_combo.currentText()
        frequency = self.payment_frequency_combo.currentText()

        payment = {
            "name": name,
            "amount": amount,
            "category": category,
            "frequency": frequency,
            "last_paid": None
        }

        self.regular_payments.append(payment)
        self.save_data()
        self.update_payments_table()

        self.payment_name_input.clear()
        self.payment_amount_input.clear()
        self.show_notification(f"Платеж '{name}' добавлен!")

    def update_payments_table(self):
        self.payments_table.setRowCount(len(self.regular_payments))

        for row, payment in enumerate(self.regular_payments):
            name_item = QTableWidgetItem(payment["name"])
            amount_item = QTableWidgetItem(f"{payment['amount']:.2f} ₽")
            category_item = QTableWidgetItem(payment["category"])
            frequency_item = QTableWidgetItem(payment["frequency"])

            self.payments_table.setItem(row, 0, name_item)
            self.payments_table.setItem(row, 1, amount_item)
            self.payments_table.setItem(row, 2, category_item)
            self.payments_table.setItem(row, 3, frequency_item)

        self.payments_table.resizeColumnsToContents()

    def update_all_tabs(self):
        self.update_dashboard()
        self.update_transactions_table()
        self.update_budget_limits_table()
        self.update_stats()
        self.update_goals_table()
        self.update_payments_table()

    def update_dashboard(self):
        total_income = sum(t["amount"] for t in self.transactions if t["type"] == "Доход")
        total_expense = sum(t["amount"] for t in self.transactions if t["type"] == "Расход")
        balance = total_income - total_expense

        self.balance_card.value_label.setText(f"{balance:.2f} ₽")
        self.income_card.value_label.setText(f"{total_income:.2f} ₽")
        self.expense_card.value_label.setText(f"{total_expense:.2f} ₽")

        self.update_chart()
        self.update_pie_charts()

    def update_chart(self):
        months = defaultdict(lambda: {"income": 0, "expense": 0})

        for t in self.transactions:
            date = datetime.strptime(t["date"], "%Y-%m-%d")
            month_key = date.strftime("%Y-%m")

            if t["type"] == "Доход":
                months[month_key]["income"] += t["amount"]
            else:
                months[month_key]["expense"] += t["amount"]

        sorted_months = sorted(months.items())
        month_labels = [m[0] for m in sorted_months]
        income_values = [m[1]["income"] for m in sorted_months]
        expense_values = [m[1]["expense"] for m in sorted_months]

        self.chart_ax.clear()

        if month_labels:
            x = range(len(month_labels))
            width = 0.35
            self.chart_ax.bar(x, income_values, width, label='Доходы', color='#03DAC6')
            self.chart_ax.bar([p + width for p in x], expense_values, width, label='Расходы', color='#CF6679')

            self.chart_ax.set_xticks([p + width / 2 for p in x])
            self.chart_ax.set_xticklabels(month_labels, rotation=45)
            self.chart_ax.legend()
            self.chart_ax.set_title('Доходы и расходы по месяцам')
            self.chart_ax.grid(True, alpha=0.3)

        self.chart_ax.set_facecolor("#1E1E2E")
        self.chart_ax.tick_params(axis='x', colors='white')
        self.chart_ax.tick_params(axis='y', colors='white')
        self.chart_ax.spines['bottom'].set_color('white')
        self.chart_ax.spines['left'].set_color('white')
        self.chart_ax.spines['top'].set_visible(False)
        self.chart_ax.spines['right'].set_visible(False)
        self.chart_ax.figure.set_facecolor("#1E1E2E")
        self.chart_canvas.draw()

    def update_pie_charts(self):
        income_categories = defaultdict(float)
        for t in self.transactions:
            if t["type"] == "Доход":
                income_categories[t["category"]] += t["amount"]

        self.income_pie_ax.clear()
        if income_categories:
            self.income_pie_patches, _, _ = self.income_pie_ax.pie(
                income_categories.values(),
                labels=income_categories.keys(),
                autopct='%1.1f%%',
                colors=plt.cm.Pastel1.colors,
                wedgeprops={'linewidth': 1, 'edgecolor': 'white'},
                textprops={'color': 'white'}
            )
            self.income_pie_ax.set_title('Доходы по категориям', color='white')

        self.income_pie_ax.set_facecolor("#1E1E2E")
        self.income_pie_canvas.draw()

        expense_categories = defaultdict(float)
        for t in self.transactions:
            if t["type"] == "Расход":
                expense_categories[t["category"]] += t["amount"]

        self.expense_pie_ax.clear()
        if expense_categories:
            self.expense_pie_patches, _, _ = self.expense_pie_ax.pie(
                expense_categories.values(),
                labels=expense_categories.keys(),
                autopct='%1.1f%%',
                colors=plt.cm.Pastel2.colors,
                wedgeprops={'linewidth': 1, 'edgecolor': 'white'},
                textprops={'color': 'white'}
            )
            self.expense_pie_ax.set_title('Расходы по категориям', color='white')

        self.expense_pie_ax.set_facecolor("#1E1E2E")
        self.expense_pie_canvas.draw()

    def calculate_balance(self):
        total_income = sum(t["amount"] for t in self.transactions if t["type"] == "Доход")
        total_expense = sum(t["amount"] for t in self.transactions if t["type"] == "Расход")
        return total_income - total_expense

    def show_balance_notification(self):
        balance = self.calculate_balance()
        message = f"Ваш текущий баланс: {balance:.2f} ₽"

        if balance > 0:
            icon = QMessageBox.Information
        else:
            icon = QMessageBox.Warning

        QMessageBox(icon, "Баланс", message, QMessageBox.Ok, self).exec_()

    def quick_add_income(self):
        category, ok = QInputDialog.getItem(
            self, "Быстрый доход", "Выберите категорию:",
            self.budget_categories["Доход"], 0, False
        )

        if not ok:
            return

        amount, ok = QInputDialog.getDouble(
            self, "Быстрый доход", "Введите сумму:",
            0, 0, 10000000, 2
        )

        if ok:
            transaction = {
                "type": "Доход",
                "category": category,
                "amount": amount,
                "date": QDate.currentDate().toString("yyyy-MM-dd"),
                "description": "Быстрый доход"
            }
            self.transactions.append(transaction)
            self.save_data()
            self.update_all_tabs()
            self.show_notification(f"Доход добавлен: {amount:.2f} ₽")

    def quick_add_expense(self):
        category, ok = QInputDialog.getItem(
            self, "Быстрый расход", "Выберите категорию:",
            self.budget_categories["Расход"], 0, False
        )

        if not ok:
            return

        amount, ok = QInputDialog.getDouble(
            self, "Быстрый расход", "Введите сумму:",
            0, 0, 10000000, 2
        )

        if ok:
            transaction = {
                "type": "Расход",
                "category": category,
                "amount": amount,
                "date": QDate.currentDate().toString("yyyy-MM-dd"),
                "description": "Быстрый расход"
            }
            self.transactions.append(transaction)
            self.save_data()
            self.update_all_tabs()
            self.show_notification(f"Расход добавлен: {amount:.2f} ₽")

    def show_notification(self, message):
        notification = QLabel(self)
        notification.setText(message)
        notification.setAlignment(Qt.AlignCenter)
        notification.setStyleSheet(f"""
                QLabel {{
                    background-color: {self.accent_color.name()};
                    color: black;
                    border-radius: 10px;
                    padding: 10px;
                    font-weight: bold;
                }}
            """)
        notification.setFixedSize(300, 50)
        notification.move(self.width() - 320, 50)
        notification.show()

        effect = QGraphicsOpacityEffect(notification)
        notification.setGraphicsEffect(effect)

        anim_group = QSequentialAnimationGroup()

        fade_in = QPropertyAnimation(effect, b"opacity")
        fade_in.setDuration(300)
        fade_in.setStartValue(0)
        fade_in.setEndValue(1)

        delay = QPauseAnimation(1500)

        fade_out = QPropertyAnimation(effect, b"opacity")
        fade_out.setDuration(300)
        fade_out.setStartValue(1)
        fade_out.setEndValue(0)

        anim_group.addAnimation(fade_in)
        anim_group.addAnimation(delay)
        anim_group.addAnimation(fade_out)

        anim_group.finished.connect(notification.deleteLater)
        anim_group.start()

    def export_to_csv(self):
        try:
            filename = f"finance_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("Дата;Тип;Категория;Сумма;Описание\n")
                for transaction in self.transactions:
                    line = f"{transaction['date']};{transaction['type']};{transaction['category']};"
                    line += f"{transaction['amount']:.2f};{transaction['description']}\n"
                    f.write(line)
            self.show_notification(f"Данные экспортированы в {filename}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось экспортировать данные: {str(e)}")

    def import_from_csv(self):
        try:
            filename, _ = QFileDialog.getOpenFileName(
                self, "Импорт из CSV", "", "CSV Files (*.csv)"
            )

            if not filename:
                return

            with open(filename, 'r', encoding='utf-8') as f:
                next(f)

                imported = 0
                for line in f:
                    parts = line.strip().split(';')
                    if len(parts) < 5:
                        continue

                    date, trans_type, category, amount, desc = parts[:5]

                    try:
                        amount = float(amount.replace(',', '.'))
                    except ValueError:
                        continue

                    transaction = {
                        "type": trans_type,
                        "category": category,
                        "amount": amount,
                        "date": date,
                        "description": desc
                    }
                    self.transactions.append(transaction)
                    imported += 1

            self.save_data()
            self.update_all_tabs()
            self.show_notification(f"Импортировано {imported} транзакций")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось импортировать данные: {str(e)}")

    def show_about(self):
        about_text = """
                <h2>Умный Бюджет</h2>
                <p>Версия 2.0</p>
                <p>Приложение для управления личными финансами.</p>
                <p>Позволяет отслеживать доходы и расходы, устанавливать бюджетные лимиты и достигать финансовых целей.</p>
                <p><b>Функции:</b></p>
                <ul>
                    <li>Учет доходов и расходов</li>
                    <li>Установка лимитов по категориям</li>
                    <li>Финансовые цели</li>
                    <li>Регулярные платежи</li>
                    <li>Визуализация статистики</li>
                    <li>Экспорт/импорт данных</li>
                </ul>
                """
        QMessageBox.about(self, "О программе", about_text)

    def show_tips(self):
        tips = [
            "Откладывайте минимум 10% от каждого дохода",
            "Планируйте крупные покупки заранее",
            "Используйте правило 50/30/20: 50% на нужды, 30% на желания, 20% на сбережения",
            "Регулярно анализируйте свои расходы",
            "Автоматизируйте сбережения и платежи",
            "Избегайте импульсных покупок",
            "Сравнивайте цены перед покупкой",
            "Используйте кэшбек и скидки"
        ]

        tip = random.choice(tips)
        QMessageBox.information(self, "Совет по экономии", tip)

    def load_data(self):
        try:
            if os.path.exists("data.json"):
                with open("data.json", "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.transactions = data.get("transactions", [])
                    self.budget_limits = data.get("budget_limits", {})
                    self.saving_goals = data.get("saving_goals", [])
                    self.regular_payments = data.get("regular_payments", [])
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось загрузить данные: {str(e)}")

    def save_data(self):
        try:
            data = {
                "transactions": self.transactions,
                "budget_limits": self.budget_limits,
                "saving_goals": self.saving_goals,
                "regular_payments": self.regular_payments
            }
            with open("data.json", "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось сохранить данные: {str(e)}")

if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Устанавливаем стиль приложения
    app.setStyle("Fusion")

    palette = app.palette()
    palette.setColor(palette.Window, QColor("#1E1E2E"))
    palette.setColor(palette.WindowText, QColor("#E4E6EB"))
    palette.setColor(palette.Base, QColor("#2A2A3A"))
    palette.setColor(palette.AlternateBase, QColor("#3A3A4A"))
    palette.setColor(palette.ToolTipBase, QColor("#6200EA"))
    palette.setColor(palette.ToolTipText, Qt.white)
    palette.setColor(palette.Text, QColor("#E4E6EB"))
    palette.setColor(palette.Button, QColor("#2A2A3A"))
    palette.setColor(palette.ButtonText, QColor("#E4E6EB"))
    palette.setColor(palette.BrightText, Qt.red)
    palette.setColor(palette.Highlight, QColor("#6200EA"))
    palette.setColor(palette.HighlightedText, Qt.white)
    app.setPalette(palette)

    window = SmartBudgetApp()
    window.show()
    sys.exit(app.exec_())