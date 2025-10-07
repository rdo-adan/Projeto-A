# Modules/unique.py

from Install.Libs.LIB import MODULES
os = MODULES["os"]
json = MODULES["json"]

def aggregate_unique_sequences(input_directory="assets/Collections/Sequences_cleaned", output_directory="assets/Collections/Unique", imported_modules=None):
    """
    Lê todos os arquivos JSON de sequências limpas (recursivo em subdiretórios),
    agrega apenas sequências únicas e salva CADA SEQUÊNCIA ÚNICA em arquivo JSON separado
    em 'output_directory'.

    Args:
        input_directory (str): Diretório raiz com arquivos JSON das sequências limpas (por amostra).
        output_directory (str): Diretório onde cada sequência única será salva como arquivo JSON individual.
        imported_modules (dict): Dicionário de módulos, se diferente do padrão.
    """
    if imported_modules is not None:
        os_mod = imported_modules.get("os")
        json_mod = imported_modules.get("json")
    else:
        os_mod = os
        json_mod = json

    unique_sequences = {}
    processed_files_count = 0
    
    # Cria diretório de saída se não existir
    if not os_mod.path.exists(output_directory):
        os_mod.makedirs(output_directory)

    print(f"Agregando sequências únicas (polidas) do diretório: {input_directory}")

    # Busca recursiva em todos subdiretórios
    for root, dirs, files in os_mod.walk(input_directory):
        for filename in files:
            if filename.endswith(".json"):
                file_path = os_mod.path.join(root, filename)
                try:
                    with open(file_path, 'r') as f:
                        data = json_mod.load(f)
                        sequence = data.get("sequence")
                        seq_id = data.get("ID")
                        seq_len = data.get("size")
                        sample_name = data.get("sample_name")
                        # Garante unicidade pela sequência
                        if sequence and sequence not in unique_sequences:
                            unique_sequences[sequence] = {
                                "ID": seq_id,
                                "sequence": sequence,
                                "size": seq_len,
                                "sample_name": sample_name
                            }
                    processed_files_count += 1
                except json_mod.JSONDecodeError:
                    print(f"Aviso: Arquivo '{filename}' não é um JSON válido. Ignorando.")
                except Exception as e:
                    print(f"Erro ao processar '{filename}': {e}")

    # Salva cada sequência única em arquivo JSON separado
    unique_count = 0
    for idx, (sequence, data) in enumerate(unique_sequences.items()):
        safe_id = "".join([c if c.isalnum() else "_" for c in data["ID"]])
        json_filename = f"unique_{safe_id}_{idx}.json"
        json_path = os_mod.path.join(output_directory, json_filename)
        try:
            with open(json_path, 'w') as out_f:
                json_mod.dump(data, out_f, indent=4)
            unique_count += 1
        except Exception as e:
            print(f"Erro ao salvar sequência única '{data['ID']}': {e}")

    print(f"Processados {processed_files_count} arquivos JSON.")
    print(f"Total de sequências únicas encontradas: {len(unique_sequences)}")
    print(f"Sequências únicas salvas individualmente em '{output_directory}': {unique_count} arquivos.")
