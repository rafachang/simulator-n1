# src/motor_eventos.py
"""
Motor de eventos N-1 para o simulador de SCADA.

Funcionalidade:
- Agendar e executar eventos de falha/manobra.
- Atualizar estados de equipamentos (equipamento.parametros['estado']).
- Notificar o SCADA via callback quando ocorrerem eventos/estados.
- Opcional: disparar cálculo de fluxo de potência via pandapower_integration.run_powerflow.
"""

from __future__ import annotations

import json
import logging
import threading
import time
from typing import Callable, Dict, Iterable, List, Optional

from utils import Logger

try:
    from pandapower_integration import run_powerflow  # type: ignore
except Exception:
    run_powerflow = None  # type: ignore

# Tipagem do callback de notificação ao SCADA:
# recebe (evento: str, payload: dict)
ScadaCallback = Callable[[str, Dict], None]


class Evento:
    """Representa um evento agendado no simulador."""

    def __init__(
        self,
        tempo_offset_s: float,
        tipo: str,
        alvo_id: int,
        parametros: Optional[Dict] = None,
    ) -> None:
        """
        tempo_offset_s: segundos a partir do início do cenário para disparar.
        tipo: ex: "falha_linha", "abertura_religador", "restauracao".
        alvo_id: id do equipamento ou linha alvo.
        parametros: dicionário livre com parâmetros do evento.
        """
        self.tempo_offset_s = float(tempo_offset_s)
        self.tipo = tipo
        self.alvo_id = int(alvo_id)
        self.parametros = parametros or {}

    def __repr__(self) -> str:
        return (
            f"Evento(t={self.tempo_offset_s}s, tipo={self.tipo}, "
            f"alvo={self.alvo_id}, params={self.parametros})"
        )


