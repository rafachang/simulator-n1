from typing import Optional

class Barra:
    """
    Representa um nó (barra) da rede elétrica.
    """

    def __init__(self, id: int, nome: str, vn_kv: float, tipo: str = "barras"):
        """
        :param id: Identificador único da barra
        :param nome: Nome ou identificador da barra
        :param vn_kv: Tensão nominal da barra em kV
        :param tipo: Tipo da barra (ex: 'bus', 'slack', 'pv')
        """
        self.id = int(id)
        self.nome = nome
        self.vn_kv = float(vn_kv)
        self.tipo = tipo

    def __repr__(self):
        return f"<Barra {self.nome} - {self.vn_kv} kV>"
    
class Linha:
    """
    Representa uma linha de transmissão ou distribuição entre duas barras.
    """

    def __init__(self, id: int, barra_origem: int, barra_destino: int, comprimento_km: float):
        """
        :param id: Identificador único da linha
        :param barra_origem: ID da barra de origem
        :param barra_destino: ID da barra de destino
        :param comprimento_km: Comprimento da linha em km
        """
        self.id = int(id)
        self.barra_origem = int(barra_origem)
        self.barra_destino = int(barra_destino)
        self.comprimento_km = float(comprimento_km)

    def __repr__(self):
        return f"<Linha {self.id} - {self.barra_origem} <-> {self.barra_destino} - {self.comprimento_km} km>"
    
class Carga:
    """
    Representa uma carga conectada a uma barra.
    """

    def __init__(self, id: int, barra_id: int, potencia_kw: float):
        """
        :param id: Identificador único da carga
        :param barra_id: ID da barra onde a carga está conectada
        :param potencia_kw: Potência da carga em kW
        """
        self.id = int(id)
        self.barra_id = int(barra_id)
        self.potencia_kw = float(potencia_kw)

    def __repr__(self):
        return f"<Carga {self.id} - Barra {self.barra_id} - {self.potencia_kw} kW>"

class Equipamento:
    """
    Representa um equipamento (ex: transformador, religador) conectado a uma barra.
    """

    def __init__(self, id: int, tipo: str, barra: int, parametros: Optional[dict] = None):
        """
        :param id: Identificador único do equipamento
        :param tipo: Tipo do equipamento (ex: 'transformador', 'religador')
        :param barra: ID da barra onde o equipamento está conectado
        :param parametros: Dicionário com parâmetros específicos do equipamento
        """
        self.id = int(id)
        self.tipo = tipo
        self.barra = int(barra)
        self.parametros = parametros or {}

    def __repr__(self):
        return f"<Equipamento {self.tipo} {self.id} - Barra {self.barra}>"