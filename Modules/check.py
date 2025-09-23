# Modules/check.py
# check.py --- This module checks the files submitted by the user and converts them to FASTA if needed.

def is_valid_sequence_file(file_path):
    """
    Verifica se um arquivo é um formato de sequência biológica válido (FASTA ou FASTQ).

    Args:
        file_path (str): O caminho para o arquivo a ser verificado.

    Returns:
        tuple: Uma tupla contendo (bool, str) onde:
               - O booleano indica se o arquivo é válido.
               - A string indica o formato detectado ('FASTA', 'FASTQ', ou 'Desconhecido').
    """
    try:
        with open(file_path, 'r') as f:
            lines = []
            # Lê as primeiras 5 linhas para verificar o formato
            for _ in range(5):
                line = f.readline().strip()
                if line:  # Ignora linhas vazias ao verificar
                    lines.append(line)

            if not lines:
                return False, "Arquivo vazio"

            # Verifica FASTA
            if lines[0].startswith('>'):
                # Para ser um FASTA válido, a segunda linha (se existir) não deve começar com '+' ou '@'
                if len(lines) > 1 and (lines[1].startswith('+') or lines[1].startswith('@')):
                     return False, "Possível formato misturado ou inválido para FASTA"
                return True, "FASTA"

            # Verifica FASTQ
            if lines[0].startswith('@'):
                if len(lines) >= 4:
                    if lines[2].startswith('+'):
                        f.seek(0)  # Volta ao início do arquivo para contar todas as linhas
                        all_lines = [line.strip() for line in f if line.strip()]
                        if len(all_lines) % 4 == 0:
                            return True, "FASTQ"
                        else:
                            return False, "FASTQ inválido (número de linhas não é múltiplo de 4)"
                    else:
                        return False, "FASTQ inválido (terceira linha não começa com '+')"
                else:
                    return False, "FASTQ inválido (poucas linhas para um bloco FASTQ)"

            return False, "Desconhecido"

    except FileNotFoundError:
        return False, "Arquivo não encontrado"
    except Exception as e:
        return False, f"Erro ao ler o arquivo: {e}"


def convert_to_fasta(input_file_path, output_dir, imported_modules):
    """
    Converte um arquivo FASTQ para FASTA, ou copia um arquivo FASTA existente
    para um diretório de saída especificado.

    Args:
        input_file_path (str): O caminho para o arquivo de sequência de entrada.
        output_dir (str): O diretório onde o arquivo FASTA resultante será salvo.
        imported_modules (dict): Dicionário de módulos importados dinamicamente ('os').

    Returns:
        str or None: O caminho para o arquivo FASTA de saída se a conversão/cópia for bem-sucedida,
                     caso contrário, None.
    """
    os_mod = imported_modules.get('os')
    if not os_mod:
        print("Erro: Módulo 'os' não disponível para convert_to_fasta. Não é possível prosseguir.")
        return None

    # Cria o diretório de saída se não existir
    if not os_mod.path.exists(output_dir):
        os_mod.makedirs(output_dir)
        print(f"Diretório '{output_dir}' criado com sucesso para arquivos FASTA processados.")

    is_valid, file_format = is_valid_sequence_file(input_file_path)

    if not is_valid:
        print(f"Erro: Arquivo '{input_file_path}' não é um formato de sequência válido ou não foi encontrado. Razão: {file_format}")
        return None

    base_name = os_mod.path.basename(input_file_path)
    output_fasta_name = os_mod.path.splitext(base_name)[0] + ".fasta"
    output_fasta_path = os_mod.path.join(output_dir, output_fasta_name)

    if file_format == "FASTA":
        print(f"Arquivo '{input_file_path}' já está no formato FASTA. Copiando para '{output_fasta_path}'.")
        try:
            with open(input_file_path, 'r') as infile, open(output_fasta_path, 'w') as outfile:
                outfile.write(infile.read())
            return output_fasta_path
        except Exception as e:
            print(f"Erro ao copiar arquivo FASTA: {e}")
            return None
    elif file_format == "FASTQ":
        print(f"Convertendo arquivo FASTQ '{input_file_path}' para FASTA em '{output_fasta_path}'.")
        try:
            with open(input_file_path, 'r') as fastq_file, open(output_fasta_path, 'w') as fasta_file:
                while True:
                    id_line = fastq_file.readline().strip()
                    if not id_line:
                        break # Fim do arquivo

                    sequence_line = fastq_file.readline().strip()
                    fastq_file.readline() # Pula a linha do separador '+'
                    fastq_file.readline() # Pula a linha do Q-score

                    # Remove o '@' inicial do ID e adiciona '>' para o formato FASTA
                    fasta_id = ">" + id_line.lstrip('@')
                    fasta_file.write(f"{fasta_id}\n{sequence_line}\n")
            return output_fasta_path
        except Exception as e:
            print(f"Erro ao converter FASTQ para FASTA: {e}")
            return None
    else:
        print(f"Formato de arquivo '{file_format}' não suportado para conversão para FASTA.")
        return None