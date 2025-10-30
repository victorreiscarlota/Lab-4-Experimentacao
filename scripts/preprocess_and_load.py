from pathlib import Path
import pandas as pd
import argparse
from sqlalchemy import create_engine
import sys
import os
import glob

def read_csv_safe(path):
    try:
        return pd.read_csv(path, dtype=str)
    except Exception as e:
        print(f"Erro lendo {path}: {e}")
        return pd.DataFrame()

def normalize_df(df):
    expected_cols = ["full_name","name","owner","language","stars","forks","open_issues",
                     "watchers","created_at","updated_at","license","topics","url","description"]
    for c in expected_cols:
        if c not in df.columns:
            df[c] = None

    df = df[expected_cols].copy()
    df = df.applymap(lambda v: v.strip() if isinstance(v, str) else v)

    for col in ["stars","forks","open_issues","watchers"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
    df["updated_at"] = pd.to_datetime(df["updated_at"], errors="coerce")

    now = pd.Timestamp.utcnow()
    df["created_year"] = df["created_at"].dt.year.fillna(0).astype(int)
    df["created_month"] = df["created_at"].dt.to_period("M").astype(str).fillna("")
    df["repo_age_days"] = (now - df["created_at"]).dt.days.fillna(-1).astype(int)

    def count_topics(t):
        if pd.isna(t) or t == "":
            return 0
        return len([x for x in [p.strip() for p in str(t).split(",")] if x])
    df["topics_count"] = df["topics"].apply(count_topics)

    df["license"] = df["license"].fillna("").str.replace("\n"," ").str.strip()

    df.sort_values("updated_at", ascending=False, inplace=True)
    df = df.drop_duplicates(subset=["full_name"], keep="first")

    return df

def build_aggregates(df):
    top_lang = (
        df.groupby("language", dropna=False)
          .agg(repos_count=("full_name","count"),
               stars_sum=("stars","sum"),
               forks_sum=("forks","sum"))
          .reset_index()
          .sort_values("stars_sum", ascending=False)
    )

    top_repos = df[["full_name","owner","language","stars","forks","watchers","created_at","updated_at","url"]].copy()
    top_repos = top_repos.sort_values("stars", ascending=False).reset_index(drop=True)

    monthly = (
        df.dropna(subset=["created_at"])
          .groupby(df["created_at"].dt.to_period("M").astype(str))
          .agg(created_repos=("full_name","count"),
               stars_total=("stars","sum"))
          .rename_axis("month")
          .reset_index()
          .sort_values("month")
    )

    license_dist = (
        df.groupby("license", dropna=False)
          .agg(repos_count=("full_name","count"))
          .reset_index()
          .sort_values("repos_count", ascending=False)
    )

    return {
        "agg_top_languages": top_lang,
        "agg_top_repos_by_stars": top_repos,
        "agg_monthly_creations": monthly,
        "agg_license_distribution": license_dist,
    }

def resolve_input_dir(input_dir: str):
    """Tenta resolver input_dir usando alguns lugares comuns se não existir diretamente."""
    requested = Path(input_dir)
    if requested.exists() and requested.is_dir():
        return requested.resolve()

    script_dir = Path(__file__).resolve().parent

    candidates = [
        script_dir / input_dir,
        script_dir.parent / input_dir,
        Path.cwd() / input_dir,
    ]
    for c in candidates:
        if c.exists() and c.is_dir():
            return c.resolve()

    cur = script_dir
    for _ in range(6):
        cand = cur / "data"
        if cand.exists() and cand.is_dir():
            return cand.resolve()
        if cur.parent == cur:
            break
        cur = cur.parent

    cur = Path.cwd()
    for _ in range(8):
        cand = cur / "data"
        if cand.exists() and cand.is_dir():
            return cand.resolve()
        if cur.parent == cur:
            break
        cur = cur.parent

    return requested

def find_csv_files(input_dir: str, pattern: str, recursive: bool):
    p = resolve_input_dir(input_dir)
    if not p.exists() or not p.is_dir():
        return [], p
    if recursive:
        return sorted([str(Path(f)) for f in p.rglob(pattern)]), p
    else:
        return sorted([str(Path(f)) for f in p.glob(pattern)]), p

def main():
    parser = argparse.ArgumentParser(description="Pré-processa CSVs e gera repos.db")
    parser.add_argument("--input-dir", "-i", default="data", help="Diretório onde estão os CSVs (default: ./data)")
    parser.add_argument("--pattern", "-p", default="*.csv", help="Padrão de arquivos (glob) no diretório, ex: '*_repos_*.csv' (default: *.csv)")
    parser.add_argument("--recursive", "-r", action="store_true", help="Procurar recursivamente")
    parser.add_argument("--out", "-o", default="repos.db", help="Arquivo SQLite de saída (default: repos.db)")
    args = parser.parse_args()

    files, used_dir = find_csv_files(args.input_dir, args.pattern, args.recursive)
    if not files:
        print(f"Nenhum CSV encontrado em '{args.input_dir}' com padrão '{args.pattern}'.")
        if used_dir != Path(args.input_dir):
            print(f"Tentei localizar automaticamente e procurei em: {used_dir}")
        print("Verifique o caminho e rode novamente. Exemplos:")
        print("  python preprocess_and_load.py --input-dir data")
        print("  python preprocess_and_load.py --input-dir ../data --pattern \"*_repos_*.csv\" --recursive")
        print("  python preprocess_and_load.py --input-dir /c/code/Lab-4-Experimentacao/data --recursive")
        return

    print("Arquivos encontrados em:", used_dir)
    for f in files:
        print(" -", f)

    dfs = []
    for f in files:
        df = read_csv_safe(f)
        if not df.empty:
            dfs.append(df)
        else:
            print("Pulando (vazio/erro):", f)

    if not dfs:
        print("Nenhum CSV legível. Saindo.")
        return

    all_df = pd.concat(dfs, ignore_index=True)
    print("Registros brutos:", len(all_df))
    clean = normalize_df(all_df)
    print("Registros únicos após limpeza:", len(clean))

    aggs = build_aggregates(clean)

    engine = create_engine(f"sqlite:///{args.out}")
    clean.to_sql("repos_raw", con=engine, if_exists="replace", index=False)
    for name, table in aggs.items():
        table.to_sql(name, con=engine, if_exists="replace", index=False)

    print("Banco gerado:", args.out)
    print("Tabelas criadas: repos_raw, " + ", ".join(aggs.keys()))

    for name, table in aggs.items():
        print(f"\n=== {name} (top 5) ===")
        print(table.head(5).to_string(index=False))

if __name__ == "__main__":
    main()