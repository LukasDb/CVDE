from setuptools import setup

setup(
    name='cvde',
    version='0.0.1',    
    description='A development environment for supervised deep learning in computer vision',
    url='todo',
    author='Lukas Dirnberger',
    author_email='lukas.dirnberger@tum.de',
    license='todo',
    packages=['cvde'],
    install_requires=['streamlit', 'streamlit-on-Hover-tabs'],

    classifiers=[
        'Development Status :: 1 - Planning',
        'Intended Audience :: Science/Research',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3.10',
    ],
)