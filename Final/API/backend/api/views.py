import os
import json
import uuid
import subprocess
import psycopg2
from psycopg2.extras import Json
from datetime import datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

# classe para fazer upload de ficheiros JSON
class UploadJSONView(APIView):

    # metodo POST para receber os ficheiros
    def post(self, request):
        # obtemos os ficheiros enviados pelo utilizador
        files = request.FILES.getlist('file')
        # verificamos se nao foi enviado nenhum ficheiro
        if not files:
            return Response({"error": "Nenhum ficheiro enviado."}, status=status.HTTP_400_BAD_REQUEST)

        # pastas onde vamos guardar os ficheiros de entrada e saida
        script_dir = r'C:\Users\diogo\Desktop\Diogo\Utad\3º Ano\2º Semestre\Projeto\Final\Final' #alterar sempre para a pasta RAIZ DO PROJETO (ver README)
        input_dir = os.path.join(script_dir, "inputs")
        output_dir = os.path.join(script_dir, "outputs")

        # criamos as pastas se nao existirem
        os.makedirs(input_dir, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)

        # lista para guardar os nomes dos ficheiros de entrada
        nomes_ficheiros_input = []

        # para cada ficheiro enviado
        for file in files:
            # verificamos se o ficheiro tem a extensao .json
            if not file.name.endswith('.json'):
                return Response({"error": "Apenas ficheiros .json sao permitidos."}, status=status.HTTP_400_BAD_REQUEST)
            
            # geramos um nome unico para o ficheiro
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            random_id = uuid.uuid4().hex[:6]
            input_filename = f"input_{timestamp}_{random_id}.json"
            input_path = os.path.join(input_dir, input_filename)
            
            # guardamos o ficheiro na pasta de inputs
            with open(input_path, 'wb+') as destination:
                for chunk in file.chunks():
                    destination.write(chunk)
            nomes_ficheiros_input.append(input_filename)

        # chamamos o metodo para processar os ficheiros
        return self.process_files(nomes_ficheiros_input, script_dir, input_dir, output_dir)

    # metodo GET para processar ficheiros na base de dados
    def get(self, request):
        # pastas onde vamos guardar os ficheiros de inputs e outputs
        script_dir = r'C:\Users\diogo\Desktop\Diogo\Utad\3º Ano\2º Semestre\Projeto\Final\Final'
        input_dir = os.path.join(script_dir, "inputs")
        output_dir = os.path.join(script_dir, "outputs")

        # criamos as pastas se nao existirem
        os.makedirs(input_dir, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)

        # lista para guardar os nomes dos ficheiros de entrada
        nomes_ficheiros_input = []

        try:
            # ligacao à base de dados
            conn = psycopg2.connect(
                dbname="postgres",
                user="postgres.dltmlxkjdrayavhhrebc",
                password="1Q_2w_3e_4r",
                host="aws-0-eu-west-3.pooler.supabase.com",
                port="5432"
            )
            cursor = conn.cursor()

            # selecionamos os ficheiros que ainda nao foram usados
            cursor.execute("SELECT id, name, content FROM inputs WHERE is_used = false")
            registos = cursor.fetchall()
            if not registos:
                return Response({"message": "Nenhum ficheiro por processar."}, status=204)

            # para cada registo, guardamos o conteudo num ficheiro
            for row in registos:
                db_id, name, content = row
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                random_id = uuid.uuid4().hex[:6]
                input_filename = f"input_{timestamp}_{random_id}.json"
                input_path = os.path.join(input_dir, input_filename)

                with open(input_path, 'w', encoding='utf8') as f:
                    json.dump(content, f, ensure_ascii=False, indent=4)

                nomes_ficheiros_input.append((input_filename, db_id))
                cursor.execute("UPDATE inputs SET is_used = true WHERE id = %s", (db_id,))

            conn.commit()

        except Exception as e:
            return Response({"error": f"Erro ao aceder à base de dados: {str(e)}"}, status=500)
        finally:
            if conn:
                cursor.close()

        # chamamos o metodo para processar os ficheiros
        response = self.process_files(nomes_ficheiros_input, script_dir, input_dir, output_dir, conn)
        return response

    # metodo para processar os ficheiros
    def process_files(self, nomes_ficheiros_input, script_dir, input_dir, output_dir, conn):
        # chamamos o script filtro.py para processar os ficheiros
        cmd = ["python", "filtro.py"] + [n[0] if isinstance(n, tuple) else n for n in nomes_ficheiros_input]
        try:
            subprocess.run(cmd, cwd=script_dir, capture_output=True, text=True, check=True)
        except subprocess.CalledProcessError as e:
            return Response({"error": "Erro ao correr filtro.py", "detalhe": e.stderr}, status=500)

        cursor = conn.cursor()

        # lista para guardar os outputs processados
        outputs_guardados = []
        inseridos = 0

        # para cada ficheiro de entrada, processamos o output
        for entrada in nomes_ficheiros_input:
            if isinstance(entrada, tuple):
                f_input, input_id = entrada
            else:
                f_input = entrada
                input_id = None

            nome_output_esperado = f"output_{f_input}"
            out_path = os.path.join(output_dir, nome_output_esperado)
            if os.path.exists(out_path):
                try:
                    with open(out_path, "r", encoding="utf8") as f:
                        conteudo = json.load(f)

                    print(f"[DEBUG] Output lido de {nome_output_esperado}: {conteudo}")

                    # verificamos se o conteudo do output esta no formato esperado
                    if isinstance(conteudo, list):
                        for resultado in conteudo:
                            algorithm_name = resultado.get("algoritmo")
                            route = resultado.get("rota", [])
                            cost_raw = resultado.get("custo")
                            energia_raw = resultado.get("energia_estimada")

                            try:
                                cost = float(cost_raw)
                            except (TypeError, ValueError):
                                print(f"[ERRO] Valor invalido de custo: {cost_raw}")
                                continue

                            estimated_energy = None
                            try:
                                if energia_raw is not None:
                                    estimated_energy = float(energia_raw)
                            except (TypeError, ValueError):
                                print(f"[AVISO] Energia invalida: {energia_raw}")

                            if algorithm_name:
                                if input_id is not None:
                                    if estimated_energy is not None:
                                        cursor.execute(
                                            """
                                            INSERT INTO results (file_output, algorithm_name, route, cost, input_id, estimated_energy)
                                            VALUES (%s, %s, %s, %s, %s, %s)
                                            """,
                                            (nome_output_esperado, algorithm_name, Json(route), cost, input_id, estimated_energy)
                                        )
                                    else:
                                        cursor.execute(
                                            """
                                            INSERT INTO results (file_output, algorithm_name, route, cost, input_id)
                                            VALUES (%s, %s, %s, %s, %s)
                                            """,
                                            (nome_output_esperado, algorithm_name, Json(route), cost, input_id)
                                        )
                                else:
                                    if estimated_energy is not None:
                                        cursor.execute(
                                            """
                                            INSERT INTO results (file_output, algorithm_name, route, cost, estimated_energy)
                                            VALUES (%s, %s, %s, %s, %s)
                                            """,
                                            (nome_output_esperado, algorithm_name, Json(route), cost, estimated_energy)
                                        )
                                    else:
                                        cursor.execute(
                                            """
                                            INSERT INTO results (file_output, algorithm_name, route, cost)
                                            VALUES (%s, %s, %s, %s)
                                            """,
                                            (nome_output_esperado, algorithm_name, Json(route), cost)
                                        )
                                inseridos += 1
                    else:
                        print(f"[ERRO] Formato invalido no output: {nome_output_esperado}")

                    os.remove(out_path)
                    outputs_guardados.append(nome_output_esperado)

                except Exception as e:
                    print(f"[EXCECAO] Ao processar {out_path}: {str(e)}")
                    continue

        conn.commit()

        # processamos os logs do filtro
        filtro_log_path = os.path.join(script_dir, "logs", "log_execucao.json")
        if os.path.exists(filtro_log_path):
            try:
                with open(filtro_log_path, "r", encoding="utf8") as f:
                    log_conteudo = json.load(f)

                cursor_log = conn.cursor()

                cursor_log.execute(""" 
                    INSERT INTO execute_logs (id, log, atualizado_em)
                    VALUES (1, %s, NOW())
                    ON CONFLICT (id)
                    DO UPDATE SET log = EXCLUDED.log, atualizado_em = EXCLUDED.atualizado_em;
                """, [Json(log_conteudo)])

                conn.commit()
                cursor_log.close()
            except Exception as e:
                print(f"[ERRO] Ao guardar o log na base de dados: {e}")

        cursor.close()

        # resposta com os resultados do processamento
        return Response({
            "message": f"{inseridos} resultado(s) inserido(s) na base de dados com sucesso.",
            "ficheiros_upload": [n[0] if isinstance(n, tuple) else n for n in nomes_ficheiros_input],
            "outputs_processados": outputs_guardados #mostra na consola os outputs para debug facilitado
        }, status=status.HTTP_201_CREATED)
