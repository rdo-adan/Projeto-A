# Modules/sep.py
# sep.py --- This module handles the separation of FASTQ files into JSON format

import sys
import importlib

# --- Importação da lista de bibliotecas do arquivo de configuração ---
try:
    from Install.Libs.LIB import LIBRARIES
except ImportError:
    print("Erro: Não foi possível importar LIBRARIES do arquivo 'Install/Libs/LIB.py'.")
    print("Verifique se o arquivo existe e se a estrutura de pastas está correta.")
    print("Certifique-se também de que o diretório 'Install' está no Python Path ou")
    print("que você está executando o script de um local que permite a importação.")
    sys.exit(1)


def import_configured_libraries(library_list):
    """
    Importa bibliotecas dinamicamente a partir de uma lista Python.

    Args:
        library_list (list): Uma lista de strings com os nomes das bibliotecas.

    Returns:
        dict: Um dicionário onde as chaves são os nomes das bibliotecas e os valores
              são os módulos importados. Retorna None para módulos que falharam na importação.
    """
    imported_modules = {}
    for lib_name in library_list:
        try:
            modulo = importlib.import_module(lib_name)
            imported_modules[lib_name] = modulo
        except ImportError:
            print(f"Erro: Biblioteca '{lib_name}' não encontrada. Certifique-se de que está instalada.")
            imported_modules[lib_name] = None
        except Exception as e:
            print(f"Erro inesperado ao importar '{lib_name}': {e}")
            imported_modules[lib_name] = None
    return imported_modules

# --- Lógica central para processamento FASTA para JSONs individuais ---
def separate_fasta_to_json(fasta_file_path, output_directory="Collections/Sequences", imported_modules=None):
    """
    Lê um arquivo FASTA e salva cada sequência (ID, Sequência, Tamanho da Sequência)
    em um arquivo JSON separado dentro de um diretório especificado.

    Args:
        fasta_file_path (str): O caminho para o arquivo FASTA de entrada.
        diretorio_saida (str): O diretório onde os arquivos JSON serão salvos.
                                Será criado se não existir.
        imported_modules (dict): Um dicionário de módulos importados dinamicamente (e.g., {'json': json_module, 'os': os_module}).
    """
    if imported_modules is None:
        print("Erro: Nenhum dicionário 'imported_modules' fornecido para 'separate_fasta_to_json'.")
        print("Os módulos 'json' e 'os' são necessários para esta função.")
        return

    json_mod = imported_modules.get('json')
    os_mod = imported_modules.get('os')

    if not json_mod or not os_mod:
        print("Erro: Os módulos 'json' ou 'os' não estão disponíveis via 'imported_modules'. Não é possível prosseguir.")
        return

    # Cria o diretório de saída se ele não existir
    if not os_mod.path.exists(output_directory):
        os_mod.makedirs(output_directory)
        print(f"Diretório '{output_directory}' criado com sucesso para JSONs individuais.")

    contagem_sequencias = 0
    try:
        with open(fasta_file_path, 'r') as f:
            current_id = None
            current_sequence_lines = []

            for line in f:
                line = line.strip()
                if not line: # Ignora linhas vazias
                    continue

                if line.startswith('>'):
                    # Se já temos uma sequência acumulada, processe-a
                    if current_id is not None and current_sequence_lines:
                        sequence_str = "".join(current_sequence_lines)
                        process_and_save_sequence(current_id, sequence_str, output_directory, json_mod, os_mod)
                        contagem_sequencias += 1

                    # Inicia um novo registro FASTA
                    current_id = line.lstrip('>')
                    current_sequence_lines = []
                else:
                    # Acumula linhas da sequência
                    if current_id is not None:
                        current_sequence_lines.append(line)
                    # Caso contrário (linha de sequência sem ID anterior), ignora ou loga um erro
                    # Depende da robustez desejada
                    # print(f"Aviso: Linha de sequência sem ID anterior: {line}")


            # Processa a última sequência no arquivo, se houver
            if current_id is not None and current_sequence_lines:
                sequence_str = "".join(current_sequence_lines)
                process_and_save_sequence(current_id, sequence_str, output_directory, json_mod, os_mod)
                contagem_sequencias += 1

    except FileNotFoundError:
        print(f"Erro: Arquivo FASTA '{fasta_file_path}' não encontrado.")
        return
    except Exception as e:
        print(f"Ocorreu um erro inesperado ao processar o arquivo FASTA: {e}")
        return

    print(f"\nProcessamento concluído. {contagem_sequencias} sequências FASTA separadas em JSONs individuais em '{output_directory}'.")


def process_and_save_sequence(seq_id, sequence_str, output_directory, json_mod, os_mod):
    """Função auxiliar para processar e salvar uma única sequência."""
    tamanho_sequencia = len(sequence_str)

    dados_sequencia = {
        "ID": seq_id,
        "sequence": sequence_str,
        "Size": tamanho_sequencia
    }

    # Garante nomes de arquivo válidos, substituindo espaços, barras e pontos
    nome_arquivo_json = os_mod.path.join(
        output_directory,
        f"{seq_id.replace(' ', '_').replace('/', '_').replace('.', '_').replace('|', '_')}.json" # Adicionado replace para '|' comum em IDs FASTA
    )

    try:
        with open(nome_arquivo_json, 'w') as json_file:
            json_mod.dump(dados_sequencia, json_file, indent=4)
    except Exception as e:
        print(f"Erro ao salvar o arquivo JSON para o ID {seq_id}: {e}")

# A lista LIBRARIES e a função import_configured_libraries também são expostas