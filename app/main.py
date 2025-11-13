#!/usr/bin/env python3
"""
Gera um Excel único com todas as tabelas encontradas em results/ e algumas agregações úteis.

Uso:
  pip install pandas openpyxl
  python scripts/generate_results_excel.py --results-dir results --out results/all_results.xlsx
"""
from pathlib import Path
import pandas as pd
import json
import argparse
import sys
import ast
import numpy as np

def resolve_results_dir(input_dir: str) -> Path:
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
    return requested

def read_csv(path: Path) -> pd.DataFrame:
    try:
        return pd.read_csv(path)
    except TypeError:
        return pd.read_csv(path, engine="python", encoding="utf-8")
    except Exception:
        return pd.read_csv(path, engine="python", encoding="utf-8", on_bad_lines="skip")

def read_json(path: Path) -> pd.DataFrame:
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    if isinstance(data, list):
        return pd.json_normalize(data)
    elif isinstance(data, dict):
        for k, v in data.items():
            if isinstance(v, list):
                return pd.json_normalize(v)
        return pd.json_normalize([data])
    else:
        return pd.DataFrame()

def parse_cves_column(series: pd.Series) -> pd.Series:
    """
    Robust parsing for the 'cves' column. Returns a Series where each cell is a Python list.
    Handles None, NaN, list/tuple/ndarray/Series, JSON strings, Python-literal lists, and bracketed comma strings.
    """
    def is_nan_scalar(val):
        # True only for scalar NaN (float('nan')), not for arrays/Series
        return isinstance(val, float) and np.isnan(val)

    def parse_cell(x):
        # None
        if x is None:
            return []
        # scalar NaN
        if is_nan_scalar(x):
            return []
        # if already list/tuple/ndarray/Series -> normalize to list of strings
        if isinstance(x, (list, tuple, np.ndarray, pd.Series)):
            try:
                seq = list(x)
            except Exception:
                return []
            out = []
            for v in seq:
                if v is None:
                    continue
                if is_nan_scalar(v):
                    continue
                sval = str(v).strip()
                if sval:
                    out.append(sval.strip("'\""))
            return out
        # otherwise coerce to str and try parse
        s = str(x).strip()
        if not s or s.lower() == "nan":
            return []
        # try JSON first
        try:
            parsed = json.loads(s)
            if isinstance(parsed, list):
                return [str(p).strip() for p in parsed if p is not None and str(p).strip()]
        except Exception:
            pass
        # try Python literal eval (single quotes)
        try:
            parsed = ast.literal_eval(s)
            if isinstance(parsed, list):
                return [str(p).strip() for p in parsed if p is not None and str(p).strip()]
        except Exception:
            pass
        # fallback: remove brackets and split by comma
        s2 = s.strip("[] ")
        if not s2:
            return []
        parts = [p.strip().strip("'\"") for p in s2.split(",") if p.strip()]
        return parts

    return series.apply(parse_cell)

