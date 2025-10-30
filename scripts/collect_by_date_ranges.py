import argparse
import subprocess
import pandas as pd
from datetime import datetime, timedelta
import os
import sys

def generate_month_ranges(start_date, end_date):
    start = datetime.fromisoformat(start_date)
    end = datetime.fromisoformat(end_date)
    ranges = []
    cur = start
    while cur <= end:
        next_month = (cur.replace(day=1) + timedelta(days=32)).replace(day=1)
        end_period = min(end, next_month - timedelta(days=1))
        ranges.append((cur.date().isoformat(), end_period.date().isoformat()))
        cur = next_month
    return ranges

def run_collect_for_period(python_exec, lang, start, end, max_per_period, temp_out):
    query = f"language:{lang} created:{start}..{end}"
    cmd = [
        python_exec, os.path.join("scripts", "collect_github.py"),
        "--query", query,
        "--max", str(max_per_period),
        "--out", temp_out
    ]
    print("Executando:", " ".join(cmd))
    subprocess.check_call(cmd)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--lang", required=True, help="Linguagem ex: Python")
    parser.add_argument("--start", required=True, help="Data inicial YYYY-MM-DD")
    parser.add_argument("--end", required=True, help="Data final YYYY-MM-DD")
    parser.add_argument("--out", default="data/repos_concatenated.csv", help="CSV final")
    parser.add_argument("--max_per_period", type=int, default=800, help="Máx por período (por query)")
    args = parser.parse_args()

    python_exec = sys.executable  
    ranges = generate_month_ranges(args.start, args.end)
    temp_files = []
    for start, end in ranges:
        tf = f"data/tmp_{start}_{end}.csv"
        os.makedirs(os.path.dirname(tf), exist_ok=True)
        try:
            run_collect_for_period(python_exec, args.lang, start, end, args.max_per_period, tf)
            temp_files.append(tf)
        except subprocess.CalledProcessError as e:
            print("Erro ao coletar período", start, end, e)
            continue

    dfs = []
    for f in temp_files:
        try:
            df = pd.read_csv(f)
            dfs.append(df)
        except Exception as e:
            print("Erro lendo temporário", f, e)
    if dfs:
        combined = pd.concat(dfs, ignore_index=True)
        combined.drop_duplicates(subset=["full_name"], inplace=True)
        combined.to_csv(args.out, index=False)
        print(f"Concatenação completa: {len(combined)} registros em {args.out}")
    else:
        print("Nenhum arquivo temporário gerado. Verifique erros anteriores.")

if __name__ == "__main__":
    main()