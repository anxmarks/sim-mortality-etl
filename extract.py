import io
import time
import zipfile
import requests
from pathlib import Path

sim_csv_base_url = "https://s3.sa-east-1.amazonaws.com/ckan.saude.gov.br/SIM/csv"

raw_data_path = Path(__file__).parent / "data" / "raw"


def download_sim_year(year: int, max_retries: int = 5) -> Path:

    url = f"{sim_csv_base_url}/Mortalidade_Geral_{year}_csv.zip"

    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(url, timeout=120)
            response.raise_for_status()
            break
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            if attempt == max_retries:
                raise
            wait = min(2 ** attempt, 30)
            print(f"[extract] Network error downloading {year} (attempt {attempt}/{max_retries}): {e}")
            print(f"[extract] Retrying in {wait}s...")
            time.sleep(wait)

    raw_data_path.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(io.BytesIO(response.content)) as z:
        inner_name = z.namelist()[0]
        out_path = raw_data_path / f"Mortalidade_Geral_{year}.csv"
        with z.open(inner_name) as src, open(out_path, "wb") as dst:
            dst.write(src.read())

    print(f"[extract] Saved {out_path} ({out_path.stat().st_size / 1e6:.1f} MB)")
    return out_path


def extract_sim_years(start_year: int = 2000, end_year: int = 2009, sleep_seconds: float = 1.0) -> list[Path]:
    paths = []
    for year in range(start_year, end_year + 1):
        print(f"[extract] Downloading {year}...")
        paths.append(download_sim_year(year))
        time.sleep(sleep_seconds)
    return paths


if __name__ == "__main__":
    extract_sim_years(2000, 2009)
