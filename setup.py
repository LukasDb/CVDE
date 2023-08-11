from setuptools import setup, find_packages

setup(
    name="cvde",
    version="0.5.2",
    description="A development environment for supervised deep learning in computer vision",
    url="todo",
    author="Lukas Dirnberger",
    author_email="lukas.dirnberger@tum.de",
    license="todo",
    packages=find_packages(),
    include_package_data=True,
    install_requires=open("requirements.txt").readlines(),
    entry_points= {"console_scripts": ["cvde = cvde.__main__:run"]},
    classifiers=[
        "Intended Audience :: Science/Research",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3.10",
    ],
)