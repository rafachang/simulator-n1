import json
import csv

with open("./docs/modelagem/pontos.json", "r", encoding="utf-8") as f:
    data = json.load(f)

with open("pontos.csv", "w", newline="", encoding="utf-8") as csvfile:
    writer = csv.writer(csvfile, delimiter=";")
    writer.writerow(["Equipamento", "Tag", "Tipo", "Unidade", "Descricao"])

    for eq, conteudo in data.items():
        for ponto in conteudo.get("Dados", []):
            if ponto:
                writer.writerow([eq, "ClassName", "Data", "", ponto["ClassName"]])
            else:
                writer.writerow([eq, "ClassName", "Data", "", ""])
        for ponto in conteudo.get("Analogicos", []):
            writer.writerow([eq, ponto["tag"], "Analog", ponto.get("unidade", ""), ponto["descricao"]])
        for ponto in conteudo.get("Discretos", []):
            writer.writerow([eq, ponto["tag"], "Digital", "", ponto["descricao"]])
        for ponto in conteudo.get("Comandos", []):
            writer.writerow([eq, ponto["tag"], "Command", "", ponto["descricao"]])
        for ponto in conteudo.get("Medicoes", []):
            writer.writerow([eq, ponto["tag"], "Measure", ponto.get("unidade", ""), ponto["descricao"]])
        for ponto in conteudo.get("Alarmes", []):
            writer.writerow([eq, ponto["tag"], "Alarm", "", ponto["descricao"]])