def make_sheet_name(name: str, existing: set) -> str:
    base = name[:31]
    candidate = base
    i = 1
    while candidate in existing:
        suffix = f"_{i}"
        candidate = (base[:31 - len(suffix)] + suffix) if len(base) + len(suffix) > 31 else base + suffix
        i += 1
    existing.add(candidate)
    return candidate

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--results-dir", default="results", help="Diretório com arquivos coletados (default: results)")
    p.add_argument("--out", "-o", default="results/all_results.xlsx", help="Caminho do Excel de saída")
    p.add_argument("--top-n", type=int, default=50, help="Quantos top repos na aba top_vulnerable (default 50)")
    args = p.parse_args()

    results_dir = resolve_results_dir(args.results_dir)
    if not results_dir.exists() or not results_dir.is_dir():
        print("Diretório results não encontrado em:", results_dir)
        sys.exit(1)

    files = sorted([f for f in results_dir.iterdir() if f.is_file() and f.suffix.lower() in {".csv", ".json"}])
    if not files:
        print("Nenhum CSV/JSON encontrado em", results_dir)
        sys.exit(1)

    sheets = {}
    print("Arquivos encontrados em", results_dir)
    for f in files:
        print(" -", f.name)
        try:
            if f.suffix.lower() == ".csv":
                df = read_csv(f)
            else:
                df = read_json(f)
        except Exception as e:
            print("   Erro lendo", f.name, "->", e)
            continue
        df.columns = [str(c).strip() for c in df.columns]
        for col in df.columns:
            if df[col].dtype == object:
                try:
                    conv = pd.to_numeric(df[col], errors="coerce")
                    if conv.notna().sum() > 0:
                        df[col] = conv.where(conv.notna(), df[col])
                except Exception:
                    pass
        sheets[f.stem] = df

    # detect cve-like files
    cve_candidates = [k for k in sheets.keys() if "dependencies_cve" in k.lower() or "cve" in k.lower()]
    existing_sheet_names = set()
    cves_exploded_df = None
    vuln_by_repo_df = None
    top_vuln_df = None

    for key in cve_candidates:
        df = sheets.get(key)
        if df is None:
            continue
        cols = {c.lower(): c for c in df.columns}
        # find cves column
        cves_col = None
        for name in df.columns:
            if name.lower() == "cves" or "cve" in name.lower():
                cves_col = name
                break
        if cves_col:
            df["_cves_list"] = parse_cves_column(df[cves_col])
            exploded = df.copy()
            exploded = exploded.explode("_cves_list")
            exploded = exploded.rename(columns={"_cves_list": "cve"})
            keep_cols = []
            for c in ["repo", "Repo", "repository", "path_usado"]:
                if c in exploded.columns and c not in keep_cols:
                    keep_cols.append(c)
            if "cve" not in exploded.columns:
                exploded["cve"] = None
            selected_cols = [c for c in keep_cols if c in exploded.columns] + ["cve"]
            if selected_cols:
                cves_exploded_df = exploded[selected_cols].reset_index(drop=True)
            else:
                cves_exploded_df = exploded.reset_index(drop=True)
        # vuln summary
        def find_col_possibilities(df_local, names):
            for n in names:
                for c in df_local.columns:
                    if c.lower() == n:
                        return c
            return None
        v_col = find_col_possibilities(df, ["vulnerable_deps", "vulnerable", "vuln", "vulnerabilities"])
        d_col = find_col_possibilities(df, ["dependencies", "deps", "num_dependencies"])
        repo_col = find_col_possibilities(df, ["repo", "repository", "full_name"])
        if repo_col:
            vuln_by_repo_df = pd.DataFrame()
            vuln_by_repo_df["repo"] = df[repo_col].astype(str)
            if d_col and d_col in df.columns:
                vuln_by_repo_df["dependencies"] = pd.to_numeric(df[d_col], errors="coerce").fillna(0).astype(int)
            else:
                vuln_by_repo_df["dependencies"] = 0
            if v_col and v_col in df.columns:
                vuln_by_repo_df["vulnerable_deps"] = pd.to_numeric(df[v_col], errors="coerce").fillna(0).astype(int)
            else:
                vuln_by_repo_df["vulnerable_deps"] = 0
            vuln_by_repo_df["vuln_ratio"] = vuln_by_repo_df.apply(
                lambda r: (r["vulnerable_deps"] / r["dependencies"]) if r["dependencies"] > 0 else None, axis=1
            )
            vuln_by_repo_df = vuln_by_repo_df.sort_values("vulnerable_deps", ascending=False).reset_index(drop=True)
            top_vuln_df = vuln_by_repo_df.head(args.top_n)

    if cves_exploded_df is not None:
        sheets["cves_exploded"] = cves_exploded_df
    if vuln_by_repo_df is not None:
        sheets["vuln_by_repo"] = vuln_by_repo_df
    if top_vuln_df is not None:
        sheets["top_vulnerable"] = top_vuln_df

    out_path = Path(args.out).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
            for name, df in sheets.items():
                sheet_name = make_sheet_name(name, existing_sheet_names)
                try:
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
                except Exception:
                    df2 = df.copy().astype(str)
                    df2.to_excel(writer, sheet_name=sheet_name, index=False)
            readme_text = [
                "Arquivo gerado automaticamente por scripts/generate_results_excel.py",
                "",
                "Cada aba equivale a um arquivo original ou a uma tabela derivada:",
                "- cves_exploded: cada CVE em linha separada com a coluna 'repo' (se o arquivo original tinha cves)",
                "- vuln_by_repo: resumo por repo (dependencies, vulnerable_deps, vuln_ratio)",
                "- top_vulnerable: top N repositórios por número de dependências vulneráveis",
                "- outras abas: uma aba por CSV/JSON lido",
                "",
                "Abra este Excel no Power BI: Home -> Get Data -> Excel -> selecione este arquivo.",
            ]
            rd = pd.DataFrame({"info": readme_text})
            sheet_name = make_sheet_name("README", existing_sheet_names)
            rd.to_excel(writer, sheet_name=sheet_name, index=False)
    except ModuleNotFoundError as e:
        print("Erro: biblioteca necessária para escrever Excel não encontrada:", e)
        print("Instale com: pip install openpyxl")
        sys.exit(1)

    print("Excel gerado em:", out_path)
    print("Abas criadas:")
    for s in sheets.keys():
        print(" -", s)

if __name__ == "__main__":
    main()