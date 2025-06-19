from setuptools import setup, find_packages

setup(
    name="ocr-backend",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "uvicorn",
        "python-multipart",
        "easyocr",
        "pillow",
        "numpy",
        "pandas",
        "hgtk"
    ],
) 