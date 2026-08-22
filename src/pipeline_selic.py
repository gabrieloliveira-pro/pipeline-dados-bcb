import os
import logging
from datetime import datetime
import requests
import psycopg2
from dotenv import load_dotenv

load_dotenv()

# Configuração do logging
os.makedirs("logs", exist_ok=True)
nome_arquivo_log = f"logs/pipeline_{datetime.now().strftime('%Y-%m-%d')}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(nome_arquivo_log, encoding="utf-8"),
        logging.StreamHandler()  # também mostra no terminal
    ]
)

logger = logging.getLogger(__name__)


def buscar_dados_selic():
    url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.11/dados/ultimos/20?formato=json"
    response = requests.get(url)
    if response.status_code != 200:
        logger.error(f"Falha na requisicao a API. Status: {response.status_code} - Resposta: {response.text}")
    response.raise_for_status()
    dados = response.json()
    logger.info(f"{len(dados)} registros recebidos da API do BCB.")
    return dados

def validar_registro(registro):
    data = registro.get("data")
    valor = registro.get("valor")

    if not data or not valor:
        logger.warning(f"Registro descartado por campo vazio: {registro}")
        return False

    try:
        valor_float = float(valor)
    except ValueError:
        logger.warning(f"Registro descartado por valor nao numerico: {registro}")
        return False

    if valor_float < 0 or valor_float > 100:
        logger.warning(f"Registro descartado por valor fora do range esperado: {registro}")
        return False

    return True

def conectar_db():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )


def inserir_dados(conexao, dados):
    cursor = conexao.cursor()
    inseridos = 0
    descartados = 0

    for registro in dados:
        if not validar_registro(registro):
            descartados += 1
            continue

        data_formatada = registro["data"]
        dia, mes, ano = data_formatada.split("/")
        data_sql = f"{ano}-{mes}-{dia}"
        valor = registro["valor"]

        cursor.execute(
            """
            INSERT INTO selic (data, valor)
            VALUES (%s, %s)
            ON CONFLICT (data) DO NOTHING
            """,
            (data_sql, valor)
        )
        if cursor.rowcount > 0:
            inseridos += 1

    conexao.commit()
    cursor.close()

    if descartados > 0:
        logger.warning(f"{descartados} registros descartados na validacao.")

    return inseridos


def main():
    logger.info("Iniciando execucao do pipeline SELIC.")
    try:
        dados = buscar_dados_selic()
        conexao = conectar_db()
        total_inseridos = inserir_dados(conexao, dados)
        conexao.close()
        logger.info(f"Pipeline executado com sucesso. {total_inseridos} novos registros inseridos de {len(dados)} recebidos.")
    except Exception as e:
        logger.error(f"Erro na execucao do pipeline: {e}")


if __name__ == "__main__":
    main()