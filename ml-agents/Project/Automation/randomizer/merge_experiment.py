import argparse
import csv
import math
import os
import re
import shutil
import sys
import yaml

CSV_COLUMNS = [
    "Step", "Policy/Entropy", "Environment/Episode Length", "Trainer Step",
    "Policy/Extrinsic Value Estimate", "Environment/Cumulative Reward", "Policy/Extrinsic Reward",
    "Losses/Policy Loss", "Losses/Value Loss", "Policy/Learning Rate", "Policy/Epsilon",
    "Policy/Beta", "Is Training",
]

DEFAULT_PARAMS = ["learning_rate", "batch_size", "buffer_size", "hidden_units", "num_layers",
                  "gamma", "beta"]


def fail(msg):
    sys.exit(f"merge_experiment: ERROR: {msg}")


# --------------------------------------------------------------------------- raw CSV
def realign(vals):
    step, mid, is_training = vals[0], vals[1:-1], vals[-1]
    pair = next((i for i in range(2, len(mid) - 1) if mid[i] == mid[i + 1]), None)
    if pair is None:
        raise ValueError("cannot find the Cumulative/Extrinsic Reward pair")
    trainer_step, value_est, cum, ext = mid[pair - 2:pair + 2]
    rest = mid[:pair - 2] + mid[pair + 2:]

    group_b = None
    if len(rest) == 2:
        group_a = rest
    elif len(rest) == 7:
        def looks_like_b(w):  # learning rate, epsilon, beta
            return w[2] < 0.01 and 0 < w[3] < 0.5 and 0 < w[4] < 0.1
        first, last = looks_like_b(rest[0:5]), looks_like_b(rest[2:7])
        if first == last:
            raise ValueError("ambiguous column order")
        group_b, group_a = (rest[0:5], rest[5:7]) if first else (rest[2:7], rest[0:2])
    else:
        raise ValueError(f"unexpected number of values ({len(vals)})")

    entropy, ep_len = sorted(group_a)  # assumption: entropy < episode length (true for 3DBall)
    row = {
        "Step": int(step), "Policy/Entropy": entropy, "Environment/Episode Length": ep_len,
        "Trainer Step": int(trainer_step), "Policy/Extrinsic Value Estimate": value_est,
        "Environment/Cumulative Reward": cum, "Policy/Extrinsic Reward": ext,
        "Is Training": int(is_training),
    }
    if group_b:
        row.update(zip(["Losses/Policy Loss", "Losses/Value Loss", "Policy/Learning Rate",
                        "Policy/Epsilon", "Policy/Beta"], group_b))
    return row


def read_raw(path):
    with open(path, newline="") as f:
        lines = list(csv.reader(f))
    rows = []
    for line_no, r in enumerate(lines[1:], start=2):  # the raw header is not reliable
        if not any(x.strip() for x in r):
            continue
        try:
            rows.append(realign([float(x) for x in r]))
        except ValueError as e:
            fail(f"{path} line {line_no}: {e}")
    return rows


def split_runs(rows):
    runs, cur = [], []
    for r in rows:
        if cur and r["Step"] <= cur[-1]["Step"]:
            runs.append(cur)
            cur = []
        cur.append(r)
    if cur:
        runs.append(cur)
    return runs


# --------------------------------------------------------------------------- YAML
def find_key(data, key):
    if isinstance(data, dict):
        for k, v in data.items():
            if k == key and not isinstance(v, dict):
                return v
            found = find_key(v, key)
            if found is not None:
                return found
    return None


def read_yaml(path):
    with open(path) as f:
        text = f.read()
    data = yaml.safe_load(text)
    lines = text.splitlines()
    if len(lines) >= 2 and lines[0].startswith("#") and lines[1].startswith("#"):
        names = [s.strip() for s in lines[0][1:].split(",") if s.strip()]
        header_vals = [s.strip() for s in lines[1][1:].split(",")]
    else:
        names, header_vals = DEFAULT_PARAMS, []
    params = {}
    for i, n in enumerate(names):
        v = find_key(data, n)
        if v is None:
            fail(f"{path}: randomized parameter '{n}' not found in the YAML")
        if i < len(header_vals) and not math.isclose(float(header_vals[i]), float(v), rel_tol=1e-9):
            fail(f"{path}: '{n}' is {v} in the YAML but {header_vals[i]} in its header line")
        params[n] = v
    return params, data


def mismatch(run, data):
    first = next((r for r in run if "Policy/Learning Rate" in r), None)
    if first is None:
        return None
    lr, beta = find_key(data, "learning_rate"), find_key(data, "beta")
    max_steps = find_key(data, "max_steps")
    lr_sched = find_key(data, "learning_rate_schedule") or "linear"
    beta_sched = find_key(data, "beta_schedule") or lr_sched
    decay = 1 - first["Step"] / max_steps if max_steps else 1
    exp_lr = lr * (decay if lr_sched == "linear" else 1)
    exp_beta = beta * (decay if beta_sched == "linear" else 1)
    return max(abs(first["Policy/Learning Rate"] / exp_lr - 1),
               abs(first["Policy/Beta"] / exp_beta - 1))


