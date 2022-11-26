import pandas as pd
import numpy as np
import glob


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


def load_homicide_dataset():
    files = list_files("../dataset/input/homicide/*.xlsx")
    list_dfs = []
    df = pd.DataFrame()

    for file in files:
        df = pd.concat(read_excel(file), ignore_index=True)

        if "Feminicidio" in file:
            df = select_columns(df, [0, 2, 10, 16, 17, 18, 19, 20, 21, 22, 24, 25, 26, 27, 28, 30])

        elif "LCSM" in file:
            df = select_columns(df, [0, 2, 9, 15, 16, 17, 18, 19, 20, 21, 23, 24, 25, 26, 27, 28])

        else:
            df = select_columns(df, [0, 2, 10, 16, 17, 18, 19, 20, 21, 22, 24, 25, 26, 27, 28, 29])

        df = filter_rows(df, df.columns[1], ["Santo André", "São Bernardo do Campo", "Diadema", "São Caetano do Sul",
                                             "Mauá", "Ribeirão Pires", "Rio Grande da Serra"])

        list_dfs.append(df)

    df = pd.DataFrame(np.concatenate(list_dfs, axis=0))
    df = rename_columns(df, ["DEPARTAMENTO", "MUNICIPIO", "NUM_BO", "DATA", "HORA", "DESCRICAO_LOCAL", "LOGRADOURO",
                             "NUMERO", "LATITUDE", "LONGITUDE", "SEXO", "IDADE", "DATA_NASCIMENTO", "COR_PELE",
                             "PROFISSAO", "NATUREZA_APURADA"])

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
    df['PERIODO'] = df['HORA']

    list_ranges = [[6, 12], [12, 18], [18, 24], [0, 6]]
    list_period = ['Manhã', 'Tarde', 'Noite', 'Madrugada']

    df['HORA'] = '0 days ' + df['HORA'].replace(['EM HORA INCERTA', 'PELA MANHÃ', 'A TARDE', 'A NOITE', 'DE MADRUGADA'], '').astype('str')


    for ranges, periods in zip(list_ranges, list_period):
        df['HORA'] = pd.to_timedelta(df['HORA'].squeeze())

        datetime_start = pd.Timedelta(ranges[0], "h")
        datetime_end = pd.Timedelta(ranges[1], "h")

        df['PERIODO'] = np.where(
            (pd.to_timedelta(df['HORA'].squeeze()) >= datetime_start) & (pd.to_timedelta(df['HORA'].squeeze()) < datetime_end),
            periods, df['PERIODO'].squeeze())

    df = replace_values(df, 'PERIODO', {'PELA MANHÃ': 'Manhã', 'A TARDE': 'Tarde', 'A NOITE': 'Noite',
                                        'DE MADRU0GADA': 'Madrugada', 'EM HORA INCERTA': 'Em hora incerta'})

    return df


def normalize_professions(df):
    df = replace_values(df, 'PROFISSAO', {'DESEMPREGADO': 'Desempregado', 'DESEMPREGADO(A)': 'Desempregado'})
    df['PROFISSAO'] = np.where((df['PROFISSAO'] != 'Desempregado'), 'Empregado', df['PROFISSAO'])
    return df


def normalize_local_description(df):
    df_map = pd.concat(read_excel('../dataset/map/ESTABELECIMENTOS.xlsx'))

    dict_map = df_map.set_index('DESCRICAO_LOCAL')['DESCRICAO_LOCAL_ATUALIZADA'].to_dict()
    return replace_values(df, 'DESCRICAO_LOCAL', dict_map)


def replace_nan(df):
    return df.replace(np.nan, 'Não Informado', regex=True)


if __name__ == '__main__':
    df1 = load_homicide_dataset()
    df2 = normalize_periods(df1)
    df3 = normalize_professions(df2)
    df4 = normalize_local_description(df3)

    df5 = replace_values(df4, 'NATUREZA_APURADA', {'Feminicídio-contra a mulher por razões da condição de sexo feminino': 'Feminicídio',
                                                   'HOMICÍDIO DOLOSO': 'Homicídio Doloso',
                                                   'LATROCÍNIO': 'Latrocínio',
                                                   'LESÃO CORPORAL SEGUIDA DE MORTE': 'Lesão corporal seguida de morte'
                                                   })
    df6 = replace_nan(df5)
    df6.drop(columns=['DATA_NASCIMENTO'])
    df6 = df6[['NUM_BO', 'DEPARTAMENTO', 'DATA', 'HORA', 'PERIODO', 'MUNICIPIO', 'LOGRADOURO', 'NUMERO', 'LATITUDE', 'LONGITUDE',
               'DESCRICAO_LOCAL', 'NATUREZA_APURADA', 'SEXO', 'IDADE', 'COR_PELE', 'PROFISSAO']]
    df6.to_excel('../dataset/output/dataset_ssp.xlsx')
