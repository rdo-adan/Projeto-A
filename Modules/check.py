# Modules/check.py
# check.py --- Funções para checagem e conversão de arquivos de sequência biológica.

import gzip

def smart_open(file_path):
    """
    Abre o arquivo em modo texto, usando gzip.open se for .gz, senão open normal.
    """
    if file_path.lower().endswith('.gz'):
        return gzip.open(file_path, 'rt')
    else:
        return open(file_path, 'r')

def is_valid_sequence_file(file_path):
    """
    Verifica se um arquivo é um formato de sequência biológica válido (FASTA ou FASTQ),
    incluindo arquivos compactados (.gz).

    Returns:
        tuple: (bool, str) — válido ou não, e o tipo/razão identificado.
    """
    try:
        with smart_open(file_path) as f:
            lines = []
            for _ in range(5):
                line = f.readline().strip()
                if line:
                    lines.append(line)
            if not lines:
                return False, "Arquivo vazio"
            # Verifica FASTA
            if lines[0].startswith('>'):
                if len(lines) > 1 and (lines[1].startswith('+') or lines[1].startswith('@')):
                    return False, "Possível formato misturado ou inválido para FASTA"
                return True, "FASTA"
            # Verifica FASTQ
            if lines[0].startswith('@'):
                if len(lines) >= 4:
                    if lines[2].startswith('+'):
                        try:
                            f.seek(0)
                            all_lines = [line.strip() for line in f if line.strip()]
                            if len(all_lines) % 4 == 0:
                                return True, "FASTQ"
                            else:
                                return False, "FASTQ inválido (linhas não múltiplo de 4)"
                        except Exception:
                            return True, "FASTQ (não checado número de linhas em arquivos compactados)"  # fallback seguro
                    else:
                        return False, "FASTQ inválido (terceira linha não começa com '+')"
                else:
                    return False, "FASTQ inválido (poucas linhas para bloco FASTQ)"
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
        input_file_path (str): Caminho do arquivo de entrada.
        output_dir (str): Diretório de saída.
        imported_modules (dict): Dicionário de módulos ('os').

    Returns:
        str or None: Caminho do arquivo FASTA de saída, ou None.
    """
    os_mod = imported_modules.get('os')
    if not os_mod:
        print("Erro: Módulo 'os' não disponível.")
        return None

    if not os_mod.path.exists(output_dir):
        os_mod.makedirs(output_dir)
        print(f"Diretório '{output_dir}' criado para arquivos FASTA processados.")

    is_valid, file_format = is_valid_sequence_file(input_file_path)
    if not is_valid:
        print(f"Erro: Arquivo '{input_file_path}' não é válido ou não foi encontrado. Razão: {file_format}")
        return None

    base_name = os_mod.path.basename(input_file_path)
    output_fasta_name = os_mod.path.splitext(base_name)[0] + ".fasta"
    output_fasta_path = os_mod.path.join(output_dir, output_fasta_name)

    try:
        with smart_open(input_file_path) as infile:
            if file_format == "FASTA":
                print(f"Arquivo '{input_file_path}' já está em formato FASTA. Copiando para '{output_fasta_path}'.")
                with open(output_fasta_path, 'w') as outfile:
                    outfile.write(infile.read())
                return output_fasta_path
            elif file_format == "FASTQ":
                print(f"Convertendo '{input_file_path}' para FASTA em '{output_fasta_path}'.")
                with open(output_fasta_path, 'w') as fasta_file:
                    while True:
                        id_line = infile.readline()
                        if not id_line:
                            break
                        sequence_line = infile.readline()
                        infile.readline()  # Pula linha '+'
                        infile.readline()  # Pula linha de qualidade
                        fasta_id = ">" + id_line.strip().lstrip('@')
                        fasta_file.write(f"{fasta_id}\n{sequence_line.strip()}\n")
                return output_fasta_path
            else:
                print(f"Formato '{file_format}' não suportado para conversão para FASTA.")
                return None
    except Exception as e:
        print(f"Erro ao processar arquivo: {e}")
        return None

def find_valid_fastq_files(input_path, accepted_exts=('.fastq', '.fq', '.fastq.gz')):
    """
    Busca e valida arquivos FASTQ e copia para assets/Collections/Raw_sequences/{amostra}/.
    - arquivo único
    - pasta de arquivos
    - pasta com subpastas (cada subpasta uma amostra)

    Returns:
        dict: {amostra_nome: [lista de arquivos válidos]}
    """
    import os
    import shutil

    def is_valid_fastq(file_path):
        valid, tipo = is_valid_sequence_file(file_path)
        return valid and tipo == "FASTQ"

    valid_files = {}
    # Pasta de destino dos arquivos validados
    raw_seq_root = os.path.join("assets", "Collections", "Raw_sequences")
    if not os.path.exists(raw_seq_root):
        os.makedirs(raw_seq_root)

    if os.path.isfile(input_path):
        if input_path.lower().endswith(accepted_exts) and is_valid_fastq(input_path):
            amostra = os.path.splitext(os.path.basename(input_path))[0]
            valid_files[amostra] = [input_path]

            # Copia para Raw_sequences/amostra/
            dest_dir = os.path.join(raw_seq_root, amostra)
            os.makedirs(dest_dir, exist_ok=True)
            shutil.copy2(input_path, dest_dir)
            return valid_files

    elif os.path.isdir(input_path):
        arquivos = [os.path.join(input_path, f) for f in os.listdir(input_path)
                    if os.path.isfile(os.path.join(input_path, f)) and f.lower().endswith(accepted_exts)]
        valid_arquivos = [f for f in arquivos if is_valid_fastq(f)]
        if valid_arquivos:
            amostra = os.path.basename(input_path)
            valid_files[amostra] = valid_arquivos
            dest_dir = os.path.join(raw_seq_root, amostra)
            os.makedirs(dest_dir, exist_ok=True)
            for arquivo in valid_arquivos:
                shutil.copy2(arquivo, dest_dir)

        subpastas = [os.path.join(input_path, d) for d in os.listdir(input_path)
                     if os.path.isdir(os.path.join(input_path, d))]
        for sp in subpastas:
            arquivos_sp = [os.path.join(sp, f) for f in os.listdir(sp)
                           if os.path.isfile(os.path.join(sp, f)) and f.lower().endswith(accepted_exts)]
            valid_arquivos_sp = [f for f in arquivos_sp if is_valid_fastq(f)]
            if valid_arquivos_sp:
                amostra_sp = os.path.basename(sp)
                valid_files[amostra_sp] = valid_arquivos_sp
                dest_dir = os.path.join(raw_seq_root, amostra_sp)
                os.makedirs(dest_dir, exist_ok=True)
                for arquivo in valid_arquivos_sp:
                    shutil.copy2(arquivo, dest_dir)
    return valid_files
