import sys
import json
import os
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap, QIcon
from mcstatus import JavaServer
import requests
from io import BytesIO

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QLineEdit, QPushButton, QLabel, QListWidget, QTabWidget, 
                            QComboBox, QScrollArea, QMessageBox)

class MinecraftServerMonitor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Minecraft Server Monitor")
        self.setMinimumSize(800, 600)
        
        # Initialize settings
        self.settings = self.load_settings()
        self.servers = self.load_servers()
        
        # Setup UI
        self.setup_ui()
        
        # Setup auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_all_servers)
        self.refresh_timer.start(30000)  # Refresh every 30 seconds

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Title
        title_label = QLabel("Minecraft Server Monitor")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; margin: 10px;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)

        # Tab widget
        tab_widget = QTabWidget()
        main_layout.addWidget(tab_widget)

        # Servers tab
        servers_tab = QWidget()
        servers_layout = QHBoxLayout(servers_tab)
        
        # Server list
        self.server_list = QListWidget()
        self.server_list.setMaximumWidth(200)
        self.server_list.itemClicked.connect(self.show_server_details)
        servers_layout.addWidget(self.server_list)

        # Server details
        self.server_details = QScrollArea()
        self.server_details.setWidgetResizable(True)
        self.server_details_widget = QWidget()
        self.server_details_layout = QVBoxLayout(self.server_details_widget)
        self.server_details.setWidget(self.server_details_widget)
        servers_layout.addWidget(self.server_details)

        # Settings tab
        settings_tab = QWidget()
        settings_layout = QVBoxLayout(settings_tab)

        # Theme selector
        theme_layout = QHBoxLayout()
        theme_label = QLabel("Тема:")
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Системная", "QT6 Dark"])
        self.theme_combo.currentTextChanged.connect(self.change_theme)
        theme_layout.addWidget(theme_label)
        theme_layout.addWidget(self.theme_combo)
        settings_layout.addLayout(theme_layout)
        settings_layout.addStretch()

        # Add tabs
        tab_widget.addTab(servers_tab, "Серверы")
        tab_widget.addTab(settings_tab, "Настройки")

        # Add server controls
        server_controls = QHBoxLayout()
        self.server_input = QLineEdit()
        self.server_input.setPlaceholderText("Введите IP сервера")
        add_button = QPushButton("Добавить сервер")
        add_button.clicked.connect(self.add_server)
        server_controls.addWidget(self.server_input)
        server_controls.addWidget(add_button)
        main_layout.addLayout(server_controls)

        # Load saved servers
        self.refresh_server_list()

    def add_server(self):
        server_address = self.server_input.text().strip()
        if server_address:
            if server_address not in self.servers:
                self.servers[server_address] = {"name": server_address}
                self.save_servers()
                self.refresh_server_list()
                self.server_input.clear()

    def refresh_server_list(self):
        self.server_list.clear()
        for server in self.servers:
            self.server_list.addItem(server)
        self.refresh_all_servers()

    def show_server_details(self, item):
        # Clear previous details
        for i in reversed(range(self.server_details_layout.count())): 
            self.server_details_layout.itemAt(i).widget().setParent(None)

        server_address = item.text()
        try:
            server = JavaServer.lookup(server_address)
            status = server.status()
            
            # Server info
            info_label = QLabel(f"Сервер: {server_address}")
            info_label.setStyleSheet("font-weight: bold;")
            self.server_details_layout.addWidget(info_label)
            
            # Status
            self.server_details_layout.addWidget(QLabel(f"Статус в сети: Online"))
            self.server_details_layout.addWidget(QLabel(f"Версия (ядро сервера): {status.version.name}"))
            self.server_details_layout.addWidget(QLabel(f"Игроки: {status.players.online}/{status.players.max}"))
            
            # Player list
            if status.players.sample:
                players_label = QLabel("Игроки на сервере:")
                players_label.setStyleSheet("font-weight: bold;")
                self.server_details_layout.addWidget(players_label)
                for player in status.players.sample:
                    self.server_details_layout.addWidget(QLabel(f"- {player.name}"))

            # Remove server button
            remove_button = QPushButton("Удалить сервер")
            remove_button.clicked.connect(lambda: self.remove_server(server_address))
            self.server_details_layout.addWidget(remove_button)
            
        except Exception as e:
            self.server_details_layout.addWidget(QLabel("Сервер не найден, либо недоступен"))

    def remove_server(self, server_address):
        if server_address in self.servers:
            del self.servers[server_address]
            self.save_servers()
            self.refresh_server_list()

    def refresh_all_servers(self):
        for i in range(self.server_list.count()):
            server_address = self.server_list.item(i).text()
            try:
                server = JavaServer.lookup(server_address)
                status = server.status()
                self.server_list.item(i).setForeground(Qt.GlobalColor.green)
            except:
                self.server_list.item(i).setForeground(Qt.GlobalColor.red)

    def change_theme(self, theme):
        if theme == "Dark":
            self.setStyleSheet("""
                QMainWindow { background-color: #2b2b2b; color: #ffffff; }
                QWidget { background-color: #2b2b2b; color: #ffffff; }
                QLabel { color: #ffffff; }
                QPushButton { background-color: #3b3b3b; color: #ffffff; border: 1px solid #555555; padding: 5px; }
                QPushButton:hover { background-color: #4b4b4b; }
                QLineEdit { background-color: #3b3b3b; color: #ffffff; border: 1px solid #555555; padding: 5px; }
                QListWidget { background-color: #3b3b3b; color: #ffffff; border: 1px solid #555555; }
            """)
        else:
            self.setStyleSheet("")
        self.settings["theme"] = theme
        self.save_settings()

    def load_settings(self):
        try:
            with open("settings.json", "r") as f:
                return json.load(f)
        except:
            return {"theme": "Light"}

    def save_settings(self):
        with open("settings.json", "w") as f:
            json.dump(self.settings, f)

    def load_servers(self):
        try:
            with open("servers.json", "r") as f:
                return json.load(f)
        except:
            return {}

    def save_servers(self):
        with open("servers.json", "w") as f:
            json.dump(self.servers, f)

def main():
    app = QApplication(sys.argv)
    window = MinecraftServerMonitor()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()