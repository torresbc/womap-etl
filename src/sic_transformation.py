import pandas as pd
import numpy as np
import glob

"""
MAPEAMENTO DE RUBRICA
MAPEAMENTO DE DESCRICAO_RELACIONAMENTO
MAPEAMENTO DE PROFISSAO
MAPEAMENTO DE ESCOLARIDADE
"""

def list_files(path):
    return glob.glob(path)


def read_excel(file):
    return pd.read_excel(file, sheet_name=None)


def select_columns(df, list_index):
    return df.iloc[:, list_index]


def filter_rows(df_fr, column_name, list_values):
    return df_fr[df_fr[column_name].isin(list_values)]


def rename_columns(df, list_columns_name):
    df.columns = [list_columns_name]
    return df


def load_sic_dataset():
    files = list_files("../dataset/input/sic/*.xlsx")
    list_dfs = []
    df = pd.DataFrame()

    for file in files:
        df = pd.concat(read_excel(file), ignore_index=True)

        df = select_columns(df, [6, 7, 10, 12, 13, 18, 24, 27, 30, 31, 33, 34, 35, 36, 37, 44, 46, 47, 48, 49, 50])

        df['NOME_MUNICIPIO_CIRC'] = df['NOME_MUNICIPIO_CIRC'].squeeze().str.strip()
        df["NOME_MUNICIPIO_CIRC"] = df["NOME_MUNICIPIO_CIRC"].replace({'S.ANDRE': 'Santo André',
                                                                       'S.BERNARDO DO CAMPO': 'São Bernardo do Campo',
                                                                       'DIADEMA': 'Diadema',
                                                                       'S.CAETANO DO SUL': 'São Caetano do Sul',
                                                                       'MAUA': 'Mauá',
                                                                       'RIBEIRAO PIRES': 'Ribeirão Pires',
                                                                       'RIO GRANDE DA SERRA': 'Rio Grande da Serra'})

        list_dfs.append(df)

    df = pd.DataFrame(np.concatenate(list_dfs, axis=0))
    df = rename_columns(df, ["NUM_BO", "DEPARTAMENTO", "MUNICIPIO", "DATA", "HORA", "PERIODO", "VIOLENCIA_DOMESTICA", "RUBRICA",
                             "BAIRRO", "DESCRICAO_LOCAL", "CEP", "LOGRADOURO", "NUMERO", "LATITUDE", "LONGITUDE",
                             "DESCRICAO_RELACIONAMENTO", "SEXO", "IDADE", "COR_PELE", "PROFISSAO", "ESCOLARIDADE"])

    return df


def replace_values(df, column_name, dict_values):
    df[column_name] = df[column_name].replace(dict_values)
    return df


def normalize_periods(df):
    """
    Matutino ou Manhã: 6:00 às 11:59
    Vespertino ou Tarde: 12:00 (Meio-dia) às 17:59
    Noite ou Noturno 18:00 às 23:59
    Madrugada ou Sembrol: 00:00 (Meia-noite) às 05:59
    """
    list_ranges = [[6, 12], [12, 18], [18, 24], [0, 6]]
    list_period = ['Manhã', 'Tarde', 'Noite', 'Madrugada']

    df = df.dropna(how='all').fillna('')
    df['PERIODO'] = df['PERIODO'].squeeze().str.strip()
    df['HORA'] = '0 days ' + df['HORA'].astype('str')

    df = replace_values(df, 'PERIODO', {'PELA MANHÃ': 'Manhã', 'A TARDE': 'Tarde', 'A NOITE': 'Noite',
                                        'DE MADRUGADA': 'Madrugada', 'EM HORA INCERTA': 'Em hora incerta'})

    for ranges, periods in zip(list_ranges, list_period):
        df['HORA'] = pd.to_timedelta(df['HORA'].squeeze())

        datetime_start = pd.Timedelta(ranges[0], "h")
        datetime_end = pd.Timedelta(ranges[1], "h")

        updated = (pd.to_timedelta(df['HORA'].squeeze()) >= datetime_start) & (pd.to_timedelta(df['HORA'].squeeze()) < datetime_end) & (pd.to_timedelta(df['HORA'].squeeze()) != pd.Timedelta("0 days 00:00:00"))
        df.loc[updated, 'PERIODO'] = periods

    return df


def normalize_professions(df):
    df = replace_values(df, 'PROFISSAO', {'DESEMPREGADO': 'Desempregado', 'DESEMPREGADO(A)': 'Desempregado'})
    df['PROFISSAO'] = np.where((df['PROFISSAO'] != 'Desempregado'), 'Empregado', df['PROFISSAO'])
    return df


def mapping_values(df, path, column_old, column_new):
    df_map = pd.concat(read_excel(path))

    dict_map = df_map.set_index(column_old)[column_new].to_dict()
    return replace_values(df, column_old, dict_map)


def replace_nan(df):
    return df.replace('', 'Não Informado', regex=True)


if __name__ == '__main__':
    df1 = load_sic_dataset()
    df2 = normalize_periods(df1)
    df3 = normalize_professions(df2)
    df4 = mapping_values(df3, '../dataset/map/ESTABELECIMENTOS.xlsx', 'DESCRICAO_LOCAL', 'DESCRICAO_LOCAL_ATUALIZADA')
    df5 = mapping_values(df4, '../dataset/map/RELACIONAMENTOS.xlsx', 'DESCRICAO_RELACIONAMENTO', 'DESCRICAO_RELACIONAMENTO_ATUALIZADA')
    df6 = mapping_values(df5, '../dataset/map/RUBRICAS.xlsx', 'RUBRICA', 'RUBRICA_ATUALIZADA')
    df7 = replace_nan(df6)
    df7['NATUREZA_APURADA'] = 'Violência Contra Mulher'

    df8 = df7[['NUM_BO', 'DEPARTAMENTO', 'DATA', 'HORA', 'PERIODO', 'MUNICIPIO', 'LOGRADOURO', 'NUMERO', 'LATITUDE', 'LONGITUDE',
               'DESCRICAO_LOCAL', 'NATUREZA_APURADA', 'SEXO', 'IDADE', 'COR_PELE', 'PROFISSAO', 'ESCOLARIDADE', 'BAIRRO', 'CEP',
               'VIOLENCIA_DOMESTICA', 'RUBRICA']]

    df8.to_excel('../dataset/output/dataset_sic.xlsx')
