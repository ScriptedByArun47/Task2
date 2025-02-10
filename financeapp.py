from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.scrollview import MDScrollView
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy_garden.matplotlib.backend_kivyagg import FigureCanvasKivyAgg
from kivymd.uix.list import OneLineListItem

import sqlite3
import datetime
import matplotlib.pyplot as plt
from matplotlib.figure import Figure


class FinanceTrackerScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Database setup
        self.db_connection()

        # Main layout
        layout = MDBoxLayout(orientation="vertical", padding=20, spacing=10)

        # Title
        self.title_label = MDLabel(
            text="Finance Tracker",
            halign="center",
            font_style="H5",
            size_hint=(1, None),
            height=40,
            text_color=(26 / 255, 47 / 255, 86 / 255, 1)
        )
        layout.add_widget(self.title_label)

        # Input for amount
        self.amount_input = MDTextField(
            hint_text="Enter Amount",
            size_hint=(1, None),
            height=50
        )
        layout.add_widget(self.amount_input)

        # Dropdown for category
        self.category_menu_items = [
            {"text": cat, "viewclass": "OneLineListItem", "on_release": lambda x=cat: self.set_category(x)}
            for cat in ["Income", "Rent", "Food", "Entertainment", "Other"]
        ]

        self.category_menu = MDDropdownMenu(
            items=self.category_menu_items,
            width_mult=4
        )

        self.category_button = MDRaisedButton(
            text="Select Category",
            size_hint=(1, None),
            height=50
        )
        self.category_button.bind(on_release=self.category_menu_open)
        layout.add_widget(self.category_button)

        # Button to add transaction
        self.add_transaction_button = MDRaisedButton(
            text="Add Transaction",
            size_hint=(1, None),
            height=50,
            md_bg_color=(0, 0.5, 1, 1)
        )
        self.add_transaction_button.bind(on_release=self.add_transaction)
        layout.add_widget(self.add_transaction_button)

        # Clear history button
        self.clear_history_button = MDRaisedButton(
            text="Clear History",
            size_hint=(1, None),
            height=50,
            md_bg_color=(1, 0, 0, 1)
        )
        self.clear_history_button.bind(on_release=self.clear_history)
        layout.add_widget(self.clear_history_button)

        # Pie chart display
        self.pie_chart_layout = BoxLayout(size_hint=(1, None), height=300)
        layout.add_widget(self.pie_chart_layout)

        # Scrollable transaction list
        self.scroll_view = MDScrollView()
        self.transaction_list = MDBoxLayout(orientation="vertical", size_hint_y=None)
        self.transaction_list.bind(minimum_height=self.transaction_list.setter('height'))
        self.scroll_view.add_widget(self.transaction_list)
        layout.add_widget(self.scroll_view)

        self.add_widget(layout)

        # Initial data display
        self.display_transactions()
        self.update_pie_chart()

    def db_connection(self):
        self.conn = sqlite3.connect("finance.db")
        self.cursor = self.conn.cursor()
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY,
            amount REAL,
            category TEXT,
            date TEXT
        )""")
        self.conn.commit()

    def category_menu_open(self, instance):
        self.category_menu.caller = self.category_button
        self.category_menu.open()

    def set_category(self, category):
        self.category_button.text = category
        self.category_menu.dismiss()

    def add_transaction(self, instance):
        amount = self.amount_input.text.strip()
        category = self.category_button.text.strip()
        date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if not amount.replace(".", "", 1).isdigit() or float(amount) <= 0:
            print("Invalid amount. Enter a positive number.")
            return

        if category == "Select Category":
            print("Please select a valid category.")
            return

        try:
            self.cursor.execute(
                "INSERT INTO transactions (amount, category, date) VALUES (?, ?, ?)",
                (float(amount), category, date)
            )
            self.conn.commit()
            self.amount_input.text = ""
            self.category_button.text = "Select Category"
            self.display_transactions()
            self.update_pie_chart()
        except ValueError:
            print("Invalid amount. Enter a valid number.")

    def display_transactions(self):
        self.transaction_list.clear_widgets()
        self.cursor.execute("SELECT amount, category, date FROM transactions ORDER BY date DESC")
        transactions = self.cursor.fetchall()

        if not transactions:
            self.transaction_list.add_widget(MDLabel(text="No transactions yet.", halign="center"))
            return

        for amount, category, date in transactions:
            self.transaction_list.add_widget(
                MDLabel(text=f"{date} - {category}: ${amount:.2f}", theme_text_color="Primary", size_hint_y=None, height=30)
            )

    def update_pie_chart(self):
        self.cursor.execute("SELECT category, SUM(amount) FROM transactions GROUP BY category")
        data = self.cursor.fetchall()

        if not data:
            self.pie_chart_layout.clear_widgets()
            self.pie_chart_layout.add_widget(MDLabel(text="No data to display.", halign="center"))
            return

        categories, amounts = zip(*data)

        # Clear existing chart
        self.pie_chart_layout.clear_widgets()

        # Create a new pie chart figure
        fig = Figure(figsize=(4, 4))
        ax = fig.add_subplot(111)

        colors = plt.cm.Paired.colors  # Distinct color palette
        ax.pie(amounts, labels=categories, autopct='%1.1f%%', startangle=140, colors=colors)
        ax.axis('equal')
        ax.legend(categories, loc="upper right")

        # Add chart to the layout
        chart = FigureCanvasKivyAgg(fig)
        self.pie_chart_layout.add_widget(chart)

    def clear_history(self, instance):
        self.cursor.execute("DELETE FROM transactions")
        self.conn.commit()
        self.display_transactions()
        self.update_pie_chart()


class FinanceApp(MDApp):
    def build(self):
        self.title = "Finance Tracker"
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.theme_style = "Light"
        sm = ScreenManager()
        sm.add_widget(FinanceTrackerScreen(name="finance"))
        return sm


if __name__ == "__main__":
    FinanceApp().run()