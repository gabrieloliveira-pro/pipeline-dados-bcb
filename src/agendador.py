import schedule
import time
from pipeline_selic import main
import logging      

logger = logging.getLogger(__name__)

def executar_pipeline():
    logger.info('Executando pipeline agendado.')
    main()


schedule.every().day.at('17:14').do(executar_pipeline)

if __name__ == '__main__':
    logger.info('Agendador iniciando. Aguardando horario programado (09:00 diariamente)')
    while True:
        schedule.run_pending()
        time.sleep(60)