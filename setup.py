import os
from setuptools import setup, find_packages


def read(filename: str):
    return open(
        os.path.join(os.path.dirname(__file__), filename), encoding="utf-8"
    ).read()


def read_requirements(filename: str):
    with open(filename, "r", encoding="utf-8") as req:
        return [line.strip() for line in req if line and not line.startswith("#")]


setup(
    name="py-dynaflow",
    version="1.0.0",
    description="A Dynamic Workflow Execution Tool for Python 🚀",
    long_description=read("README.md"),
    long_description_content_type="text/markdown",
    packages=find_packages(exclude=["tests"]),
    install_requires=read_requirements("requirements.txt"),
    extras_require={"dev": read_requirements("requirements-dev.txt")},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
    ],
    python_requires=">=3.9",
    url="https://github.com/sgg10/dynaflow",
    author="sgg10",
    license="MIT",
    author_email="sgg10.develop@gmail.com",
    project_urls={
        "Bug Reports": "https://github.com/sgg10/dynaflow/issues",
        "Source": "https://github.com/sgg10/dynaflow/",
        "Repository": "https://github.com/sgg10/dynaflow/",
    },
)
