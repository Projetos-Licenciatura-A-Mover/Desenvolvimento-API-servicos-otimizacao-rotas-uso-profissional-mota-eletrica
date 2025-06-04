README

ESTRUTURA DO PROJETO

/RAIZ DO PROJETO
│
├── /API                   # pasta que contém a API (deve ser sempre colocada diretamente na raiz do projeto)
├── /logs                  # Logs de execução da API em conjunto com os algoritmos
├── /inputs                # Ficheiros de entrada da API
├── /outputs               # Ficheiros de saída da API
├── /docs                  # Documentação do projeto
│   └── README.txt         # instruções (ficheiro atual)
│
├── /algorithms            # pasta que contem os algoritmos desenvolvidos pelo colega a fazer projeto paralelo (deve ser sempre colocada na raiz do projeto)
│
├── filtro.py              # script de filtro (deve ser sempre colocada na raiz do projeto)

Detalhes das Pastas

1. `/API`

- Função: Contém a lógica de backend da aplicação, onde são definidos os endpoints da API, como o upload de ficheiros, processamento de dados e interação com a base de dados.
- Caminho relativo: `RAIZ_DO_PROJETO/API/`
- Observação: Esta pasta deve ser colocada diretamente na raiz do projeto, juntamente com as demais pastas e scripts.

2. `/logs`

- Função: Guarda os logs de execução da API e dos algoritmos. A cada execução, os detalhes do processamento e qualquer erro gerado são registrados aqui.
- Caminho relativo: `RAIZ_DO_PROJETO/logs/`
- Observação: O script irá criar a pasta `logs` caso ela não exista.

3. `/inputs`

- Função: Contém os ficheiros de entrada enviados para a API. Estes ficheiros devem ser JSON e passarão por um processo de validação e filtragem.
- Caminho relativo: `RAIZ_DO_PROJETO/inputs/`
- Observação: A pasta será criada automaticamente, caso não exista. Aqui, os ficheiros são armazenados temporariamente antes de serem processados.

4. `/outputs`

- Função: Armazena os ficheiros de saída gerados pelos algoritmos após o processamento dos dados de entrada.
- Caminho relativo: `RAIZ_DO_PROJETO/outputs/`
- Observação: Os resultados serão armazenados aqui após a execução dos algoritmos, com um formato JSON gerado pelo sistema.

5. `/docs`

- Função: Contém a documentação do projeto, incluindo este README.
- Caminho relativo: `RAIZ_DO_PROJETO/docs/`
- Observação: Não é necessário fazer alterações nesta pasta, exceto para documentações adicionais que possam ser necessárias.

6. `/algorithms`

- Função: Contém os scripts dos algoritmos que processam os dados (desenvolvidos pelo colega a fazer projeto paralelo). Cada algoritmo é responsável por calcular rotas, custos, e outros parâmetros conforme a lógica do projeto.
- Caminho relativo: `RAIZ_DO_PROJETO/algorithms/`
- Observação: Estes scripts são executados pelo `filtro.py`. O caminho para esta pasta deve ser mantido tal como está.

7. `filtro.py`

- Função: Realiza o pré-processamento dos dados, filtra os dados de entrada e executa os algoritmos com os dados filtrados. Os resultados são então armazenados na pasta `/outputs`.
- Caminho relativo: `RAIZ_DO_PROJETO/filtro.py`
- Observação: Este script também gera logs de execução em `/logs` e remove ficheiros temporários após a execução.


Tanto as pastas inputs, outputs e logs estão a ser criadas por paths relativos a um path absoluto definido no codigo views.py da API que deverá ser alterado conforme comentado no mesmo linhas 37 e 70, para o path da raiz do projeto mostrado na estrutura de pastas acima.
