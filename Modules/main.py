from Install.Libs.LIB import MODULES
os = MODULES["os"]
json = MODULES["json"]
import sys

from Modules.check import find_valid_fastq_files
from Modules.quality import (
    extract_fastq_sequences_and_qualities_with_ids,
    extract_fasta_sequences_with_ids,
    QualityCutter,
    export_cut_sequences_to_json,
    export_fasta_sequences_to_json,
)
from Modules.unique import aggregate_unique_sequences
from Modules.search import (
    add_taxonomy_to_unique_jsons,
    count_unique_sequences_in_raw_fast,
    blast_taxonomy_search_local,
    parse_taxonomy_from_description,
)

def main():
    # --- INPUT/VALIDAÇÃO ---
    input_path = sys.argv[1] if len(sys.argv) > 1 else input(
        "\nInforme o caminho do arquivo, pasta ou pasta com subpastas de arquivos FASTQ/FASTA: ").strip()
    _ = find_valid_fastq_files(input_path)  # Copia arquivos válidos para Raw_sequences

    # --- LIMPEZA/EXPORTAÇÃO ---
    raw_sequences_root = os.path.join("assets", "Collections", "Raw_sequences")
    for amostra in os.listdir(raw_sequences_root):
        amostra_dir = os.path.join(raw_sequences_root, amostra)
        if not os.path.isdir(amostra_dir):
            continue
        for arquivo in os.listdir(amostra_dir):
            input_file = os.path.join(amostra_dir, arquivo)
            if arquivo.lower().endswith(('.fasta', '.fa')):
                # Apenas extração e exportação, sem corte de qualidade!
                ids, seqs = extract_fasta_sequences_with_ids(input_file)
                export_fasta_sequences_to_json(ids, seqs, input_file, sample_name=amostra)
            elif arquivo.lower().endswith(('.fastq', '.fq', '.fastq.gz')):
                ids, seqs, qs = extract_fastq_sequences_and_qualities_with_ids(input_file)
                # Se não houver scores (para garantir robustez)
                if not qs or not isinstance(qs[0], list) or qs[0] is None:
                    print(f"[INFO] Pulando corte de qualidade: {arquivo} não contém scores válidos.")
                    continue
                cutter = QualityCutter()
                try:
                    cutter.analyze_and_set_cutoff(qs)
                except Exception as e:
                    print(f"[ERRO] Corte de qualidade falhou para {arquivo}: {str(e)} – Pulando este arquivo.")
                    continue
                seqs_filt, qs_filt = cutter.cut_low_quality_bases(seqs, qs)
                ids_filt = [
                    i for i, s, q in zip(ids, seqs, qs)
                    if len(''.join([base for base, score in zip(s, q) if score >= cutter.cutoff])) > 0
                ]
                export_cut_sequences_to_json(ids_filt, seqs_filt, qs_filt, input_file, output_dir=None, sample_name=amostra)

    # --- AGREGAÇÃO DE SEQUÊNCIAS ÚNICAS ---
    aggregate_unique_sequences(
        input_directory="assets/Collections/Sequences_cleaned",
        output_directory="assets/Collections/Unique"
    )

    # --- BUSCA TAXONÔMICA ---
    blast_db_path = "/caminho/para/seu/banco"  # Ajuste conforme seu sistema!
    add_taxonomy_to_unique_jsons(
        unique_dir="assets/Collections/Unique",
        taxonomy_func=lambda seq: blast_taxonomy_search_local(seq, blast_db_path, parse_func=parse_taxonomy_from_description)
    )

    # --- MATRIZ/CONTAGEM DE ABUNDÂNCIA ---
    df_abundancia = count_unique_sequences_in_raw_fast(
        unique_dir="assets/Collections/Unique",
        raw_dir="assets/Collections/Raw_sequences"
    )

    print(f"\n[SUCCESS] Pipeline completo: dados organizados, limpos, únicas salvas, taxonomia atribuída, matriz de abundância pronta!")

if __name__ == "__main__":
    main()
