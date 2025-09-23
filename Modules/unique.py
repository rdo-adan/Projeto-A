# unique_sequence_aggregator.py
# unique.py --- This module aggregates unique sequences from JSON files into a consolidated JSON file
import sys
import importlib

# --- Importação da lista de bibliotecas do arquivo de configuração ---
try:
    # Certifique-se de que o caminho 'Install.Libs.LIB' reflete a estrutura de pastas correta
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
            # print(f"Biblioteca '{lib_name}' importada com sucesso.") # Comentado para evitar poluir o output principal
        except ImportError:
            print(f"Erro: Biblioteca '{lib_name}' não encontrada. Certifique-se de que está instalada.")
            imported_modules[lib_name] = None
        except Exception as e:
            print(f"Erro inesperado ao importar '{lib_name}': {e}")
            imported_modules[lib_name] = None
    return imported_modules

# --- Lógica para agregar sequências únicas ---
def aggregate_unique_sequences(input_directory="Collections/Sequences", output_file="unique_sequences.json", imported_modules=None):
    """
    Lê todos os arquivos JSON de um diretório, extrai sequências únicas
    e as salva em um único arquivo JSON consolidado.

    Args:
        input_directory (str): O diretório onde os arquivos JSON de sequências estão localizados.
        output_file (str): O caminho e nome do arquivo JSON de saída consolidado.
        imported_modules (dict): Dicionário de módulos importados dinamicamente ('json', 'os').
    """
    if imported_modules is None:
        print("Erro: Nenhum dicionário 'imported_modules' fornecido para 'aggregate_unique_sequences'.")
        print("Os módulos 'json' e 'os' são necessários para esta função.")
        return

    json_mod = imported_modules.get('json')
    os_mod = imported_modules.get('os')

    if not json_mod or not os_mod:
        print("Erro: Os módulos 'json' ou 'os' não estão disponíveis via 'imported_modules'. Não é possível prosseguir.")
        return

    unique_sequences = {}  # Usamos um dicionário para garantir unicidade pela sequência
    processed_files_count = 0

    print(f"Agregando sequências únicas do diretório: {input_directory}")

    if not os_mod.path.exists(input_directory):
        print(f"Erro: Diretório de entrada '{input_directory}' não encontrado.")
        return

    for filename in os_mod.listdir(input_directory):
        if filename.endswith(".json"):
            file_path = os_mod.path.join(input_directory, filename)
            try:
                with open(file_path, 'r') as f:
                    data = json_mod.load(f)
                    sequence = data.get("sequencia")
                    seq_id = data.get("id")
                    seq_len = data.get("tamanho") # Pega o tamanho se existir

                    if sequence:
                        # Usamos a sequência como chave para garantir unicidade
                        # E armazenamos os dados completos, ou apenas ID e tamanho para duplicatas
                        if sequence not in unique_sequences:
                            unique_sequences[sequence] = {
                                "id": seq_id,
                                "sequencia": sequence,
                                "tamanho": seq_len
                            }
                        # else:
                            # Opcional: registrar que uma duplicata foi encontrada
                            # print(f"Sequência duplicada encontrada (ID: {seq_id}), ignorando.")

                processed_files_count += 1
            except json_mod.JSONDecodeError:
                print(f"Aviso: Arquivo '{filename}' não é um JSON válido. Ignorando.")
            except Exception as e:
                print(f"Erro ao processar o arquivo '{filename}': {e}")

    # Convertendo o dicionário de sequências únicas de volta para uma lista de objetos
    # para salvá-lo no JSON final.
    final_unique_list = list(unique_sequences.values())

    print(f"Processados {processed_files_count} arquivos JSON.")
    print(f"Total de sequências únicas encontradas: {len(final_unique_list)}")

    try:
        with open(output_file, 'w') as out_f:
            json_mod.dump(final_unique_list, out_f, indent=4)
        print(f"Sequências únicas salvas com sucesso em '{output_file}'.")
    except Exception as e:
        print(f"Erro ao salvar o arquivo consolidado '{output_file}': {e}")

# As funções e a lista LIBRARIES são expostas para serem usadas pelo main.py