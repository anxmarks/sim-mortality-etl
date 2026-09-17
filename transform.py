import numpy as np
import pandas as pd
from pathlib import Path

raw_data_path = Path(__file__).parent / "data" / "raw"
processed_data_path = Path(__file__).parent / "data" / "processed"

COLUNAS = ["CONTADOR", "TIPOBITO", "DTOBITO", "DTNASC", "IDADE",
           "SEXO", "RACACOR", "CODMUNRES", "OCUP", "LOCOCOR",
           "QTDFILVIVO", "QTDFILMORT", "GRAVIDEZ", "PARTO",
           "OBITOPARTO", "OBITOGRAV", "OBITOPUERP", "ASSISTMED",
           "CAUSABAS", "CIRCOBITO", "ACIDTRAB"]

UF_POR_CODIGO = {
    "11": "RO", "12": "AC", "13": "AM", "14": "RR", "15": "PA", "16": "AP", "17": "TO",
    "21": "MA", "22": "PI", "23": "CE", "24": "RN", "25": "PB", "26": "PE", "27": "AL", "28": "SE", "29": "BA",
    "31": "MG", "32": "ES", "33": "RJ", "35": "SP",
    "41": "PR", "42": "SC", "43": "RS",
    "50": "MS", "51": "MT", "52": "GO", "53": "DF",
}

CAPITULOS_CID10 = [
    ("A00", "B99", "Infecciosas e parasitarias"),
    ("C00", "D48", "Neoplasias"),
    ("D50", "D89", "Sangue e orgaos hematopoeticos"),
    ("E00", "E90", "Endocrinas, nutricionais e metabolicas"),
    ("F00", "F99", "Transtornos mentais e comportamentais"),
    ("G00", "G99", "Sistema nervoso"),
    ("H00", "H59", "Olho"),
    ("H60", "H95", "Ouvido"),
    ("I00", "I99", "Aparelho circulatorio"),
    ("J00", "J99", "Aparelho respiratorio"),
    ("K00", "K93", "Aparelho digestivo"),
    ("L00", "L99", "Pele"),
    ("M00", "M99", "Osteomuscular"),
    ("N00", "N99", "Aparelho geniturinario"),
    ("O00", "O99", "Gravidez, parto e puerperio"),
    ("P00", "P96", "Periodo perinatal"),
    ("Q00", "Q99", "Malformacoes congenitas"),
    ("R00", "R99", "Sintomas e sinais mal definidos"),
    ("S00", "T98", "Causas externas - lesoes"),
    ("V01", "Y98", "Causas externas - acidentes e violencia"),
    ("Z00", "Z99", "Fatores que influenciam o estado de saude"),
    ("U00", "U99", "Codigos especiais"),
]


def classificar_causa(codigo3):
    if pd.isna(codigo3):
        return np.nan
    for inicio, fim, nome in CAPITULOS_CID10:
        if inicio <= codigo3 <= fim:
            return nome
    return "Nao classificado"


def transformar_ano(ano: int) -> pd.DataFrame:
    df = pd.read_csv(raw_data_path / f"Mortalidade_Geral_{ano}.csv", sep=";", encoding="latin-1", dtype=str)
    df = df[COLUNAS].copy()

    # No arquivo de 2000, o 1o digito de IDADE nao bate com o dicionario oficial
    # (que descreve o formulario atual): 0=minuto, 1=hora, 2=dias, 3=mes, 4=ano,
    # 5=+100 anos. Confirmado empiricamente pelo range de cada valor.
    idade_unidade = df["IDADE"].str[0]
    idade_valor = pd.to_numeric(df["IDADE"].str[1:3], errors="coerce")
    idade_menor_1_ano = idade_unidade.isin(["0", "1", "2", "3"])

    df["INFANTIL"] = ((df["TIPOBITO"] == "2") & idade_menor_1_ano).astype(int)
    df["MATERNO"] = (
        (df["SEXO"] == "2")
        & ((df["OBITOGRAV"] == "1") | df["OBITOPUERP"].isin(["1", "2"]))
    ).astype(int)
    df["IDADE_ANOS"] = np.select(
        [idade_menor_1_ano, idade_unidade == "4", idade_unidade == "5"],
        [0, idade_valor, 100 + idade_valor],
        default=np.nan,
    )

    df["DTOBITO"] = pd.to_datetime(df["DTOBITO"].str.zfill(8), format="%d%m%Y", errors="coerce")
    df["UF"] = df["CODMUNRES"].str[:2].map(UF_POR_CODIGO)
    df["CAUSA_GRUPO"] = df["CAUSABAS"].str[:3].apply(classificar_causa)
    df["ANO"] = ano

    return df


if __name__ == "__main__":
    processed_data_path.mkdir(parents=True, exist_ok=True)
    output_path = processed_data_path / "sim_mortalidade_2000_2009.csv"
    output_path.unlink(missing_ok=True)

    total = 0
    wrote_header = False
    for ano in range(2000, 2010):
        print(f"[transform] Processando {ano}...")
        df_ano = transformar_ano(ano)
        df_ano.to_csv(output_path, mode="a", index=False, header=not wrote_header)
        wrote_header = True
        total += len(df_ano)
        print(f"[transform] {ano}: {len(df_ano)} registros (total: {total})")

    print(f"[transform] Concluido. {total} registros salvos em {output_path}")
