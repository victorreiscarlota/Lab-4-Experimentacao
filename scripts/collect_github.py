import os
import time
import argparse
import requests
import pandas as pd
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()
TOKEN = os.getenv("GITHUB_TOKEN")

if not TOKEN:
    raise SystemExit("GITHUB_TOKEN não encontrado no .env. Coloque seu token em .env com GITHUB_TOKEN=...")

HEADERS = {
    "Accept": "application/vnd.github.v3+json",
    "Authorization": f"token {TOKEN}"
}

SEARCH_URL = "https://api.github.com/search/repositories"

def fetch_search(query, page, per_page=100):
    params = {"q": query, "per_page": per_page, "page": page}
    r = requests.get(SEARCH_URL, headers=HEADERS, params=params)
    if r.status_code == 200:
        return r.json(), r.headers
    else:
        raise Exception(f"GitHub API erro {r.status_code}: {r.text}")

def safe_sleep_for_rate_limit(headers):
    rem = int(headers.get("X-RateLimit-Remaining", "1"))
    reset = int(headers.get("X-RateLimit-Reset", "0"))
    if rem <= 2:
        wait = max(0, reset - int(time.time()) + 5)
        print(f"[rate-limit] remaining={rem}. Dormindo {wait}s até reset.")
        time.sleep(wait)

def collect(query, max_records, out_path, per_page=100, sleep_between_pages=2):
    collected = []
    page = 1
    pbar = tqdm(total=max_records, desc="Coletando repos")
    while len(collected) < max_records:
        try:
            data, headers = fetch_search(query, page, per_page)
        except Exception as e:
            print("Erro na requisição:", e)
            break
        items = data.get("items", [])
        if not items:
            break
        for it in items:
            repo = {
                "full_name": it.get("full_name"),
                "name": it.get("name"),
                "owner": it.get("owner", {}).get("login"),
                "language": it.get("language"),
                "stars": it.get("stargazers_count"),
                "forks": it.get("forks_count"),
                "open_issues": it.get("open_issues_count"),
                "watchers": it.get("watchers_count"),
                "created_at": it.get("created_at"),
                "updated_at": it.get("updated_at"),
                "license": it.get("license", {}).get("name") if it.get("license") else None,
                "topics": ",".join(it.get("topics", [])) if it.get("topics") else None,
                "url": it.get("html_url"),
                "description": it.get("description")
            }
            collected.append(repo)
            pbar.update(1)
            if len(collected) >= max_records:
                break
        safe_sleep_for_rate_limit(headers)
        time.sleep(sleep_between_pages)
        page += 1
        if page * per_page > 1000:
            print("Aviso: Search API geralmente retorna no máximo ~1000 resultados por query.")
            break
    pbar.close()
    df = pd.DataFrame(collected)
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    df.to_csv(out_path, index=False)
    print(f"Salvos {len(df)} registros em {out_path}")
    return out_path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", required=True, help='Ex: "language:Python created:>2018-01-01"')
    parser.add_argument("--max", type=int, default=500, help="Máx registros a coletar")
    parser.add_argument("--out", default="data/repos.csv", help="Caminho CSV de saída")
    parser.add_argument("--per_page", type=int, default=100, help="Resultados por página (max 100)")
    parser.add_argument("--sleep", type=float, default=1.5, help="Segundos entre páginas")
    args = parser.parse_args()

    collect(args.query, args.max, args.out, per_page=args.per_page, sleep_between_pages=args.sleep)

if __name__ == "__main__":
    main()