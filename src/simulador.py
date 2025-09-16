# src/simulador.py (exemplo de execução)
from motor_eventos import Evento, MotorEventos
from classes import Barra, Linha, Carga, Equipamento  # suas classes
import time

def scada_receiver(evento: str, payload: dict):
    print(f"[SCADA RECEBEU] {evento} -> {payload}")

# carregar rede (ex: já com carregar_rede)
# aqui criamos manualmente um pequeno exemplo
b1 = Barra(1, "Barra A", 13.8)
b2 = Barra(2, "Barra B", 13.8)
l1 = Linha(1, 1, 2, 2.0)
eq_religador = Equipamento(1, "religador", barra=2, parametros={"estado": "fechado"})
eq_trafo = Equipamento(2, "transformador", barra=1, parametros={"estado": "ativo"})

rede = {
    "barras": [b1, b2],
    "linhas": [l1],
    "cargas": [],
    "equipamentos": [eq_religador, eq_trafo],
}

# define eventos: falha de linha após 2s, religador abre em 4s, transformador sai em 8s
eventos = [
    Evento(2.0, "falha_linha", alvo_id=1),
    Evento(4.0, "abertura_religador", alvo_id=1),
    Evento(8.0, "transformador_saida", alvo_id=2),
]

motor = MotorEventos(rede, scada_callback=scada_receiver, enable_powerflow=False)
motor.start_in_thread(eventos, realtime=True)

total_time = max([x.tempo_offset_s for x in eventos])

# espera terminar (ou faça outras tarefas)
time.sleep(total_time + 2)
