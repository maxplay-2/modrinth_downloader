from setuptools import setup, find_packages

setup(
    name="modrinth-downloader",           # Название пакета на PyPI
    version="0.1.0",                       # Версия
    packages=find_packages(),              # Автоматически находит пакет modrinth_downloader
    install_requires=[
        "PySide6>=6.5.0",
        "requests>=2.31.0"
    ],
    entry_points={
        "console_scripts": [
            "modrinth-downloader=modrinth_downloader.main:main",
        ],
    },
    author="Ваше Имя",
    author_email="your.email@example.com",
    description="GUI-программа для скачивания модов с Modrinth",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/maxplay-2/modrinth-downloader",  # ссылка на репозиторий
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
)
