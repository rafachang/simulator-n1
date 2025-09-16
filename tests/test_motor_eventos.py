import time
import pytest
from src.motor_eventos import MotorEventos


def test_inicializacao():
    motor = MotorEventos()
    assert motor.eventos == []
    assert not motor.executando


def test_adicionar_evento():
    motor = MotorEventos()
    def dummy():
        return "ok"
    motor.adicionar_evento(1, dummy)
    assert len(motor.eventos) == 1
    assert motor.eventos[0]["tempo"] == 1
    assert motor.eventos[0]["acao"] == dummy


def test_executar_evento_em_ordem():
    resultados = []

    def evento1():
        resultados.append("A")

    def evento2():
        resultados.append("B")

    motor = MotorEventos()
    motor.adicionar_evento(0.1, evento1)
    motor.adicionar_evento(0.2, evento2)

    motor.iniciar()
    time.sleep(0.5)  # espera os eventos rodarem
    motor.parar()

    assert resultados == ["A", "B"]


def test_parar_motor():
    motor = MotorEventos()

    def evento():
        time.sleep(0.2)

    motor.adicionar_evento(0.1, evento)
    motor.iniciar()
    time.sleep(0.15)
    motor.parar()

    assert not motor.executando
