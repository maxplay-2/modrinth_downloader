import sys
import os
import requests
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QFileDialog,
    QProgressBar, QMessageBox, QListWidget, QListWidgetItem,
    QTextEdit, QComboBox
)
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtCore import Qt, QThread, Signal


class DownloadThread(QThread):
    progress = Signal(int)
    finished = Signal(str)
    error = Signal(str)

    def __init__(self, download_url, save_path):
        super().__init__()
        self.download_url = download_url
        self.save_path = save_path

    def run(self):
        try:
            with requests.get(self.download_url, stream=True) as r:
                r.raise_for_status()
                total_length = int(r.headers.get('content-length', 0))
                downloaded = 0
                with open(self.save_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total_length > 0:
                                percent = int(downloaded / total_length * 100)
                                self.progress.emit(percent)
            self.finished.emit(self.save_path)
        except Exception as e:
            self.error.emit(str(e))


class ModDownloader(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Modrinth Downloader")
        self.setGeometry(300, 300, 700, 500)
        self.mods = []
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Ввод названия мода
        self.mod_input = QLineEdit()
        self.mod_input.setPlaceholderText("Введите название мода")
        self.search_btn = QPushButton("Поиск")
        self.search_btn.clicked.connect(self.search_mods)
        layout.addWidget(self.mod_input)
        layout.addWidget(self.search_btn)

        # Список модов
        self.mods_list = QListWidget()
        self.mods_list.itemClicked.connect(self.select_mod)
        layout.addWidget(self.mods_list)

        # Описание мода
        self.description = QTextEdit()
        self.description.setReadOnly(True)
        layout.addWidget(self.description)

        # Фильтры
        filter_layout = QHBoxLayout()
        self.mc_version_combo = QComboBox()
        self.loader_combo = QComboBox()
        self.loader_combo.addItem("Все загрузчики")
        filter_layout.addWidget(QLabel("Версия Minecraft:"))
        filter_layout.addWidget(self.mc_version_combo)
        filter_layout.addWidget(QLabel("Загрузчик:"))
        filter_layout.addWidget(self.loader_combo)
        layout.addLayout(filter_layout)

        # Список версий
        self.version_combo = QComboBox()
        layout.addWidget(self.version_combo)

        # Выбор папки
        folder_layout = QHBoxLayout()
        self.folder_input = QLineEdit()
        self.folder_btn = QPushButton("Выбрать папку")
        self.folder_btn.clicked.connect(self.choose_folder)
        folder_layout.addWidget(self.folder_input)
        folder_layout.addWidget(self.folder_btn)
        layout.addLayout(folder_layout)

        # Кнопка скачать
        self.download_btn = QPushButton("Скачать выбранную версию")
        self.download_btn.clicked.connect(self.download_mod)
        layout.addWidget(self.download_btn)

        # Прогресс-бар
        self.progress_bar = QProgressBar()
        self.progress_bar.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.progress_bar)

        self.setLayout(layout)

        # События фильтров
        self.mc_version_combo.currentIndexChanged.connect(self.apply_filters)
        self.loader_combo.currentIndexChanged.connect(self.apply_filters)

    def choose_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Выберите папку для модов")
        if folder:
            self.folder_input.setText(folder)

    def search_mods(self):
        mod_name = self.mod_input.text().strip()
        if not mod_name:
            QMessageBox.warning(self, "Ошибка", "Введите название мода!")
            return
        try:
            response = requests.get("https://api.modrinth.com/v2/search", params={"query": mod_name})
            data = response.json()
            self.mods = data.get("hits", [])
            self.mods_list.clear()
            self.version_combo.clear()
            self.description.clear()
            self.mc_version_combo.clear()
            self.loader_combo.clear()
            self.loader_combo.addItem("Все загрузчики")
            if not self.mods:
                QMessageBox.information(self, "Результат", "Моды не найдены")
                return
            for mod in self.mods:
                item = QListWidgetItem(mod["title"])
                icon_url = mod.get("icon_url")
                if icon_url:
                    try:
                        pixmap = QPixmap()
                        pixmap.loadFromData(requests.get(icon_url).content)
                        item.setIcon(QIcon(pixmap))
                    except:
                        pass
                self.mods_list.addItem(item)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))

    def select_mod(self, item):
        index = self.mods_list.row(item)
        mod = self.mods[index]
        self.description.setText(mod.get("description", "Нет описания"))
        try:
            proj_id = mod["project_id"]
            versions = requests.get(f"https://api.modrinth.com/v2/project/{proj_id}/version").json()
            self.versions_data = versions
            self.update_filters()
            self.apply_filters()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))

    def update_filters(self):
        mc_versions = set()
        loaders = set()
        for v in self.versions_data:
            mc_versions.update(v["game_versions"])
            loaders.update(v["loaders"])
        self.mc_version_combo.clear()
        self.mc_version_combo.addItem("Все версии")
        self.mc_version_combo.addItems(sorted(mc_versions))
        self.loader_combo.clear()
        self.loader_combo.addItem("Все загрузчики")
        self.loader_combo.addItems(sorted(loaders))

    def apply_filters(self):
        if not hasattr(self, "versions_data"):
            return
        selected_mc = self.mc_version_combo.currentText()
        selected_loader = self.loader_combo.currentText()
        self.version_combo.clear()
        for v in self.versions_data:
            if (selected_mc == "Все версии" or selected_mc in v["game_versions"]) and \
               (selected_loader == "Все загрузчики" or selected_loader in v["loaders"]):
                self.version_combo.addItem(f"{v['name']} ({v['game_versions']}, {v['loaders']})")

    def download_mod(self):
        mods_path = self.folder_input.text().strip()
        if not os.path.exists(mods_path):
            QMessageBox.warning(self, "Ошибка", "Папка не существует!")
            return
        if not hasattr(self, "versions_data") or not self.versions_data:
            QMessageBox.warning(self, "Ошибка", "Выберите мод и версию!")
            return
        index = self.version_combo.currentIndex()
        if index < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите версию!")
            return

        selected_mc = self.mc_version_combo.currentText()
        selected_loader = self.loader_combo.currentText()
        filtered_versions = [
            v for v in self.versions_data
            if (selected_mc == "Все версии" or selected_mc in v["game_versions"]) and
               (selected_loader == "Все загрузчики" or selected_loader in v["loaders"])
        ]
        file_info = filtered_versions[index]["files"][0]
        download_url = file_info["url"]
        filename = file_info["filename"]
        save_path = os.path.join(mods_path, filename)

        self.download_thread = DownloadThread(download_url, save_path)
        self.download_thread.progress.connect(self.progress_bar.setValue)
        self.download_thread.finished.connect(self.download_finished)
        self.download_thread.error.connect(self.download_error)
        self.download_thread.start()
        self.download_btn.setEnabled(False)

    def download_finished(self, path):
        QMessageBox.information(self, "Готово", f"Мод успешно скачан в:\n{path}")
        self.progress_bar.setValue(0)
        self.download_btn.setEnabled(True)

    def download_error(self, message):
        QMessageBox.critical(self, "Ошибка", message)
        self.download_btn.setEnabled(True)
        self.progress_bar.setValue(0)


def main():
    app = QApplication(sys.argv)
    window = ModDownloader()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
