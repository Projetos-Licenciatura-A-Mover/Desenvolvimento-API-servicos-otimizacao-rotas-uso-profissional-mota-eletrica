import json
import os
import subprocess
from datetime import datetime
import sys
import re

# Tabela de filtros
filtros_algoritmos = {
    "dijkstra": {
        "obrigatorio": ["nodes", "vehicles"],
        "opcional": ["start_id", "end_id", "is_charging_station", "charger_power_kw", "energy_matrix", "travel_time_matrix"]
    },
    "branch_and_bound": {
        "obrigatorio": ["nodes", "vehicles"],
        "opcional": ["demand", "time_window", "service_time", "energy_matrix", "travel_time_matrix"]
    },
    "savings": {
        "obrigatorio": ["nodes", "vehicles"],
        "opcional": ["demand", "time_window", "service_time", "energy_matrix", "travel_time_matrix"]
    },
    "nearest_neighbor": {
        "obrigatorio": ["nodes", "vehicles"],
        "opcional": ["demand", "time_window", "service_time", "energy_matrix", "travel_time_matrix"]
    },
    "tabu_search": {
        "obrigatorio": ["nodes", "vehicles"],
        "opcional": ["demand", "time_window", "service_time", "energy_matrix", "travel_time_matrix",
                     "start_id", "end_id", "is_charging_station", "charger_power_kw", "config"]
    },
    "grasp": {
        "obrigatorio": ["nodes", "vehicles"],
        "opcional": ["demand", "time_window", "service_time", "energy_matrix", "travel_time_matrix",
                     "start_id", "end_id", "is_charging_station", "charger_power_kw", "config"]
    }
}

def filtrar_para_algoritmos(json_entrada):
    resultado = {}
    for algoritmo, campos in filtros_algoritmos.items():
        dados = {}
        faltam = []

        for campo in campos["obrigatorio"]:
            if campo not in json_entrada or not json_entrada[campo]:
                faltam.append(campo)
            else:
                dados[campo] = json_entrada[campo]

        if faltam:
            print(f"[ERRO] {algoritmo}: faltam campos obrigatórios {faltam}")
            continue

        for campo in campos["opcional"]:
            if campo in json_entrada:
                dados[campo] = json_entrada[campo]

        resultado[algoritmo] = dados
    return resultado

def main():
    # Diretório dos scripts de algoritmos
    script_dir = "algorithms"

    # Os ficheiros a processar são passados como argumentos na linha de comando
    if len(sys.argv) < 2:
        print("Nenhum ficheiro de input especificado para processar.")
        exit(1)

    ficheiros_input = sys.argv[1:]

    # Diretórios na raiz do projeto
    input_dir = "inputs"
    output_dir = "outputs"
    log_dir = "logs"
    os.makedirs(input_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(log_dir, exist_ok=True)

    log_file = os.path.join(log_dir, "log_execucao.json")

    # Carregar log antigo (se existir)
    if os.path.exists(log_file):
        with open(log_file, "r", encoding="utf8") as f:
            logs_json = json.load(f)
    else:
        logs_json = []

    algoritmos = [
        "dijkstra.py",
        "branch_and_bound.py",
        "savings.py",
        "nearest_neighbor.py",
        "tabu_search.py",
        "grasp.py"
    ]

    for input_file in ficheiros_input:
        caminho = os.path.join(input_dir, input_file)
        if not os.path.exists(caminho):
            print(f"Ficheiro {input_file} não encontrado na pasta inputs/")
            continue

        print(f"\nA processar: {input_file}")

        try:
            with open(caminho, "r", encoding="utf8") as f:
                entrada = json.load(f)
        except Exception as e:
            print(f"Erro ao ler {input_file}: {e}")
            continue

        dados_filtrados = filtrar_para_algoritmos(entrada)
        resultados = {}

        base_name = os.path.splitext(input_file)[0]

        # Criar ficheiros de input por algoritmo com nomes únicos (na pasta inputs)
        for nome_alg, dados in dados_filtrados.items():
            nome_ficheiro = os.path.join(input_dir, f"{base_name}_{nome_alg}_input.json")
            with open(nome_ficheiro, "w", encoding="utf8") as f:
                json.dump(dados, f, indent=2)

        # Executar algoritmos e registar logs + outputs
        for script in algoritmos:
            nome_input_json = os.path.join(input_dir, f"{base_name}_{script.replace('.py','')}_input.json")
            script_path = os.path.join(script_dir, script)
            if os.path.exists(nome_input_json):
                print(f"A executar {script_path} com {nome_input_json}")
                result = subprocess.run(["python", script_path, nome_input_json], capture_output=True, text=True)
                resultados[script] = result.stdout.strip()

                agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                try:
                    with open(nome_input_json, "r", encoding="utf8") as input_f:
                        input_content = json.load(input_f)
                except:
                    input_content = {}

                logs_json.append({
                    "input_file": input_file,
                    "algoritmo": script,
                    "timestamp": agora,
                    "input": input_content,
                    "output": result.stdout.strip()
                })

        # 🔁 NOVO: converter resultados para lista com algoritmo, rota, custo
        resultados_lista = []
        for script, saida in resultados.items():
            nome_alg = script.replace(".py", "")
            rota_match = re.search(r"\[([0-9,\s]+)\]", saida)
            custo_match = re.search(r"(?i)(?:distância|custo|dist)[:\s]*([0-9.]+)|([0-9.]+)\s*km", saida)

            if rota_match and custo_match:
                rota_str = rota_match.group(1)
                rota = [int(x.strip()) for x in rota_str.split(",") if x.strip().isdigit()]
                custo = float(custo_match.group(1) or custo_match.group(2))
                resultados_lista.append({
                    "algoritmo": nome_alg,
                    "rota": rota,
                    "custo": custo
                })
            else:
                print(f"[AVISO] Não foi possível extrair rota/custo de {script}: {saida}")

        # Guardar output individual
        nome_output = f"output_{input_file}"
        caminho_output = os.path.join(output_dir, nome_output)
        with open(caminho_output, "w", encoding="utf8") as out:
            json.dump(resultados_lista, out, indent=2, ensure_ascii=False)
        print(f"Output guardado: {nome_output}")

        # Guardar log_execucao.json (sobrescreve para manter um único ficheiro)
        with open(log_file, "w", encoding="utf8") as f:
            json.dump(logs_json, f, indent=2, ensure_ascii=False)
        print(f"Log atualizado: {log_file}")

        # Limpeza de temporários - apagar só os criados para este input
        for script in algoritmos:
            nome_input_json = os.path.join(input_dir, f"{base_name}_{script.replace('.py','')}_input.json")
            if os.path.exists(nome_input_json):
                os.remove(nome_input_json)
                print(f"Removido temporário: {nome_input_json}")

        # Apagar input original
        if os.path.exists(caminho):
            os.remove(caminho)
            print(f"Input apagado: {input_file}")

if __name__ == "__main__":
    main()
