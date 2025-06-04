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

class UploadJSONView(APIView):

    def post(self, request):
        files = request.FILES.getlist('file')
        if not files:
            return Response({"error": "Nenhum ficheiro enviado."}, status=status.HTTP_400_BAD_REQUEST)

        script_dir = r'C:\Users\diogo\Desktop\Diogo\Utad\3º Ano\2º Semestre\Projeto\Final\Final'
        input_dir = os.path.join(script_dir, "inputs")
        output_dir = os.path.join(script_dir, "outputs")

        os.makedirs(input_dir, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)

        nomes_ficheiros_input = []

        for file in files:
            if not file.name.endswith('.json'):
                return Response({"error": "Apenas ficheiros .json são permitidos."}, status=status.HTTP_400_BAD_REQUEST)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            random_id = uuid.uuid4().hex[:6]
            input_filename = f"input_{timestamp}_{random_id}.json"
            input_path = os.path.join(input_dir, input_filename)
            with open(input_path, 'wb+') as destination:
                for chunk in file.chunks():
                    destination.write(chunk)
            nomes_ficheiros_input.append(input_filename)

        return self.process_files(nomes_ficheiros_input, script_dir, input_dir, output_dir)

    def get(self, request):
        script_dir = r'C:\Users\diogo\Desktop\Diogo\Utad\3º Ano\2º Semestre\Projeto\Final\Final'
        input_dir = os.path.join(script_dir, "inputs")
        output_dir = os.path.join(script_dir, "outputs")

        os.makedirs(input_dir, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)

        nomes_ficheiros_input = []

        try:
            conn = psycopg2.connect(
                dbname="postgres",
                user="postgres.dltmlxkjdrayavhhrebc",
                password="1Q_2w_3e_4r",
                host="aws-0-eu-west-3.pooler.supabase.com",
                port="5432"
            )
            cursor = conn.cursor()

            cursor.execute("SELECT id, name, content FROM inputs WHERE is_used = false")
            registos = cursor.fetchall()
            if not registos:
                return Response({"message": "Nenhum ficheiro por processar."}, status=204)

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
                conn.close()

        response = self.process_files(nomes_ficheiros_input, script_dir, input_dir, output_dir)
        return response

    def process_files(self, nomes_ficheiros_input, script_dir, input_dir, output_dir):
        cmd = ["python", "filtro.py"] + [n[0] if isinstance(n, tuple) else n for n in nomes_ficheiros_input]
        try:
            subprocess.run(cmd, cwd=script_dir, capture_output=True, text=True, check=True)
        except subprocess.CalledProcessError as e:
            return Response({"error": "Erro ao correr filtro.py", "detalhe": e.stderr}, status=500)

        try:
            conn = psycopg2.connect(
                dbname="postgres",
                user="postgres.dltmlxkjdrayavhhrebc",
                password="1Q_2w_3e_4r",
                host="aws-0-eu-west-3.pooler.supabase.com",
                port="6543"
            )
            cursor = conn.cursor()
        except Exception as e:
            return Response({"error": f"Erro a ligar à base de dados: {str(e)}"}, status=500)

        outputs_guardados = []
        inseridos = 0

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

                    if isinstance(conteudo, list):
                        for resultado in conteudo:
                            algorithm_name = resultado.get("algoritmo")
                            route = resultado.get("rota", [])
                            cost_raw = resultado.get("custo")
                            energia_raw = resultado.get("energia_estimada")

                            try:
                                cost = float(cost_raw)
                            except (TypeError, ValueError):
                                print(f"[ERRO] Valor inválido de custo: {cost_raw}")
                                continue

                            estimated_energy = None
                            try:
                                if energia_raw is not None:
                                    estimated_energy = float(energia_raw)
                            except (TypeError, ValueError):
                                print(f"[AVISO] Energia inválida: {energia_raw}")

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
                        print(f"[ERRO] Formato inválido no output: {nome_output_esperado}")

                    os.remove(out_path)
                    outputs_guardados.append(nome_output_esperado)

                except Exception as e:
                    print(f"[EXCEÇÃO] Ao processar {out_path}: {str(e)}")
                    continue

        conn.commit()
        cursor.close()
        conn.close()

        filtro_log_path = os.path.join(script_dir, "logs", "log_execucao.json")
        if os.path.exists(filtro_log_path):
            try:
                with open(filtro_log_path, "r", encoding="utf8") as f:
                    log_conteudo = json.load(f)

                conn_log = psycopg2.connect(
                    dbname="postgres",
                    user="postgres.dltmlxkjdrayavhhrebc",
                    password="1Q_2w_3e_4r",
                    host="aws-0-eu-west-3.pooler.supabase.com",
                    port="6543"
                )
                cursor_log = conn_log.cursor()

                cursor_log.execute("""
                    INSERT INTO execute_logs (id, log, atualizado_em)
                    VALUES (1, %s, NOW())
                    ON CONFLICT (id)
                    DO UPDATE SET log = EXCLUDED.log, atualizado_em = EXCLUDED.atualizado_em;
                """, [Json(log_conteudo)])

                conn_log.commit()
                cursor_log.close()
                conn_log.close()
            except Exception as e:
                print(f"[ERRO] Ao guardar o log na base de dados: {e}")

        return Response({
            "message": f"{inseridos} resultado(s) inserido(s) na base de dados com sucesso.",
            "ficheiros_upload": [n[0] if isinstance(n, tuple) else n for n in nomes_ficheiros_input],
            "outputs_processados": outputs_guardados
        }, status=status.HTTP_201_CREATED)
