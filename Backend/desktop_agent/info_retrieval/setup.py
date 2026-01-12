from setuptools import find_packages, setup

setup(
    name="info_retrieval",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[],
    description="Engineering document retrieval foundation with dual vector indexes.",
)
