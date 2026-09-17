import sqlite3
import pandas as pd
from pathlib import Path

processed_data_path = Path(__file__).parent / "data" / "processed"
input_path = processed_data_path / "sim_mortalidade_2000_2009.csv"
db_path = processed_data_path / "sim_mortalidade.db"

TABLE_NAME = "obitos"
CHUNKSIZE = 200_000

DTYPE_COLS = {
    "CONTADOR": str, "TIPOBITO": str, "DTNASC": str, "IDADE": str,
    "SEXO": str, "RACACOR": str, "CODMUNRES": str, "OCUP": str, "LOCOCOR": str,
    "QTDFILVIVO": str, "QTDFILMORT": str, "GRAVIDEZ": str, "PARTO": str,
    "OBITOPARTO": str, "OBITOGRAV": str, "OBITOPUERP": str, "ASSISTMED": str,
    "CAUSABAS": str, "CIRCOBITO": str, "ACIDTRAB": str,
    "UF": str, "CAUSA_GRUPO": str,
    "INFANTIL": "Int64", "MATERNO": "Int64", "ANO": "Int64",
    "IDADE_ANOS": "float64",
}


def carregar_sqlite() -> Path:
    db_path.unlink(missing_ok=True)
    conn = sqlite3.connect(db_path)

    total = 0
    leitor = pd.read_csv(
        input_path,
        dtype=DTYPE_COLS,
        parse_dates=["DTOBITO"],
        chunksize=CHUNKSIZE,
    )
    for i, chunk in enumerate(leitor):
        chunk.to_sql(TABLE_NAME, conn, if_exists="append", index=False)
        total += len(chunk)
        print(f"[load] Bloco {i + 1}: +{len(chunk)} registros (total: {total})")

    print("[load] Criando indices...")
    conn.execute(f"CREATE INDEX idx_ano ON {TABLE_NAME} (ANO)")
    conn.execute(f"CREATE INDEX idx_uf ON {TABLE_NAME} (UF)")
    conn.execute(f"CREATE INDEX idx_causa_grupo ON {TABLE_NAME} (CAUSA_GRUPO)")
    conn.execute(f"CREATE INDEX idx_infantil ON {TABLE_NAME} (INFANTIL)")
    conn.execute(f"CREATE INDEX idx_materno ON {TABLE_NAME} (MATERNO)")
    conn.commit()
    conn.close()

    print(f"[load] Concluido. {total} registros carregados em {db_path}")
    return db_path


if __name__ == "__main__":
    carregar_sqlite()
