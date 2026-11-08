from setuptools import setup

setup(
    name="csv-plugin",
    version="0.1",
    py_modules=["csv_writer"],
    entry_points={
        "mlagents.stats_writer": [
            "csv = csv_writer:get_csv_writer"
        ]
    },
)