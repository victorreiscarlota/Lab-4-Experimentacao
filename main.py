from __future__ import annotations
import sys
import os
import subprocess
import argparse
import json
from typing import Optional
import pandas as pd
import numpy as np
from dotenv import load_dotenv

load_dotenv() 

PY = sys.executable 

def run_subscript(script_path: str, args: list[str]) -> int:
    cmd = [PY, script_path] + args
    print("Executando:", " ".join(cmd))
    res = subprocess.run(cmd)
    return res.returncode

def collect(query: str, max_records: int, out: str, per_page: int = 100, sleep: float = 1.5) -> None:
    script = os.path.join("scripts", "collect_github.py")
    args = ["--query", query, "--max", str(max_records), "--out", out, "--per_page", str(per_page), "--sleep", str(sleep)]
    rc = run_subscript(script, args)
    if rc != 0:
        raise SystemExit(f"collect_github.py retornou código {rc}")

def collect_range(lang: str, start: str, end: str, out: str, max_per_period: int = 800) -> None:
    script = os.path.join("scripts", "collect_by_date_ranges.py")
    args = ["--lang", lang, "--start", start, "--end", end, "--out", out, "--max_per_period", str(max_per_period)]
    rc = run_subscript(script, args)
    if rc != 0:
        raise SystemExit(f"collect_by_date_ranges.py retornou código {rc}")

def process_csv(input_path: str, output_path: str, drop_duplicates_on: str = "full_name") -> dict:
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Arquivo de entrada não encontrado: {input_path}")

    print(f"Carregando {input_path} ...")
    df = pd.read_csv(input_path)

    expected = ["full_name","name","owner","language","stars","forks","open_issues","watchers",
                "created_at","updated_at","license","topics","url","description"]
    for c in expected:
        if c not in df.columns:
            df[c] = np.nan

    df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
    df["updated_at"] = pd.to_datetime(df["updated_at"], errors="coerce")
    for ncol in ["stars","forks","open_issues","watchers"]:
        df[ncol] = pd.to_numeric(df[ncol], errors="coerce").astype("Int64")

    for tcol in ["language","license","topics","description"]:
        df[tcol] = df[tcol].fillna("Desconhecido")

    if drop_duplicates_on and drop_duplicates_on in df.columns:
        before = len(df)
        df = df.drop_duplicates(subset=[drop_duplicates_on])
        after = len(df)
        print(f"Removidas {before-after} duplicatas (base={before} -> {after})")

    df["YearMonth"] = df["created_at"].dt.to_period("M").astype(str).fillna("Desconhecido")
    df["StarsLog"] = df["stars"].apply(lambda x: np.log10(int(x) + 1) if pd.notna(x) else np.nan)

    if "stars" in df.columns:
        df = df.sort_values(by="stars", ascending=False)

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Arquivo processado salvo em: {output_path}")

    stats = summarize_dataframe(df)
    stats_path = os.path.splitext(output_path)[0] + ".summary.json"
    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    print(f"Resumo estatístico salvo em: {stats_path}")

    return stats

def summarize_dataframe(df: pd.DataFrame) -> dict:
    total = len(df)
    def safe_agg(col, func):
        try:
            series = df[col].dropna().astype(float)
            if len(series)==0:
                return None
            return float(getattr(series, func)())
        except Exception:
            return None

    stats = {
        "total_records": int(total),
        "languages_unique": int(df["language"].nunique(dropna=True)),
        "top_languages": df["language"].value_counts().head(10).to_dict(),
        "stars": {
            "mean": safe_agg("stars","mean"),
            "median": safe_agg("stars","median"),
            "std": safe_agg("stars","std"),
            "min": safe_agg("stars","min"),
            "max": safe_agg("stars","max")
        },
        "forks": {
            "mean": safe_agg("forks","mean"),
            "median": safe_agg("forks","median"),
            "std": safe_agg("forks","std"),
            "min": safe_agg("forks","min"),
            "max": safe_agg("forks","max")
        },
        "missing": {
            "language_null_pct": float((df["language"].isna() | (df["language"]=="Desconhecido")).sum()) / max(1, total),
            "license_null_pct": float((df["license"].isna() | (df["license"]=="Desconhecido")).sum()) / max(1, total),
            "topics_null_pct": float((df["topics"].isna() | (df["topics"]=="Desconhecido")).sum()) / max(1, total),
        },
        "by_month_counts": df["YearMonth"].value_counts().sort_index().to_dict()
    }
    return stats

def print_stats(stats: dict, pretty: bool = True) -> None:
    if pretty:
        print(json.dumps(stats, indent=2, ensure_ascii=False))
    else:
        print(stats)

def main(argv: Optional[list[str]] = None) -> None:
    parser = argparse.ArgumentParser(prog="main.py", description="Orquestrador: coleta e preparação de dados para Sprint 1")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_collect = sub.add_parser("collect", help="Coleta com uma única query (até ~1000 resultados)")
    p_collect.add_argument("--query", required=True)
    p_collect.add_argument("--max", type=int, default=500)
    p_collect.add_argument("--out", default="data/repos.csv")
    p_collect.add_argument("--per_page", type=int, default=100)
    p_collect.add_argument("--sleep", type=float, default=1.5)

    p_crange = sub.add_parser("collect_range", help="Coleta por intervalos de data (gera CSV concatenado)")
    p_crange.add_argument("--lang", required=True)
    p_crange.add_argument("--start", required=True)
    p_crange.add_argument("--end", required=True)
    p_crange.add_argument("--out", default="data/repos_concatenated.csv")
    p_crange.add_argument("--max_per_period", type=int, default=800)

    p_proc = sub.add_parser("process", help="Processa/limpa CSV gerado pela coleta")
    p_proc.add_argument("--in", dest="input", required=True)
    p_proc.add_argument("--out", dest="output", default="data/repos_concatenated_clean.csv")

    p_stats = sub.add_parser("stats", help="Imprime o arquivo summary.json gerado pelo process, ou calcula estatísticas de um CSV")
    p_stats.add_argument("--in", dest="input", required=True)

    p_all = sub.add_parser("all", help="Collect by ranges then process (wrapper)")
    p_all.add_argument("--lang", required=True)
    p_all.add_argument("--start", required=True)
    p_all.add_argument("--end", required=True)
    p_all.add_argument("--out", default="data/repos_concatenated.csv")
    p_all.add_argument("--max_per_period", type=int, default=800)
    p_all.add_argument("--processed_out", default="data/repos_concatenated_clean.csv")

    args = parser.parse_args(argv)

    if args.cmd == "collect":
        collect(args.query, args.max, args.out, per_page=args.per_page, sleep=args.sleep)
    elif args.cmd == "collect_range":
        collect_range(args.lang, args.start, args.end, args.out, max_per_period=args.max_per_period)
    elif args.cmd == "process":
        stats = process_csv(args.input, args.output)
        print_stats(stats)
    elif args.cmd == "stats":
        summary_path = os.path.splitext(args.input)[0] + ".summary.json"
        if os.path.exists(summary_path):
            with open(summary_path, "r", encoding="utf-8") as f:
                stats = json.load(f)
            print_stats(stats)
        else:
            df = pd.read_csv(args.input)
            stats = summarize_dataframe(df)
            print_stats(stats)
    elif args.cmd == "all":
        collect_range(args.lang, args.start, args.end, args.out, max_per_period=args.max_per_period)
        stats = process_csv(args.out, args.processed_out)
        print_stats(stats)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()