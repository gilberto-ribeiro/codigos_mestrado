import re
import os
import pandas as pd
import matplotlib.pyplot as plt

plt.style.use(os.path.join(os.path.dirname(__file__), 'graficos.mplstyle'))

relatorio = list()
arquivos_log = [arquivo for arquivo in os.listdir() if re.search('output(.*)log', arquivo)]
colunas = ['iter', 'continuity', 'x-velocity', 'y-velocity', 'z-velocity', 'k', 'omega',
           'rp-h-p-v-z-150', 'rp-h-p-v-z-225', 'rp-h-p-v-z-75', 'rp-v-v', 'rp-m-i-y-p']
iteracao = colunas[0]
residuos = colunas[1:7]
reports = colunas[7:]

for arquivo_log in arquivos_log:
    flag = False
    dados = list()
    with open(arquivo_log, 'r', encoding='utf-8') as arquivo:
        for linha in arquivo:
            if linha.strip().startswith('iter') and flag is False:
                # colunas = linha.strip().split()[0:-1]
                flag = True
            if flag and re.search('\d$', linha):
                dados.append(linha.strip().split()[0:-2])
    arquivo.close()
    dados = pd.DataFrame(dados, columns=colunas)
    dados[iteracao] = dados[iteracao].astype(int)
    dados[residuos] = dados[residuos].astype(float)
    dados[reports] = dados[reports].astype(float)
    relatorio.append(dados)

relatorio = pd.concat(relatorio)
relatorio.sort_values('iter', inplace=True)
relatorio.reset_index(drop=True, inplace=True)

fig, axs = plt.subplots(2, 2)
x = relatorio[iteracao]
for velocidade_s in reports[0:3]:
    y = relatorio[velocidade_s]
    axs[0, 0].plot(x, y, label=velocidade_s, lw=1)
axs[0, 0].set_title('Velocidade média nos planos horizontais')
axs[0, 0].set_xlabel('Iteração')
axs[0, 0].set_ylabel('Velocidade média [m/s]')
axs[0, 0].legend()

velocidade_v = reports[3]
y = relatorio[velocidade_v]
axs[0, 1].plot(x, y, label=velocidade_v, lw=1)
axs[0, 1].set_title('Velocidade média em todo o tanque')
axs[0, 1].set_xlabel('Iteração')
axs[0, 1].set_ylabel('Velocidade média [m/s]')
axs[0, 1].legend()

y_plus = reports[4]
y = relatorio[y_plus]
axs[1, 0].plot(x, y, label=y_plus, lw=1)
axs[1, 0].set_title('Y plus máximo no impelidor')
axs[1, 0].set_xlabel('Iteração')
axs[1, 0].set_ylabel('Y plus')
axs[1, 0].legend()

plt.yscale('log')
for residuo in residuos:
    y = relatorio[residuo]
    axs[1, 1].plot(x, y, label=residuo, lw=1)
axs[1, 1].set_title('Gráfico de resíduos')
axs[1, 1].set_xlabel('Iteração')
axs[1, 1].set_ylabel('Resíduos')
axs[1, 1].legend()
plt.show()