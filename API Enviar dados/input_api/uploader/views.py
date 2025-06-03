import json
import psycopg2
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

# Configuração da base de dados Supabase (PostgreSQL)
DB_CONFIG = {
    'dbname': 'postgres',
    'user': 'postgres.dltmlxkjdrayavhhrebc',
    'password': '1Q_2w_3e_4r',
    'host': 'aws-0-eu-west-3.pooler.supabase.com',
    'port': '6543',
}

class UploadInputView(APIView):
    def post(self, request):
        print("DEBUG - request.FILES:", request.FILES)  # Para debugging

        # Garante que estamos a receber os ficheiros com o nome 'file'
        files = request.FILES.getlist('file')
        if not files:
            return Response({"error": "Nenhum ficheiro foi enviado no campo 'file'."}, status=400)

        inseridos = 0

        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()

            for f in files:
                try:
                    # Lê o conteúdo JSON
                    content_dict = json.load(f)
                    name = f.name
                    content_json = json.dumps(content_dict)

                    # Insere na base de dados
                    cursor.execute(
                        "INSERT INTO inputs (name, content) VALUES (%s, %s);",
                        (name, content_json)
                    )
                    inseridos += 1

                except json.JSONDecodeError as e:
                    conn.rollback()
                    return Response(
                        {"error": f"Ficheiro '{f.name}' não é um JSON válido: {e}"},
                        status=400
                    )
                except Exception as e:
                    conn.rollback()
                    return Response(
                        {"error": f"Erro ao processar o ficheiro '{f.name}': {e}"},
                        status=400
                    )

            conn.commit()
            cursor.close()
            conn.close()

            return Response(
                {"message": f"{inseridos} ficheiro(s) inserido(s) com sucesso."},
                status=201
            )

        except Exception as e:
            return Response(
                {"error": f"Erro ao ligar à base de dados: {e}"},
                status=500
            )