def choose_run(runs, data, path, check):
    scores = [mismatch(r, data) for r in runs]
    if not check:
        return len(runs) - 1
    good = [i for i, s in enumerate(scores) if s is not None and s < 0.15]
    if len(good) != 1:
        shown = ["n/a" if s is None else f"{s:.2f}" for s in scores]
        fail(f"{path}: cannot match {len(runs)} run(s) in the CSV to this YAML (mismatch per run: "
             f"{shown}; 0 = perfect). Wrong YAML? Use --no-check to skip this test.")
    if len(runs) > 1:
        print(f"merge_experiment: note: the CSV held {len(runs)} runs; used run {good[0] + 1}, "
              f"which matches the YAML")
    return good[0]


# --------------------------------------------------------------------------- commands
def next_number(out_dir, prefix):
    pat = re.compile(rf"^{re.escape(prefix)}(\d+)\.csv$")
    nums = [int(m.group(1)) for f in os.listdir(out_dir) if (m := pat.match(f))]
    return max(nums, default=0) + 1


def cmd_merge(a):
    params, data = read_yaml(a.yaml)
    if not os.path.isdir(a.csv_dir):
        fail(f"CSV folder not found: {a.csv_dir}")
    raws = sorted(f for f in os.listdir(a.csv_dir) if f.endswith(".csv"))
    if not raws:
        fail(f"no CSV in {a.csv_dir} (did the csv-plugin run?)")
    os.makedirs(os.path.join(a.out_dir, "raw"), exist_ok=True)
    for name in raws:
        raw_path = os.path.join(a.csv_dir, name)
        runs = split_runs(read_raw(raw_path))
        if not runs:
            fail(f"{raw_path} has no data rows")
        run = runs[choose_run(runs, data, raw_path, not a.no_check)]
        prefix = a.name or os.path.splitext(name)[0]
        n = next_number(a.out_dir, prefix)
        out_path = os.path.join(a.out_dir, f"{prefix}{n}.csv")
        with open(out_path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=CSV_COLUMNS + list(params), restval="")
            w.writeheader()
            for r in run:
                w.writerow({**r, **params})
        shutil.move(raw_path, os.path.join(a.out_dir, "raw", f"{prefix}{n}_raw.csv"))
        print(f"merge_experiment: wrote {out_path} ({len(run)} rows, "
              f"{len(CSV_COLUMNS) + len(params)} columns) from {name} + {os.path.basename(a.yaml)}")


def cmd_combine(a):
    pat = re.compile(r"^(.+?)(\d+)\.csv$")
    groups = {}
    for f in os.listdir(a.out_dir):
        m = pat.match(f)
        if m and (not a.name or m.group(1) == a.name):
            groups.setdefault(m.group(1), []).append((int(m.group(2)), f))
    if not groups:
        fail(f"no numbered CSVs in {a.out_dir}")
    for prefix, files in groups.items():
        files.sort()
        header, rows = None, []
        for _, f in files:
            with open(os.path.join(a.out_dir, f), newline="") as fh:
                r = list(csv.reader(fh))
            if header is None:
                header = r[0]
            elif r[0] != header:
                fail(f"{f} has different columns than {files[0][1]}; not combining")
            rows += r[1:]
        out_path = os.path.join(a.out_dir, f"{prefix}_all.csv")
        with open(out_path, "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(header)
            w.writerows(rows)
        print(f"merge_experiment: wrote {out_path} ({len(files)} experiments, {len(rows)} rows)")


def main():
    ap = argparse.ArgumentParser(description="Merge ML-Agents CSVs with randomized YAML values.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("merge", help="merge the latest experiment")
    m.add_argument("--yaml", required=True, help="the output_<runId>.yaml of this experiment")
    m.add_argument("--csv-dir", default=os.path.join("results", "csv_output"))
    m.add_argument("--out-dir", default=os.path.join("results", "merged"))
    m.add_argument("--name", help="file name prefix (default: the CSV's name, e.g. 3DBall)")
    m.add_argument("--no-check", action="store_true",
                   help="skip the test that the YAML belongs to this CSV")
    c = sub.add_parser("combine", help="append all numbered CSVs into <name>_all.csv")
    c.add_argument("--out-dir", default=os.path.join("results", "merged"))
    c.add_argument("--name", help="only combine this prefix")
    a = ap.parse_args()
    os.makedirs(a.out_dir, exist_ok=True)
    cmd_merge(a) if a.cmd == "merge" else cmd_combine(a)


if __name__ == "__main__":
    main()
