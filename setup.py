from setuptools import setup


setup(
    name="Geospark",
    version="1.0",
    py_modules=["geospark"],
    install_requires=[
        "click",
        "requests",
    ],
    entry_points='''
    [console_scripts]
    geospark-cli=geospark:geospark_cli
    ''',
)
