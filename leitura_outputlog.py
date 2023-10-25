import re
import os
import pandas as pd
import matplotlib.pyplot as plt

plt.style.use(os.path.join(os.path.dirname(__file__), 'graficos.mplstyle'))

residuos = list()
arquivos_log = [arquivo for arquivo in os.listdir() if re.search('output(.*)log', arquivo)]

for arquivo_log in arquivos_log:
    flag = False
    dados = list()
    with open(arquivo_log, 'r', encoding='utf-8') as arquivo:
        for linha in arquivo:
            if linha.strip().startswith('iter') and flag is False:
                colunas = linha.strip().split()[0:-1]
                flag = True
            if flag and re.search('\d$', linha):
                dados.append(linha.strip().split()[0:-2])
    arquivo.close()
    dados = pd.DataFrame(dados, columns=colunas)
    colunas_x = colunas[0]
    colunas_y = colunas[1:]
    dados[colunas_x] = dados[colunas_x].astype(int)
    dados[colunas_y] = dados[colunas_y].astype(float)
    residuos.append(dados)

residuos = pd.concat(residuos)
residuos.sort_values('iter', inplace=True)
residuos.reset_index(inplace=True)

fig, ax = plt.subplots()
x = residuos[colunas_x]
plt.yscale('log')
for coluna_y in colunas_y:
    y = residuos[coluna_y]
    ax.plot(x, y, label=coluna_y, lw=1)
ax.set_title('Gráfico de resíduos')
ax.set_xlabel(colunas_x)
ax.set_ylabel('residuals')
ax.legend()
plt.show()