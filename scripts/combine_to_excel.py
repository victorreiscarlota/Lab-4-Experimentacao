
import argparse
from pathlib import Path
import pandas as pd
import sqlite3
from sqlalchemy import create_engine

def write_excel_from_db(db_path: Path, out_path: Path):
    print(f"Lendo SQLite: {db_path}")
    engine = create_engine(f"sqlite:///{db_path}")
    # listar tabelas
    tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;", engine)
    if tables.empty:
        print("Nenhuma tabela encontrada no DB.")
        return
    with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
        for t in tables["name"]:
            print(" - exportando tabela:", t)
            df = pd.read_sql_table(t, engine)
            # Trunca nome da aba para 31 chars (limite Excel)
            sheet_name = (t[:31]) if len(t) > 31 else t
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    print("Excel gerado:", out_path)

def write_excel_from_csv_dir(csv_dir: Path, out_path: Path, pattern="*.csv"):
    print(f"Lendo CSVs em: {csv_dir}")
    files = sorted(csv_dir.glob(pattern))
    if not files:
        print("Nenhum CSV encontrado em", csv_dir)
        return
    with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
        for f in files:
            name = f.stem
            print(" - exportando CSV:", f)
            try:
                df = pd.read_csv(f, dtype=str)
            except Exception as e:
                print("   erro lendo", f, ":", e)
                continue
            # Tenta converter numerics e datas simples automaticamente
            for col in df.columns:
                # numeric
                try:
                    df[col] = pd.to_numeric(df[col], errors="ignore")
                except Exception:
                    pass
            sheet_name = (name[:31]) if len(name) > 31 else name
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    print("Excel gerado:", out_path)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--db", help="Caminho para repos.db (SQLite). Se fornecido, será usado.")
    p.add_argument("--csv-dir", default="data", help="Diretório com CSVs (usado se --db não for passado). Default: ./data")
    p.add_argument("--out", "-o", default="all_tables.xlsx", help="Arquivo Excel de saída")
    args = p.parse_args()

    out_path = Path(args.out).resolve()

    if args.db:
        db_path = Path(args.db).resolve()
        if not db_path.exists():
            print("Arquivo DB não encontrado:", db_path)
            return
        write_excel_from_db(db_path, out_path)
    else:
        csv_dir = Path(args.csv_dir).resolve()
        if not csv_dir.exists() or not csv_dir.is_dir():
            print("Diretório CSV não encontrado:", csv_dir)
            return
        write_excel_from_csv_dir(csv_dir, out_path)

if __name__ == "__main__":
    main()