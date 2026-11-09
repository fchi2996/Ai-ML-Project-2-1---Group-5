import csv
import os
from typing import Dict, List
from mlagents.trainers.settings import RunOptions
from mlagents.trainers.stats import StatsWriter, StatsSummary

class CSVWriter(StatsWriter):
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        os.makedirs(base_dir, exist_ok=True)

    def write_stats(self, category: str, values: Dict[str, StatsSummary], step: int) -> None:
        filepath = os.path.join(self.base_dir, f"{category}.csv")
        file_exists = os.path.isfile(filepath)

        with open(filepath, "a", newline="") as f:
            writer = csv.writer(f)
            if not file_exists:
                headers = ["Step"] + list(values.keys())
                writer.writerow(headers)

            row = [step] + [values[k].mean for k in values.keys()]
            writer.writerow(row)

def get_csv_writer(run_options: RunOptions) -> List[StatsWriter]:
    base_dir = os.path.join("results", "csv_output")
    return [CSVWriter(base_dir=base_dir)]