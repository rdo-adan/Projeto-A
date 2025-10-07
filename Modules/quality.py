# Modules/quality.py

"""
quality.py
Módulo para análise, extração e separação de sequências de arquivos FASTQ e FASTA.  
Inclui:
 - Score de qualidade por posição (média/mediana, para FASTQ)
 - Histograma da média de qualidade por leitura (para FASTQ)
 - Distribuição de tamanho das leituras
 - GC content por leitura
 - Distribuição de conteúdo das bases por posição
 - Extração/corte de sequências pelo score de qualidade (apenas para FASTQ)
 - Processamento de arquivos FASTA para JSONs individuais (sem scoring)
"""

from Install.Libs.LIB import MODULES
os = MODULES["os"]
json = MODULES["json"]

import numpy as np
import matplotlib.pyplot as plt
from collections import Counter
import gzip

def smart_open(file_path):
    """Abre arquivo texto padrão ou compactado (.gz) como texto."""
    if file_path.lower().endswith('.gz'):
        return gzip.open(file_path, 'rt')
    else:
        return open(file_path, 'r')

def extract_fastq_sequences_and_qualities_with_ids(fastq_file_path):
    """
    Extrai IDs, sequências e scores de qualidade de cada leitura do arquivo FASTQ (plano ou gz).
    Retorna: ids, sequences, quality_scores
    """
    ids = []
    sequences = []
    quality_scores = []
    try:
        with smart_open(fastq_file_path) as f:
            while True:
                id_line = f.readline()
                if not id_line:
                    break
                seq_line = f.readline()
                plus_line = f.readline()
                qual_line = f.readline()
                if not qual_line:
                    break
                ids.append(id_line.strip().lstrip('@').split()[0])
                sequences.append(seq_line.strip())
                scores = [ord(char) for char in qual_line.strip()]
                quality_scores.append(scores)
        return ids, sequences, quality_scores
    except Exception as e:
        print(f"Erro ao ler arquivo FASTQ: {e}")
        return [], [], []

def extract_fasta_sequences_with_ids(fasta_file_path):
    """
    Extrai IDs e sequências de arquivo FASTA (plano ou gz).
    Retorna: ids, sequences (sem scores de qualidade)
    """
    ids = []
    sequences = []
    try:
        with smart_open(fasta_file_path) as f:
            current_id = None
            current_sequence_lines = []
            for line in f:
                line = line.strip()
                if not line:
                    continue
                if line.startswith('>'):
                    if current_id is not None and current_sequence_lines:
                        sequence_str = "".join(current_sequence_lines)
                        ids.append(current_id)
                        sequences.append(sequence_str)
                    current_id = line.lstrip('>')
                    current_sequence_lines = []
                else:
                    if current_id is not None:
                        current_sequence_lines.append(line)
            if current_id is not None and current_sequence_lines:
                sequence_str = "".join(current_sequence_lines)
                ids.append(current_id)
                sequences.append(sequence_str)
        return ids, sequences
    except Exception as e:
        print(f"Erro ao ler arquivo FASTA: {e}")
        return [], []

def export_cut_sequences_to_json(ids, seqs, quality_scores, origem_fastq, output_dir=None, sample_name=None):
    """
    Exporta cada sequência filtrada de FASTQ para um arquivo JSON individual na pasta assets/Collections/Sequences_cleaned/{amostra},
    incluindo sample_name e nome claro do arquivo final.
    """
    assets_dir = os.path.join("assets", "Collections", "Sequences_cleaned")
    if not os.path.exists(assets_dir):
        os.makedirs(assets_dir)
    amostra_dir = os.path.join(assets_dir, sample_name if sample_name else "undefined_sample")
    if not os.path.exists(amostra_dir):
        os.makedirs(amostra_dir)
    for idx, (seq_id, seq, qs) in enumerate(zip(ids, seqs, quality_scores)):
        dados = {
            "ID": seq_id,
            "sample_name": sample_name,
            "sequence": seq,
            "quality": qs,
            "source_fastq": os.path.basename(origem_fastq),
            "size": len(seq)
        }
        safe_id = "".join([c if c.isalnum() else "_" for c in seq_id])
        json_file = os.path.join(
            amostra_dir,
            f"{sample_name}_{safe_id}_{idx}.json"
        )
        try:
            with open(json_file, "w") as jf:
                json.dump(dados, jf, indent=4)
        except Exception as e:
            print(f"Erro ao salvar JSON de {seq_id}: {e}")

def export_fasta_sequences_to_json(ids, seqs, origem_fasta, sample_name=None):
    """
    Exporta cada sequência FASTA para JSON individual em assets/Collections/Sequences_cleaned/{amostra}, sem scores de qualidade.
    """
    assets_dir = os.path.join("assets", "Collections", "Sequences_cleaned")
    if not os.path.exists(assets_dir):
        os.makedirs(assets_dir)
    amostra_dir = os.path.join(assets_dir, sample_name if sample_name else "undefined_sample")
    if not os.path.exists(amostra_dir):
        os.makedirs(amostra_dir)
    for idx, (seq_id, seq) in enumerate(zip(ids, seqs)):
        dados = {
            "ID": seq_id,
            "sample_name": sample_name,
            "sequence": seq,
            "size": len(seq),
            "source_fasta": os.path.basename(origem_fasta),
            "quality": None
        }
        safe_id = "".join([c if c.isalnum() else "_" for c in seq_id])
        json_file = os.path.join(
            amostra_dir,
            f"{sample_name}_{safe_id}_{idx}.json"
        )
        try:
            with open(json_file, "w") as jf:
                json.dump(dados, jf, indent=4)
        except Exception as e:
            print(f"Erro ao salvar JSON de {seq_id}: {e}")

