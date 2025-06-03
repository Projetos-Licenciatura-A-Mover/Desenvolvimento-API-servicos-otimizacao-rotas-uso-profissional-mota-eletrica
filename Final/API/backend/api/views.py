import os
import json
import uuid
import shutil
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

        script_dir = r'C:\Users\diogo\Desktop\Diogo\Utad\3º Ano\2º Semestre\Projeto\Final\Final' #alterar dependendo do path que se quiser
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
        script_dir = r'C:\Users\diogo\Desktop\Diogo\Utad\3º Ano\2º Semestre\Projeto\Final\Final' #alterar dependendo do path que se quiser
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

            # ✅ MODO ATIVO: processar todos os inputs com is_used = false
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

            '''
            # 💤 MODO OPCIONAL: processar apenas 1 input por chamada
            cursor.execute("""
                SELECT id, name, content FROM inputs
                WHERE is_used = false
                ORDER BY created_at
                LIMIT 1
                FOR UPDATE SKIP LOCKED
            """)
            row = cursor.fetchone()
            if not row:
                return Response({"message": "Nenhum ficheiro por processar."}, status=204)

            db_id, name, content = row
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            random_id = uuid.uuid4().hex[:6]
            input_filename = f"input_{timestamp}_{random_id}.json"
            input_path = os.path.join(input_dir, input_filename)

            with open(input_path, 'w', encoding='utf8') as f:
                json.dump(content, f, ensure_ascii=False, indent=4)

            nomes_ficheiros_input.append((input_filename, db_id))

            # Marca como usado já
            cursor.execute("UPDATE inputs SET is_used = true WHERE id = %s", (db_id,))
            conn.commit()
            '''

        except Exception as e:
            return Response({"error": f"Erro ao aceder à base de dados: {str(e)}"}, status=500)
        finally:
            if conn:
                cursor.close()
                conn.close()

        nomes_ficheiros_simples = [n[0] for n in nomes_ficheiros_input]
        response = self.process_files(nomes_ficheiros_simples, script_dir, input_dir, output_dir)

        return response

    def process_files(self, nomes_ficheiros_input, script_dir, input_dir, output_dir):
        cmd = ["python", "filtro.py"] + nomes_ficheiros_input
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

        for f_input in nomes_ficheiros_input:
            nome_output_esperado = f"output_{f_input}"
            out_path = os.path.join(output_dir, nome_output_esperado)
            if os.path.exists(out_path):
                try:
                    with open(out_path, "r", encoding="utf8") as f:
                        conteudo = json.load(f)

                    print(f"[DEBUG] Output lido de {nome_output_esperado}: {conteudo}")

                    if isinstance(conteudo, list):
                        for entrada in conteudo:
                            algorithm_name = entrada.get("algoritmo")
                            route = entrada.get("rota", [])
                            cost_raw = entrada.get("custo")

                            try:
                                cost = float(cost_raw)
                            except (TypeError, ValueError):
                                print(f"[ERRO] Valor inválido de custo: {cost_raw}")
                                continue

                            if algorithm_name:
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

        # Guardar log_execucao.json diretamente na base de dados (overwrite)
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
            "ficheiros_upload": nomes_ficheiros_input,
            "outputs_processados": outputs_guardados
        }, status=status.HTTP_201_CREATED)
