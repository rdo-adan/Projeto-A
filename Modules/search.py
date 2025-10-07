# Modules/search.py

from Install.Libs.LIB import MODULES
os = MODULES["os"]
json = MODULES["json"]

import pandas as pd
import os
import json
import gzip
from collections import Counter

def smart_open(file_path):
    if file_path.lower().endswith('.gz'):
        return gzip.open(file_path, 'rt')
    else:
        return open(file_path, 'r')

def yield_sequences_from_file(file_path):
    """
    Gera todas as sequências de um arquivo FASTQ/FASTA (gz/plano).
    """
    try:
        with smart_open(file_path) as f:
            first = f.readline()
            if first.startswith('>'):
                # FASTA
                seq = ''
                for line in f:
                    line = line.strip()
                    if line.startswith('>'):
                        if seq:
                            yield seq
                        seq = ''
                    elif line:
                        seq += line
                if seq:
                    yield seq
            elif first.startswith('@'):
                # FASTQ
                while first:
                    seq_line = f.readline()
                    f.readline()  # +
                    f.readline()  # qualidade
                    if seq_line:
                        yield seq_line.strip()
                    first = f.readline()
    except Exception:
        pass

def blast_taxonomy_search_local(sequence, blast_db_path, max_hits=5, min_identity=80.0, parse_func=None):
    """
    Busca taxonomia via BLAST local para uma sequência; retorna string taxonômica.
    """
    import subprocess
    import tempfile
    
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.fasta', delete=False) as temp_fasta:
            temp_fasta.write(f">query_seq\n{sequence}\n")
            temp_fasta_path = temp_fasta.name
        
        blast_cmd = [
            "blastn",
            "-query", temp_fasta_path,
            "-db", blast_db_path,
            "-outfmt", "6 qseqid sseqid pident length mismatch gapopen qstart qend sstart send evalue bitscore stitle",
            "-max_target_seqs", str(max_hits),
            "-perc_identity", str(min_identity)
        ]
        
        result = subprocess.run(blast_cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode != 0:
            return "BLAST_Error"
        
        lines = result.stdout.strip().split('\n')
        if not lines or lines[0] == '':
            return "No_hit"
        
        # Pega o primeiro hit (maior score)
        best_line = lines[0].split('\t')
        if len(best_line) >= 13:
            identity = float(best_line[2])
            description = best_line[12]
            taxonomy = parse_func(description) if parse_func else parse_taxonomy_from_description(description)
            return f"{taxonomy} (ID: {identity:.1f}%)"
        
        return "Parse_Error"
        
    except Exception as e:
        return f"Error: {str(e)}"
    finally:
        try:
            os.unlink(temp_fasta_path)
        except:
            pass

def parse_taxonomy_from_description(description):
    if not description:
        return "Unknown"
    desc = description.lower()
    taxa_patterns = {
        'bacteria': ['bacteria', 'bacterial'],
        'archaea': ['archaea', 'archaeal'],
        'fungi': ['fungi', 'fungal'],
        'virus': ['virus', 'viral'],
        'plant': ['plant', 'plantae'],
        'animal': ['animal', 'animalia']
    }
    for taxa, patterns in taxa_patterns.items():
        for pattern in patterns:
            if pattern in desc:
                parts = description.split()
                if len(parts) >= 2:
                    organism = f"{parts[0]} {parts[1]}"
                    return f"{taxa.capitalize()}; {organism}"
                return taxa.capitalize()
    parts = description.split()
    if len(parts) >= 2:
        return f"Unknown; {parts[0]} {parts[1]}"
    return "Unknown"

def add_taxonomy_to_unique_jsons(unique_dir="assets/Collections/Unique", taxonomy_func=None):
    """
    Atualiza cada JSON de sequência única adicionando informação taxonômica (campo 'taxonomy').
    taxonomy_func deve ser uma função que recebe a sequência e retorna a string/classificação desejada.
    """
    for filename in os.listdir(unique_dir):
        if filename.endswith('.json'):
            path = os.path.join(unique_dir, filename)
            with open(path) as f:
                data = json.load(f)
            seq = data["sequence"]
            taxonomy = taxonomy_func(seq) if taxonomy_func else "Unknown_taxonomy"
            data["taxonomy"] = taxonomy
            with open(path, 'w') as f:
                json.dump(data, f, indent=4)
    print(f"[INFO] Taxonomia adicionada a todos os arquivos JSON únicos.")

def index_raw_sequences(amostra_dir):
    seqs = []
    for arquivo in os.listdir(amostra_dir):
        path = os.path.join(amostra_dir, arquivo)
        seqs.extend(list(yield_sequences_from_file(path)))
    return Counter(seqs)

def count_unique_sequences_in_raw_fast(unique_dir="assets/Collections/Unique", raw_dir="assets/Collections/Raw_sequences"):
    """
    Gera matriz abundância: sequências únicas x amostra; exporta para CSV e retorna DataFrame.
    """
    unique_files = [os.path.join(unique_dir, f) for f in os.listdir(unique_dir) if f.endswith('.json')]
    uniques = []
    for f in unique_files:
        with open(f) as jf:
            data = json.load(jf)
            uniques.append(data)
    amostras = sorted([d for d in os.listdir(raw_dir) if os.path.isdir(os.path.join(raw_dir, d))])
    amostra_counts = {amostra: index_raw_sequences(os.path.join(raw_dir, amostra)) for amostra in amostras}
    data_matrix = []
    for uq in uniques:
        row = {
            "taxonomy": uq.get("taxonomy"),
            "ID": uq.get("ID"),
            "sequence": uq.get("sequence")
        }
        seq = uq["sequence"]
        for amostra in amostras:
            row[amostra] = amostra_counts[amostra].get(seq, 0)
        data_matrix.append(row)
    df = pd.DataFrame(data_matrix)
    csv_path = os.path.join("assets", "Collections", "unique_occurrence_matrix.csv")
    df.to_csv(csv_path, index=False)
    print(f"[INFO] Matriz de abundância salva em: {csv_path}")
    return df
