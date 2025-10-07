import requests
from bs4 import BeautifulSoup
import pandas as pd

url = "https://lista.mercadolivre.com.br/notebook"
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, "html.parser")


print("Testando seletores de título:")


titulos1 = [tag.get_text(strip=True) for tag in soup.find_all("h2", class_="ui-search-item__title")]
print(f"1. h2.ui-search-item__title: {len(titulos1)} elementos")


titulos2 = []
for tag in soup.find_all(class_="ui-search-item__title"):
    link = tag.find('a')
    if link:
        titulos2.append(link.get_text(strip=True))
print(f"2. Links em .ui-search-item__title: {len(titulos2)} elementos")


titulos3 = [tag.get_text(strip=True) for tag in soup.find_all(class_=lambda x: x and "ui-search-item__title" in x)]
print(f"3. Qualquer .ui-search-item__title*: {len(titulos3)} elementos")


titulos4 = [tag.get_text(strip=True) for tag in soup.find_all("a", class_=lambda x: x and "ui-search-link" in x)]
print(f"4. Links .ui-search-link*: {len(titulos4)} elementos")


if len(titulos3) > 0:
    titulos = titulos3
    print(f"\nUsando opção 3: {len(titulos)} títulos encontrados")
elif len(titulos2) > 0:
    titulos = titulos2
    print(f"\nUsando opção 2: {len(titulos)} títulos encontrados")
elif len(titulos4) > 0:
    titulos = titulos4
    print(f"\nUsando opção 4: {len(titulos)} títulos encontrados")
else:
    titulos = titulos1
    print(f"\nUsando opção 1: {len(titulos)} títulos encontrados")


if len(titulos) == 0:
    print("\n=== DEBUG: Amostra do HTML ===")
    print(soup.prettify()[:2000])
    print("\n=== FIM DEBUG ===")


precos_atuais = []
precos_anteriores = []
precos_parcelados = []

for preco_div in soup.find_all("div", class_="poly-component__price"):
    # Preço anterior (riscado, pode não existir)
    anterior = preco_div.find("s", class_="andes-money-amount--previous")
    if anterior:
        frac = anterior.find("span", class_="andes-money-amount__fraction")
        precos_anteriores.append(frac.get_text(strip=True) if frac else "")
    else:
        precos_anteriores.append("")
    
    # Preço atual
    atual_div = preco_div.find("div", class_="poly-price__current")
    if atual_div:
        frac = atual_div.find("span", class_="andes-money-amount__fraction")
        precos_atuais.append(frac.get_text(strip=True) if frac else "")
    else:
        precos_atuais.append("")
    
    # Preço parcelado
    par_div = preco_div.find("span", class_="poly-price__installments")
    if par_div:
        frac = par_div.find("span", class_="andes-money-amount__fraction")
        precos_parcelados.append(frac.get_text(strip=True) if frac else "")
    else:
        precos_parcelados.append("")

print(f"\nResultados finais:")
print(f"Títulos: {len(titulos)}")
print(f"Preços atuais: {len(precos_atuais)}")
print(f"Preços anteriores: {len(precos_anteriores)}")
print(f"Preços parcelados: {len(precos_parcelados)}")


tam = min(len(titulos), len(precos_atuais), len(precos_anteriores), len(precos_parcelados))
dados = []
for i in range(tam):
    dados.append({
        "titulo": titulos[i] if i < len(titulos) else "",
        "preco_anterior": precos_anteriores[i],
        "preco_atual": precos_atuais[i],
        "preco_parcelado": precos_parcelados[i]
    })

if dados:
    df = pd.DataFrame(dados)
    print(f"\nPrimeiros 5 resultados:")
    print(df.head())
    df.to_csv("notebooks_mercadolivre_precos.csv", index=False)
    print(f"\nArquivo salvo: notebooks_mercadolivre_precos.csv")
else:
    print("\nNenhum dado foi coletado. Verifique o HTML de debug acima.")




#limpeza

df = pd.read_csv('notebooks_mercadolivre_precos.csv')

def limpa_preco(v):
    v = str(v).replace('.', '').replace(',', '.')
    try:
        return float(v)
    except:
        return None
# Defina as marcas que representam notebooks reais
marcas_notebook = ['dell', 'lenovo', 'hp', 'asus', 'acer', 'apple', 'positivo', 'samsung', 'vaio']

def is_produto_real(titulo):
    tit = str(titulo).lower()
    # Elimina agrupadores genéricos e palavras-chave
    agrupadores = ['mostrar mais', 'novo', 'usado', 'recondicionado', 'caixa aberta',
                   'até r$', 'mais de', 'parcelamento', 'grátis', 'local', 'internacional',
                   'android', 'windows', 'linux', 'macos', 'google chrome', 'freedos', 'full',
                   'somente lojas', 'lojas oficiais', 'core', 'celeron', 'ryzen', 'intel']
    if any(a in tit for a in agrupadores):
        return False
    # Mantém apenas se for uma das marcas de notebook
    return any(marca in tit for marca in marcas_notebook)

# Convertendo e filtrando
df_filtrado = df[df['titulo'].apply(is_produto_real)].copy()
df_filtrado['preco_atual'] = df_filtrado['preco_atual'].apply(limpa_preco)

df_filtrado.to_csv('notebooks_mercadolivre_produtos_filtrados.csv', index=False)
print(df_filtrado.head())