class MotorEventos:
    """Motor simples de execução de eventos em tempo real (threaded)."""

    def __init__(
        self,
        rede: Dict[str, List],
        scada_callback: Optional[ScadaCallback] = None,
        enable_powerflow: bool = False,
    ) -> None:
        """
        rede: dicionário com listas de objetos carregados
              (ex: {'barras': [...], 'linhas': [...], 'equipamentos': [...]})
        scada_callback: função que recebe notificações de eventos para o SCADA
        enable_powerflow: se True e se run_powerflow existir, roda fluxo após eventos
        """
        self.logger = Logger("motor_eventos")
        self.rede = rede
        self.scada_callback = scada_callback
        self.enable_powerflow = bool(enable_powerflow) and (run_powerflow is not None)
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    # --------------------------
    # Utilitários de busca
    # --------------------------
    def _find_equipamento(self, eq_id: int):
        for e in self.rede.get("equipamentos", []):
            if getattr(e, "id", None) == eq_id:
                return e
        return None

    def _find_linha(self, linha_id: int):
        for l in self.rede.get("linhas", []):
            if getattr(l, "id", None) == linha_id:
                return l
        return None

    # --------------------------
    # Ações de evento
    # --------------------------
    def _notificar_scada(self, evento: str, payload: Dict) -> None:
        """Chama o callback do SCADA com proteção contra exceção."""
        self.logger.debug("Notificando SCADA: %s %s", evento, payload)
        if self.scada_callback:
            try:
                self.scada_callback(evento, payload)
            except Exception as exc:  # pragma: no cover - externo
                self.logger.exception("Erro no callback do SCADA: %s", exc)

    def _atualizar_estado_equipamento(
        self, equipamento, novo_estado: str, motivo: str = ""
    ) -> None:
        """Atualiza parâmetros do equipamento e emite log/notify."""
        old = equipamento.parametros.get("estado")
        equipamento.parametros["estado"] = novo_estado
        self.logger.info(
            "Equipamento %s (id=%s): %s -> %s (%s)",
            getattr(equipamento, "tipo", "?"),
            getattr(equipamento, "id", "?"),
            old,
            novo_estado,
            motivo,
        )
        payload = {
            "equipamento_id": equipamento.id,
            "tipo": equipamento.tipo,
            "estado_anterior": old,
            "estado_atual": novo_estado,
            "motivo": motivo,
        }
        self._notificar_scada("estado_equipamento", payload)

    def _rodar_powerflow_se_for_codigo(self) -> None:
        """Roda o pandapower se estiver habilitado e anexa resultados aos logs."""
        if not self.enable_powerflow:
            return

        try:
            # Supõe que run_powerflow aceita 'rede' no formato que você define.
            resultados = run_powerflow(self.rede)  # type: ignore
            ts = time.strftime("%Y%m%d_%H%M%S")
            fname = f"data/historicos/fluxo_potencia/fluxo_{ts}.json"
            with open(fname, "w", encoding="utf-8") as fp:
                json.dump(resultados, fp, indent=2, ensure_ascii=False)
            self.logger.info("Powerflow gerado e salvo em: %s", fname)
            self._notificar_scada("powerflow", {"arquivo": fname, "resultados": resultados})
        except Exception:  # pragma: no cover - externo
            self.logger.exception("Erro ao executar run_powerflow")

    def _executar_evento(self, evento: Evento) -> None:
        """Executa a lógica do evento, atualiza equipamento e notifica SCADA."""
        self.logger.debug("Executando %s", evento)

        if evento.tipo == "falha_linha":
            linha = self._find_linha(evento.alvo_id)
            if linha is None:
                self.logger.warning("Linha id=%s não encontrada", evento.alvo_id)
                return
            # Marca na linha um estado (por simplicidade colocamos no objeto)
            setattr(linha, "estado", "fora")
            self.logger.info("Linha %s marcada como 'fora' (id=%s)", linha, linha.id)
            self._notificar_scada(
                "falha_linha",
                {"linha_id": linha.id, "origem": linha.barra_origem, "destino": linha.barra_destino},
            )

        elif evento.tipo in ("abertura_religador", "falha_religador"):
            eq = self._find_equipamento(evento.alvo_id)
            if eq is None:
                self.logger.warning("Equipamento id=%s não encontrado", evento.alvo_id)
                return
            novo_estado = "aberto" if evento.tipo == "abertura_religador" else "falha"
            self._atualizar_estado_equipamento(eq, novo_estado, motivo=evento.tipo)

        elif evento.tipo == "restauracao_religador":
            eq = self._find_equipamento(evento.alvo_id)
            if eq is None:
                self.logger.warning("Equipamento id=%s não encontrado", evento.alvo_id)
                return
            self._atualizar_estado_equipamento(eq, "fechado", motivo="restauracao")

        elif evento.tipo == "transformador_saida":
            eq = self._find_equipamento(evento.alvo_id)
            if eq is None:
                self.logger.warning("Equipamento id=%s não encontrado", evento.alvo_id)
                return
            self._atualizar_estado_equipamento(eq, "inativo", motivo="transformador_saida")
            self._notificar_scada("transformador_saida", {"transformador_id": eq.id})

        elif evento.tipo == "alarme_manual":
            # evento genérico para testes
            self._notificar_scada("alarme_manual", evento.parametros)

        else:
            self.logger.warning("Tipo de evento desconhecido: %s", evento.tipo)

        # opcional: rodar fluxo de potência e salvar histórico
        self._rodar_powerflow_se_for_codigo()

    # --------------------------
    # Agendamento/Execução
    # --------------------------
    def run_scenario(self, eventos: Iterable[Evento], realtime: bool = True) -> None:
        """
        Executa os eventos do cenário.

        realtime=True -> usa os offsets em segundos reais.
        realtime=False -> executa eventos o mais rápido possível seguindo a ordem.
        """
        ev_list = sorted(list(eventos), key=lambda e: e.tempo_offset_s)

        start_ts = time.time()
        self.logger.info("Iniciando cenário com %d eventos", len(ev_list))

        for ev in ev_list:
            if self._stop_event.is_set():
                self.logger.info("Execução interrompida.")
                break

            if realtime:
                target = start_ts + ev.tempo_offset_s
                now = time.time()
                wait = target - now
                if wait > 0:
                    self.logger.debug("Aguardando %.3fs para o próximo evento", wait)
                    time.sleep(wait)

            # Executa o evento
            self._executar_evento(ev)

        self.logger.info("Cenário finalizado.")

    def start_in_thread(self, eventos: Iterable[Evento], realtime: bool = True) -> None:
        """Inicializa a execução em uma thread separada."""
        if self._thread and self._thread.is_alive():
            raise RuntimeError("Motor já está em execução")

        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self.run_scenario, args=(eventos, realtime), daemon=True
        )
        self._thread.start()
        self.logger.debug("Motor iniciado em thread.")

    def stop(self, timeout: Optional[float] = None) -> None:
        """Solicita parada e aguarda finalização da thread (se houver)."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout)
            self.logger.debug("Thread finalizada (join).")
