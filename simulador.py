# pip install pandapower pymodbus==3.6.6
import time
import threading
import pandapower as pp
import pandapower.networks as pn
from pymodbus.server.sync import StartTcpServer
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
from pymodbus.datastore import ModbusSequentialDataBlock
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.transaction import ModbusRtuFramer

# -------- Modelo elétrico (rede simples) --------
net = pp.create_empty_network()

b1 = pp.create_bus(net, vn_kv=13.8, name="BARRA1")
b2 = pp.create_bus(net, vn_kv=0.48, name="BARRA2")
ext = pp.create_ext_grid(net, bus=b1, vm_pu=1.0, name="FONTE")

trafo = pp.create_transformer_from_parameters(
    net, hv_bus=b1, lv_bus=b2, sn_mva=1.0, vn_hv_kv=13.8, vn_lv_kv=0.48,
    vkr_percent=1.0, vk_percent=6.0, pfe_kw=0.5, i0_percent=0.1, shift_degree=0, name="TR1"
)

line = pp.create_line_from_parameters(
    net, from_bus=b2, to_bus=b2, length_km=0.001, r_ohm_per_km=0.1,
    x_ohm_per_km=0.08, c_nf_per_km=0.0, max_i_ka=2.0, name="L1"
)
# Disjuntor como switch entre BARRA2 e carga (aqui simulando em série)
sw = pp.create_switch(net, bus=b2, element=line, et="l", closed=True, type="CB", name="DJ1")

load = pp.create_load(net, bus=b2, p_mw=0.3, q_mvar=0.05, name="CARGA1")

# -------- Tabela Modbus (endereços de exemplo) --------
# 40001: Vpu BARRA2 * 1000
# 40002: P_kW carga
# 40003: Q_kvar carga
# 00001: DJ1 estado (1=fechado, 0=aberto)
holding = ModbusSequentialDataBlock(1, [0]*100)   # 4xxxx
coils   = ModbusSequentialDataBlock(1, [1]*100)   # 0xxxx
slaves  = {0x01: ModbusSlaveContext(di=None, co=coils, hr=holding, ir=None, zero_mode=True)}
context = ModbusServerContext(slaves=slaves, single=False)

identity = ModbusDeviceIdentification()
identity.VendorName  = "SimuladorN1"
identity.ProductName = "PowerSim-Modbus"
identity.MajorMinorRevision = "0.1"

def servidor_modbus():
    StartTcpServer(context, identity=identity, address=("0.0.0.0", 5020))

# -------- Loop de simulação --------
def run_sim():
    while True:
        # aplica estado do DJ a partir da Coil 00001
        dj_cmd = context[0x01].getValues(1, 1, count=1)[0]  # coils
        net.switch.at[sw, "closed"] = bool(dj_cmd)

        # fluxo de potência
        pp.runpp(net)

        # coleta medidas
        v_pu = float(net.res_bus.vm_pu.at[b2])
        p_kw = float(net.res_load.p_mw.at[load]) * 1000.0
        q_kvar = float(net.res_load.q_mvar.at[load]) * 1000.0

        # escreve nos holding registers (escala simples)
        context[0x01].setValues(3, 1, [int(v_pu*1000)])
        context[0x01].setValues(3, 2, [int(p_kw)])
        context[0x01].setValues(3, 3, [int(q_kvar)])

        time.sleep(0.2)

if __name__ == "__main__":
    threading.Thread(target=servidor_modbus, daemon=True).start()
    run_sim()
