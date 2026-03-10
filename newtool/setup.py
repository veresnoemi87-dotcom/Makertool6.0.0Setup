from setuptools import setup

setup(
    name="maker-tool",
    version="6.0.0",
    description="A CLI tool to encode and run Java/Python binary scripts.",
    py_modules=["maker"],
    entry_points={
        'console_scripts': [
            'maker=maker:main',
        ],
    },
)