def plot_per_base_quality(quality_scores):
    m = max(len(q) for q in quality_scores)
    arr = np.full((len(quality_scores), m), np.nan)
    for i, q in enumerate(quality_scores):
        arr[i, :len(q)] = q
    medias = np.nanmean(arr, axis=0)
    medianas = np.nanmedian(arr, axis=0)
    plt.figure(figsize=(12,6))
    plt.plot(medias, label='Média')
    plt.plot(medianas, label='Mediana')
    plt.title('Média e Mediana dos Scores de Qualidade por Posição')
    plt.xlabel('Posição na leitura')
    plt.ylabel('Score de Qualidade (ASCII)')
    plt.legend()
    plt.tight_layout()
    plt.show()

def plot_per_sequence_quality(quality_scores):
    medias_seq = [np.mean(q) for q in quality_scores if len(q) > 0]
    plt.figure(figsize=(8,5))
    plt.hist(medias_seq, bins=50, color='skyblue')
    plt.xlabel("Média da Qualidade por Leitura")
    plt.ylabel("Frequência")
    plt.title("Distribuição da Média dos Scores de Qualidade por Leitura")
    plt.tight_layout()
    plt.show()

def plot_read_length_distribution(quality_scores):
    tam = [len(q) for q in quality_scores]
    plt.figure(figsize=(8,5))
    plt.hist(tam, bins=50, color='orange')
    plt.xlabel("Tamanho da Leitura (bases)")
    plt.ylabel("Frequência")
    plt.title("Distribuição do Tamanho das Leituras")
    plt.tight_layout()
    plt.show()

def calc_gc_content(sequences):
    gc_percent = [100 * (s.upper().count('G') + s.upper().count('C')) / len(s) if len(s) > 0 else 0 for s in sequences]
    return gc_percent

def plot_gc_content(gc_percent):
    plt.figure(figsize=(8,5))
    plt.hist(gc_percent, bins=50, color='green')
    plt.xlabel("GC Content (%)")
    plt.ylabel("Frequência")
    plt.title("Distribuição de GC Content nas Leituras")
    plt.tight_layout()
    plt.show()

def plot_base_content_by_position(sequences):
    m = max(len(s) for s in sequences)
    contagens = {base: np.zeros(m) for base in 'ATCGN'}
    total_pos = np.zeros(m)
    for s in sequences:
        for i, base in enumerate(s.upper()):
            if base in contagens:
                contagens[base][i] += 1
            total_pos[i] += 1
    plt.figure(figsize=(14,7))
    for base in "ATCGN":
        porcentagem = (contagens[base] / total_pos) * 100
        plt.plot(porcentagem, label=f'%{base}')
    plt.title('Conteúdo Percentual de Bases por Posição')
    plt.xlabel('Posição na leitura')
    plt.ylabel('Porcentagem [%]')
    plt.legend()
    plt.tight_layout()
    plt.show()

class QualityCutter:
    """
    Armazena o valor de corte escolhido e permite cortar bases de baixa qualidade em cada leitura.
    """
    def __init__(self, thresholds=[10, 15, 20, 30]):
        self.thresholds = thresholds
        self.cutoff = None

    def analyze_and_set_cutoff(self, quality_scores):
        percent_per_cut = {}
        # Checa se todos os elementos de quality_scores são listas e têm o mesmo comprimento
        if not quality_scores or not isinstance(quality_scores, list) or not any([isinstance(q, list) and len(q) > 0 for q in quality_scores]):
            raise ValueError("quality_scores está vazio ou contém entradas inválidas/FASTAs.")

        comprimentos = set([len(q) for q in quality_scores if len(q) > 0])
        if len(comprimentos) > 1:
            # Reads de tamanhos diferentes (normal em FASTQ), montar array tipo "object" ou usar masked array
            arr = [np.array(q) for q in quality_scores if len(q) > 0]
        else:
            arr = np.array([np.array(q) for q in quality_scores if len(q) > 0])

        # O resto do seu código continua igual, só usar 'arr' como lista para média etc.

        for thresh in self.thresholds:
            passes = [np.all(q >= thresh) for q in arr]
            percent = 100 * np.sum(passes) / len(passes) if len(passes) > 0 else 0
            percent_per_cut[thresh] = percent
        all_scores = np.concatenate([q for q in quality_scores if len(q) > 0])
        mean_score = np.mean(all_scores)
        best_cut = self.thresholds[np.argmin([abs(mean_score - t) for t in self.thresholds])]
        self.cutoff = best_cut
        return {'percent_per_cut': percent_per_cut, 'suggested_cut': best_cut}

    def cut_low_quality_bases(self, seqs, quality_scores):
        if self.cutoff is None:
            raise ValueError("Cutoff não definido! Use analyze_and_set_cutoff primeiro.")
        seqs_filt, qs_filt = [], []
        for s, q in zip(seqs, quality_scores):
            s_new = ''.join([base for base, score in zip(s, q) if score >= self.cutoff])
            q_new = [score for score in q if score >= self.cutoff]
            if len(s_new) > 0:
                seqs_filt.append(s_new)
                qs_filt.append(q_new)
        return seqs_filt, qs_filt
