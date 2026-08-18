import os
import requests
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def buscar_dados_selic():
    url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.11/dados/ultimos/20?formato=json"
    response = requests.get(url)

    if response.status_code != 200:
        print(f'Status: {response.status_code}')
        print(f'Resposta: {response.text}')
    response.raise_for_status()
    return response.json()

def conectar_db():
    return psycopg2.connect(
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT'),
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD')
    )

def inserior_dados(conexao, dados):
    cursor = conexao.cursor()
    inseridos = 0

    for registro in dados:
        data_formatada = registro['data'] # formato 'dd/mm/aaaa'
        dia, mes, ano = data_formatada.split('/')
        data_sql = f'{ano},{mes},{dia}'
        valor = registro ['valor']

        cursor.execute(
            """
            INSERT INTO selic (data, valor)
            VALUES(%s, %s)
            ON CONFLICT (data) DO NOTHING
            """,
            (data_sql, valor)
        )

        if cursor.rowcount > 0:
            inseridos += 1

    conexao.commit()
    cursor.close()
    return inseridos

if __name__ == '__main__':
    dados = buscar_dados_selic()
    conexao = conectar_db()
    total_inseridos = inserior_dados(conexao, dados)
    conexao.close()
    print(f'Pipeline executado. {total_inseridos} novos registros inseridos de {len(dados)} recebidos da API')