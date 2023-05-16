from setuptools import setup, find_packages
import cvde

setup(
    name="cvde",
    version="0.1.1",
    description="A development environment for supervised deep learning in computer vision",
    url="todo",
    author="Lukas Dirnberger",
    author_email="lukas.dirnberger@tum.de",
    license="todo",
    packages=find_packages(),
    install_requires=open("requirements.txt").readlines(),
    entry_points=cvde.__entry_points__,
    classifiers=[
        "Development Status :: 1 - Planning",
        "Intended Audience :: Science/Research",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3.10",
    ],
)
