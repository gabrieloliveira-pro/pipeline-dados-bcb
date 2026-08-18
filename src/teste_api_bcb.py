import requests

# Taxa SELIC diária (SGS - Banco Central do Brasil)

url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.11/dados/ultimos/5?formato=json"

response = requests.get(url)

if response.status_code == 200:
    dados = response.json()
    print(f'Sucesso! {len(dados)} registros retornados:\n')
    for registro in dados:
        print(registro)

else:
    print(f'Erro na requisição: {response.status_code}')