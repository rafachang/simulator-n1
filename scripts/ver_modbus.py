from pymodbus.client.sync import ModbusTcpClient
import time

# Configurações do servidor
IP = "127.0.0.1"  # ou o IP do PC que roda o servidor
PORT = 5020
UNIT = 1  # Slave ID

client = ModbusTcpClient(IP, port=PORT)
client.connect()

try:
    while True:
        # Lê tensão e potência nos holding registers 40001, 40002, 40003
        rr = client.read_holding_registers(1, 3, unit=UNIT)
        if rr.isError():
            print("Erro ao ler registradores")
        else:
            v_pu = rr.registers[0] / 1000.0
            p_kw = rr.registers[1]
            q_kvar = rr.registers[2]
            print(f"Tensão: {v_pu:.3f} pu | P: {p_kw} kW | Q: {q_kvar} kVar")

        # Exemplo: alternar disjuntor a cada 5 segundos
        # Lê coil 00001
        coil_status = client.read_coils(1, 1, unit=UNIT).bits[0]
        client.write_coil(1, not coil_status, unit=UNIT)
        print(f"Disjuntor {'FECHADO' if not coil_status else 'ABERTO'}")

        time.sleep(5)

except KeyboardInterrupt:
    print("Encerrando teste...")

finally:
    client.close()
