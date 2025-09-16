import time
import threading
from collections import deque

import matplotlib.pyplot as plt
import pandas as pd
import pandapower as pp
from pynput import keyboard
from pymodbus.datastore import ModbusSequentialDataBlock, ModbusSlaveContext, ModbusServerContext
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.server.sync import StartTcpServer

# =====================================
# Variável global para controlar o disjuntor
# =====================================
dj_status = True  # True = fechado, False = aberto


# =====================================
# Criação da rede N1
# =====================================
def create_network():
    """
    Cria a rede elétrica do simulador N1.
    Retorna a rede, barramento LV, disjuntor e carga.
    """
    net = pp.create_empty_network()

    # Barramentos
    b1 = pp.create_bus(net, vn_kv=13.8, name="BARRA1")
    b2 = pp.create_bus(net, vn_kv=0.48, name="BARRA2")

    # Rede externa
    pp.create_ext_grid(net, bus=b1, vm_pu=1.0, name="FONTE")

    # Transformador HV-LV
    pp.create_transformer_from_parameters(
        net,
        hv_bus=b1,
        lv_bus=b2,
        sn_mva=1.0,
        vn_hv_kv=13.8,
        vn_lv_kv=0.48,
        vkr_percent=1.0,
        vk_percent=6.0,
        pfe_kw=0.5,
        i0_percent=0.1,
        shift_degree=0,
        name="TR1",
    )

    # Linha curta
    line = pp.create_line_from_parameters(
        net,
        from_bus=b2,
        to_bus=b2,
        length_km=0.001,
        r_ohm_per_km=0.1,
        x_ohm_per_km=0.08,
        c_nf_per_km=0.0,
        max_i_ka=2.0,
        name="L1",
    )

    # Disjuntor
    sw = pp.create_switch(
        net, bus=b2, element=line, et="l", closed=True, type="CB", name="DJ1"
    )

    # Carga
    load = pp.create_load(net, bus=b2, p_mw=0.3, q_mvar=0.05, name="CARGA1")

    return net, b2, sw, load


# =====================================
# Setup do servidor Modbus
# =====================================
def setup_modbus():
    """
    Configura o servidor Modbus TCP.
    """
    holding = ModbusSequentialDataBlock(1, [0] * 100)
    coils = ModbusSequentialDataBlock(1, [1] * 100)

    slave_ctx = ModbusSlaveContext(di=None, co=coils, hr=holding, ir=None, zero_mode=True)
    context = ModbusServerContext(slaves={0x01: slave_ctx}, single=False)

    identity = ModbusDeviceIdentification()
    identity.VendorName = "SimuladorN1"
    identity.ProductName = "PowerSim-Modbus"
    identity.MajorMinorRevision = "0.3"

    return context, identity


# =====================================
# Thread do servidor Modbus
# =====================================
def modbus_server_thread(context, identity):
    """Inicia o servidor Modbus TCP"""
    StartTcpServer(context, identity=identity, address=("0.0.0.0", 5020))


# =====================================
# Função para teclado
# =====================================
def on_press(key):
    """
    Atualiza o estado do disjuntor com o teclado.
    'f' = fechar, 'o' = abrir.
    """
    global dj_status
    try:
        if key.char == "f":
            dj_status = True
            print("Disjuntor FECHADO")
        elif key.char == "o":
            dj_status = False
            print("Disjuntor ABERTO")
    except AttributeError:
        pass


# =====================================
# Loop de simulação interativo
# =====================================
def simulation_loop(net, b2, sw, load, context):
    """
    Loop de simulação com gráficos interativos e histórico.
    """
    global dj_status

    max_len = 50
    hist_time = deque(maxlen=max_len)
    hist_v = deque(maxlen=max_len)
    hist_p = deque(maxlen=max_len)
    hist_q = deque(maxlen=max_len)
    hist_dj = deque(maxlen=max_len)

    plt.ion()
    fig, ax = plt.subplots(4, 1, figsize=(8, 8))

    t_counter = 0
    while True:
        t_counter += 1

        # Atualiza o disjuntor
        net.switch.at[sw, "closed"] = dj_status

        # Roda load flow
        pp.runpp(net)

        # Resultados
        v_pu = net.res_bus.vm_pu.at[b2]
        p_kw = net.res_load.p_mw.at[load] * 1000.0
        q_kvar = net.res_load.q_mvar.at[load] * 1000.0

        # Atualiza registradores Modbus
        context[0x01].setValues(3, 1, [int(v_pu * 1000)])
        context[0x01].setValues(3, 2, [int(p_kw)])
        context[0x01].setValues(3, 3, [int(q_kvar)])
        context[0x01].setValues(1, 1, [int(dj_status)])

        # Logging
        print(
            f"[{t_counter}] Disjuntor: {'FECHADO' if dj_status else 'ABERTO'} | "
            f"V: {v_pu:.3f} pu | P: {p_kw:.1f} kW | Q: {q_kvar:.1f} kVar"
        )

        # Atualiza histórico
        hist_time.append(t_counter)
        hist_v.append(v_pu)
        hist_p.append(p_kw)
        hist_q.append(q_kvar)
        hist_dj.append(1 if dj_status else 0)

        # Atualiza gráficos
        ax[0].cla()
        ax[0].plot(hist_time, hist_v, "-o", color="blue")
        ax[0].set_ylabel("V (pu)")

        ax[1].cla()
        ax[1].plot(hist_time, hist_p, "-o", color="green")
        ax[1].set_ylabel("P (kW)")

        ax[2].cla()
        ax[2].plot(hist_time, hist_q, "-o", color="red")
        ax[2].set_ylabel("Q (kVar)")

        ax[3].cla()
        ax[3].plot(hist_time, hist_dj, "-o", color="black")
        ax[3].set_ylabel("Disjuntor")
        ax[3].set_xlabel("Ciclos")

        plt.pause(0.01)

        # Salva histórico
        df = pd.DataFrame(
            {"Ciclo": hist_time, "V_pu": hist_v, "P_kw": hist_p, "Q_kvar": hist_q, "Disjuntor": hist_dj}
        )
        df.to_csv("historico_n1_interativo.csv", index=False)

        time.sleep(0.2)


# =====================================
# Main
# =====================================
def main():
    global dj_status

    # Cria rede e Modbus
    net, b2, sw, load = create_network()
    context, identity = setup_modbus()

    # Inicia servidor Modbus
    threading.Thread(target=modbus_server_thread, args=(context, identity), daemon=True).start()

    # Inicia listener do teclado
    listener = keyboard.Listener(on_press=on_press)
    listener.start()

    # Inicia simulação
    simulation_loop(net, b2, sw, load, context)


if __name__ == "__main__":
    main()
