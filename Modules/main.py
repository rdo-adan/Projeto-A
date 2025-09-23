# Modules/main.py
# main.py

import sys
import os

# Adiciona o diretório pai (a raiz do projeto) ao Python Path
# Isso permite importar módulos como 'Install.Libs.LIB'
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

# Restante dos imports do seu main.py
from sep import LIBRARIES, import_configured_libraries, separate_fasta_to_json
from unique import aggregate_unique_sequences
from check import is_valid_sequence_file, convert_to_fasta

def main():
    """
    Função principal para orquestrar a importação de bibliotecas,
    a validação/conversão de arquivos, o processamento FASTA
    e a agregação de sequências únicas.
    """
    print("Iniciando a aplicação principal...")

    # 1. Importa as bibliotecas configuradas no LIB.py
    modules = import_configured_libraries(LIBRARIES)

    # 2. Verifica se os módulos essenciais (json, os) foram importados
    if modules.get('json') is None or modules.get('os') is None:
        print("Erro: As bibliotecas essenciais ('json' ou 'os') não puderam ser carregadas. Saindo.")
        sys.exit(1)

    # --- Seção de Validação e Conversão de Arquivo de Entrada ---
    # Definir o arquivo de entrada do usuário (pode ser FASTQ ou FASTA)
    print("Por favor, insira o caminho do arquivo de entrada (FASTA ou FASTQ):")
    user_input_file = input('') 

    # Diretório para salvar o arquivo FASTA processado/convertido
    processed_fasta_dir = "Processed_FASTA_Files"

    print(f"\n--- Verificando e convertendo arquivo de entrada: {user_input_file} ---")
    fasta_file_for_processing = convert_to_fasta(user_input_file, processed_fasta_dir, imported_modules=modules)

    if fasta_file_for_processing is None:
        print("Erro: Não foi possível obter um arquivo FASTA válido para processamento. Saindo.")
        sys.exit(1)

    # --- Seção de Processamento FASTA para JSONs Individuais ---
    output_sequences_dir = "Collections/Sequences" # Diretório de saída para JSONs individuais

    print(f"\n--- Separando o arquivo FASTA '{os.path.basename(fasta_file_for_processing)}' em JSONs individuais ---")
    # Agora chamamos a função que sabe lidar com FASTA!
    separate_fasta_to_json(fasta_file_for_processing, output_sequences_dir, imported_modules=modules)

    # --- Seção de Agregação de Sequências Únicas ---
    # O diretório de entrada para a agregação será o diretório onde os JSONs individuais
    # foram salvos, que é "Collections/Sequences".
    output_unique_dir = "Collections/Unique_S"
    # Certifica-se de que o diretório de saída para sequências únicas existe (já feito no `main.py` anterior)
    # mas para ser idempotente, mantemos a verificação aqui.
    if not os.path.exists(output_unique_dir):
        os.makedirs(output_unique_dir)
        print(f"Diretório '{output_unique_dir}' criado com sucesso para sequências únicas.")

    # Define o caminho completo do arquivo JSON consolidado
    output_unique_file = os.path.join(output_unique_dir, "unique_sequences.json")

    print(f"\n--- Agregando sequências únicas da pasta: {output_sequences_dir} ---")
    aggregate_unique_sequences(output_sequences_dir, output_unique_file, imported_modules=modules)

    print("\nAplicação concluída.")

if __name__ == "__main__":
    main()