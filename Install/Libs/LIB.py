# Install/Libs/LIB.py
"""
Módulo de carregamento dinâmico para dependências essenciais do projeto.
Adicione ao array LIBRARIES qualquer módulo do Python (padrão ou externo)
que desejar disponibilizar para importação centralizada.
"""

import importlib

LIBRARIES = [
    "os",
    "json",
    # Se quiser, adicione outros: "numpy", "matplotlib.pyplot", etc.
]

def load_modules(library_list=None):
    """
    Importa dinamicamente os módulos definidos em library_list (ou LIBRARIES por padrão).
    Retorna um dicionário mapeando nomes para objetos de módulo.
    """
    if library_list is None:
        library_list = LIBRARIES
    imported_modules = {}
    for lib_name in library_list:
        try:
            imported_modules[lib_name] = importlib.import_module(lib_name)
        except ImportError:
            print(f"Erro ao importar biblioteca '{lib_name}'. Instale-a previamente.")
            imported_modules[lib_name] = None
    return imported_modules

# Instancia automaticamente os módulos ao importar este arquivo:
MODULES = load_modules()

# Uso em outros scripts:
# from Install.Libs.LIB import MODULES
# os = MODULES["os"]
# json = MODULES["json"]
