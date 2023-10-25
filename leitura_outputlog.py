import re
import os
import pandas as pd
import matplotlib.pyplot as plt

plt.style.use(os.path.join(os.path.dirname(__file__), 'graficos.mplstyle'))

flag = False
dados = list()
with open('output.log', 'r', encoding='utf-8') as arquivo:
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

fig, ax = plt.subplots()
x = dados[colunas_x]
plt.yscale('log')
for coluna_y in colunas_y:
    y = dados[coluna_y]
    ax.plot(x, y, label=coluna_y, lw=1)
ax.set_title('Gráfico de resíduos')
ax.set_xlabel(colunas_x)
ax.set_ylabel('residuals')
ax.legend()
plt.show()