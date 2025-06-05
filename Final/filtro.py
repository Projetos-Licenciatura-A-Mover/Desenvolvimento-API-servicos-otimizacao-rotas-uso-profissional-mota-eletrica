import json
import os
import subprocess
from datetime import datetime
import sys
import re

# tabela de filtros para cada algoritmo
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

# funcao para filtrar os dados de entrada de acordo com os algoritmos
def filtrar_para_algoritmos(json_entrada):
    resultado = {}
    for algoritmo, campos in filtros_algoritmos.items():
        dados = {}
        faltam = []

        # verifica se todos os campos obrigatorios estao presentes
        for campo in campos["obrigatorio"]:
            if campo not in json_entrada or not json_entrada[campo]:
                faltam.append(campo)
            else:
                dados[campo] = json_entrada[campo]

        if faltam:
            print(f"[ERRO] {algoritmo}: faltam campos obrigatorios {faltam}")
            continue

        # adiciona os campos opcionais se existirem
        for campo in campos["opcional"]:
            if campo in json_entrada:
                dados[campo] = json_entrada[campo]

        resultado[algoritmo] = dados
    return resultado

# funcao principal
def main():
    script_dir = "algorithms"  # path onde os scripts dos algoritmos estao

    # verifica se foi especificado pelo menos um ficheiro de entrada
    if len(sys.argv) < 2:
        print("Nenhum ficheiro de input especificado para processar.")
        exit(1)

    ficheiros_input = sys.argv[1:]  # lista de ficheiros de entrada

    input_dir = "inputs"
    output_dir = "outputs"
    log_dir = "logs"
    os.makedirs(input_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(log_dir, exist_ok=True)

    # arquivo de log da execucao
    log_file = os.path.join(log_dir, "log_execucao.json")
    if os.path.exists(log_file):
        with open(log_file, "r", encoding="utf8") as f:
            logs_json = json.load(f)
    else:
        logs_json = []

    # lista de algoritmos a serem executados
    algoritmos = [
        "dijkstra.py",
        "branch_and_bound.py",
        "savings.py",
        "nearest_neighbor.py",
        "tabu_search.py",
        "grasp.py"
    ]

    # loop para processar cada ficheiro de input
    for input_file in ficheiros_input:
        caminho = os.path.join(input_dir, input_file)
        if not os.path.exists(caminho):
            print(f"Ficheiro {input_file} nao encontrado na pasta inputs/")
            continue

        print(f"\nA processar: {input_file}")
        try:
            with open(caminho, "r", encoding="utf8") as f:
                entrada = json.load(f)
        except Exception as e:
            print(f"Erro ao ler {input_file}: {e}")
            continue

        # filtra os dados de entrada de acordo com os algoritmos
        dados_filtrados = filtrar_para_algoritmos(entrada)
        resultados = {}
        base_name = os.path.splitext(input_file)[0]

        # guarda os dados filtrados para cada algoritmo
        for nome_alg, dados in dados_filtrados.items():
            nome_ficheiro = os.path.join(input_dir, f"{base_name}_{nome_alg}_input.json")
            with open(nome_ficheiro, "w", encoding="utf8") as f:
                json.dump(dados, f, indent=2)

        # executa os algoritmos e coleta os resultados
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

                # adiciona entrada no log com os detalhes da execucao
                logs_json.append({
                    "input_file": input_file,
                    "algoritmo": script,
                    "timestamp": agora,
                    "input": input_content,
                    "output": result.stdout.strip()
                })

        # organiza os resultados dos algoritmos
        resultados_lista = []
        for script, saida in resultados.items():
            nome_alg = script.replace(".py", "")
            rota_match = re.search(r"\[([0-9,\s]+)\]", saida)
            custo_match = re.search(r"(?i)(?:distancia|distância|custo|dist)[:\s]*([0-9.]+)|([0-9.]+)\s*km", saida)
            energia_match = re.search(r"energia estimada[:\s]*([0-9.]+)", saida, re.IGNORECASE)

            # extrai rota, custo e energia se encontrados
            if rota_match and custo_match:
                rota_str = rota_match.group(1)
                rota = [int(x.strip()) for x in rota_str.split(",") if x.strip().isdigit()]
                custo = float(custo_match.group(1) or custo_match.group(2))
                entrada_resultado = {
                    "algoritmo": nome_alg,
                    "rota": rota,
                    "custo": custo
                }

                # se energia estimada for encontrada, adiciona ao resultado
                if energia_match:
                    entrada_resultado["energia_estimada"] = float(energia_match.group(1))

                resultados_lista.append(entrada_resultado)
            else:
                print(f"[AVISO] Não foi possível extrair rota/custo de {script}: {saida}")

        # guarda os resultados num ficheiro de output
        nome_output = f"output_{input_file}"
        caminho_output = os.path.join(output_dir, nome_output)
        with open(caminho_output, "w", encoding="utf8") as out:
            json.dump(resultados_lista, out, indent=2, ensure_ascii=False)
        print(f"Output guardado: {nome_output}")

        # atualiza o log com os novos resultados
        with open(log_file, "w", encoding="utf8") as f:
            json.dump(logs_json, f, indent=2, ensure_ascii=False)
        print(f"Log atualizado: {log_file}")

        # remove os ficheiros temporarios gerados
        for script in algoritmos:
            nome_input_json = os.path.join(input_dir, f"{base_name}_{script.replace('.py','')}_input.json")
            if os.path.exists(nome_input_json):
                os.remove(nome_input_json)
                print(f"Removido temporario: {nome_input_json}")

        # remove o ficheiro de entrada processado
        if os.path.exists(caminho):
            os.remove(caminho)
            print(f"Input apagado: {input_file}")

# executa a funcao principal
if __name__ == "__main__":
    main()
