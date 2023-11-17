import re
import os
import math
import shutil
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from scipy.optimize import fsolve
import matplotlib.pyplot as plt
from matplotlib import ticker

plt.style.use(os.path.join(os.path.dirname(__file__), 'graficos.mplstyle'))
np.seterr(divide='ignore')

paleta_gnuplot = ['#9400d3ff', '#009e73ff', '#56b4e9ff', '#e69f00ff', '#f0e442ff', '#0072b2ff', '#e51e10ff', '#000000ff']
dashes = ['-', '--', '-.', ':']

padrao_csv = re.compile('(\w+)_(\d+)_(\w+)_(\d+).csv')
padrao_diretorio = re.compile('(\w+)_(\d+)')

class Condutivimetro:

    def __init__(self, caminho):
        self._caminho = caminho
        self._obter_arquivo()
        self._obter_base_de_dados()
        self._tratar_base_de_dados()

    @property
    def caminho(self):
        return self._caminho

    @property
    def arquivo(self):
        return self._arquivo

    @property
    def prefixo(self):
        return self._prefixo.capitalize()

    @property
    def numero_prefixo(self):
        return self._numero_prefixo
    
    @property
    def eletrodo(self):
        return f'eletrodo_{self.numero_eletrodo}'

    @property
    def numero_eletrodo(self):
        return self._numero_eletrodo
    
    @property
    def dados_originais(self):
        return self._dados_originais
    
    @property
    def dados_tratados_originais(self):
        return self._dados_tratados_originais
    
    @property
    def dados_tratados(self):
        return self._dados_tratados
    
    @property
    def dados_tratados_normalizados(self):
        dados = self.dados_tratados.copy()
        dados.insert(1, 'tempo', self.tempo)
        dados.insert(3, 'condutividade_eletrica_normalizada', self.condutividade_eletrica_normalizada)
        return dados
    
    @property
    def numero_de_observacoes(self):
        return self.dados_tratados.shape[0]
    
    @property
    def data(self):
        return list(self.dados_tratados_originais['horario'])[0].strftime('%d/%m/%Y')
    
    @property
    def horario_de_inicio(self):
        return list(self.dados_tratados_originais['horario'])[0].strftime('%H:%M:%S')
    
    @property
    def horario_de_termino(self):
        return list(self.dados_tratados_originais['horario'])[-1].strftime('%H:%M:%S')

    @property
    def intervalo_de_tempo(self):
        return (self.dados_tratados['horario'][1] - self.dados_tratados['horario'][0]).seconds
    
    @property
    def tempo(self):
        return np.array(self.dados_tratados.index * self.intervalo_de_tempo)
    
    @property
    def condutividade_eletrica(self):
        return np.array(self.dados_tratados['condutividade_eletrica'])
    
    @property
    def condutividade_inicial(self):
        return self.condutividade_eletrica[0]
    
    @property
    def condutividade_final(self):
        return self.condutividade_eletrica[-1]
    
    @property
    def condutividade_maxima(self):
        return self.dados_tratados['condutividade_eletrica'].max()
    
    @property
    def condutividade_eletrica_normalizada(self):
        c = self.condutividade_eletrica
        c_0 = self.condutividade_inicial
        c_inf = self.condutividade_final
        return (c - c_0) / (c_inf - c_0)
    
    @property
    def temperatura_media(self):
        return self.dados_tratados['temperatura'].mean()
    
    def obter_condutividade_eletrica(self, normalizada=False):
        return self.condutividade_eletrica_normalizada if normalizada else self.condutividade_eletrica
    
    def imprimir_relatorio(self):
        relatorio = f'''
RELATÓRIO POR CONDUTIVÍMETRO

{self.prefixo}: {self.numero_prefixo}
Eletrodo: {self.numero_eletrodo}

Data: {self.data}
Horário de início: {self.horario_de_inicio}
Horário de término: {self.horario_de_termino}

Número de observações: {self.numero_de_observacoes}
Intervalo entre cada observação: {self.intervalo_de_tempo} s

Condutividade elétrica inicial: {self.condutividade_inicial:.1f} mS
Condutividade elétrica final: {self.condutividade_final:.1f} mS
Condutividade elétrica máxima: {self.condutividade_maxima:.1f} mS

Temperatura média: {self.temperatura_media:.1f} °C
'''
        print(relatorio)
        return relatorio

    def resetar_dados(self):
        self.dados_tratados = self.dados_originais.copy()

    def plotar_condutividade_eletrica(self, normalizada=False, salvar=False, intervalo=None, caminho=None):
        condutividade = self.obter_condutividade_eletrica(normalizada)
        if normalizada:
            eixo_y = 'Condutividade elétrica normalizada'
            limite_y = [0, 2]
            nome_do_arquivo = f'fig_gr_{self.prefixo.lower()}_{self.numero_prefixo}_{self.eletrodo}_perfil_de_condutividade_eletrica_normalizada'
        else:
            eixo_y = 'Condutividade elétrica [mS]'
            limite_y = None
            nome_do_arquivo = f'fig_gr_{self.prefixo.lower()}_{self.numero_prefixo}_{self.eletrodo}_perfil_de_condutividade_eletrica'
        fig, ax = plt.subplots()
        ax.plot(self.tempo / 60, condutividade, label=f'Eletrodo {self.numero_eletrodo}')
        if normalizada:
            ax.fill_between([0, np.array(self.tempo)[-1] / 60] if intervalo is None else intervalo,
                            [0.95, 0.95], [1.05, 1.05], color='gray', alpha=0.25)
        ax.set_title(f'{self.prefixo} {self.numero_prefixo} - Perfil de condutividade elétrica')
        ax.set_xlabel('Tempo [min]')
        ax.set_ylabel(eixo_y)
        ax.set_xlim([0, 15*((self.tempo[-1]/60)//15)]) if intervalo is None else ax.set_xlim(intervalo)
        ax.set_ylim(limite_y)
        ax.xaxis.set_major_locator(ticker.MultipleLocator(5))
        ax.yaxis.set_major_locator(ticker.MultipleLocator(1))
        ax.legend()
        plt.show()
        if salvar:
            if caminho is None:
                caminho = os.path.dirname(self.caminho)
            else:
                caminho = caminho
            fig.savefig(os.path.join(caminho, f'{nome_do_arquivo}.png'))
            fig.savefig(os.path.join(caminho, f'{nome_do_arquivo}.pdf'))

    def _obter_arquivo(self):
        arquivo = os.path.basename(self.caminho)
        if padrao_csv.search(arquivo):
            self._arquivo = arquivo
            self._obter_identificacao()
        else:
            pass
    
    def _obter_identificacao(self):
        self._prefixo = padrao_csv.search(self.arquivo).group(1)
        self._numero_prefixo = int(padrao_csv.search(self.arquivo).group(2))
        self._numero_eletrodo = int(padrao_csv.search(self.arquivo).group(4))

    def _obter_base_de_dados(self):
        self._dados_originais = pd.read_csv(self.caminho, encoding='latin1', sep=';', decimal=',')

    def _tratar_base_de_dados(self):
        dados = self._dados_originais.iloc[:, 0:4].copy()
        colunas_renomeadas = ['data', 'hora', 'condutividade_eletrica', 'temperatura']
        colunas_mapeadas = {i: j for i, j in zip(dados.columns, colunas_renomeadas)}
        dados.rename(columns=colunas_mapeadas, inplace=True)
        dados = __class__._converter_tipo_de_dados(dados)
        dados['horario'] = dados.apply(__class__._obter_horario, axis=1)
        dados.drop(columns=['data', 'hora'], inplace=True)
        dados = dados.reindex(columns=['horario', 'condutividade_eletrica', 'temperatura'])
        self._dados_tratados_originais = dados
        self._dados_tratados = dados.copy()

    @staticmethod
    def _obter_horario(dados):
        data_hora_str = f'{dados["data"]} {dados["hora"]}'
        return datetime.strptime(data_hora_str, '%d/%m/%Y %H:%M:%S')

    @staticmethod
    def _converter_tipo_de_dados(dados):
        dados = dados.astype('str')
        dados['data'] = dados['data'].str.strip()
        dados['hora'] = dados['hora'].str.strip()
        dados['condutividade_eletrica'] = dados['condutividade_eletrica'].astype('float64')
        dados['temperatura'] = dados['temperatura'].astype('float64')
        return dados


class Ensaio:

    def __init__(self, caminho, porcentagem=95, dados_correcao_horarios=None):
        self._caminho = caminho
        self._porcentagem = porcentagem
        self._obter_diretorio()
        self._instanciar_condutivimetros()
        self._color_id = (self.numero_prefixo - 1) % 8
        self._ls_id = (self.numero_prefixo - 1) // 8
        if dados_correcao_horarios is not None:
            self._dados_correcao_horarios = dados_correcao_horarios
            self._corrigir_horarios_iniciais()

    @property
    def color_id(self):
        return self._color_id

    @property
    def ls_id(self):
        return self._ls_id
    
    @color_id.setter
    def color_id(self, color_id):
        self._color_id = color_id
    
    @ls_id.setter
    def ls_id(self, ls_id):
        self._ls_id = ls_id

    @property
    def caminho(self):
        return self._caminho

    @property
    def diretorio(self):
        return self._diretorio

    @property
    def prefixo(self):
        return self._prefixo.capitalize()

    @property
    def numero_prefixo(self):
        return self._numero_prefixo

    @property
    def ensaio(self):
        return self._diretorio
    
    @property
    def condutivimetros(self):
        return self._condutivimetros
    
    @property
    def condutivimetros_dict(self):
        return {condutivimetro.eletrodo: condutivimetro for condutivimetro in self.condutivimetros}
    
    @property
    def porcentagem(self):
        return self._porcentagem

    @property
    def limite(self):
        return np.log10((self.porcentagem/100 - 1)**2)

    @property
    def temperatura_media(self):
        lista_temperatura_media = np.array([condutivimetro.temperatura_media for condutivimetro in self.condutivimetros])
        return np.mean(lista_temperatura_media)
    
    @property
    def intervalo_de_tempo(self):
        lista_intervalo_de_tempo = [condutivimetro.intervalo_de_tempo for condutivimetro in self.condutivimetros]
        if all(intervalo_de_tempo == lista_intervalo_de_tempo[0] for intervalo_de_tempo in lista_intervalo_de_tempo):
            return lista_intervalo_de_tempo[0]
        else:
            print('Intervalos de tempo distintos')

    @property
    def tempos_de_mistura(self):
        return self._obter_tempos_de_mistura()
    
    def __getitem__(self, chave):
        return self.condutivimetros_dict[chave]
    
    def imprimir_relatorio(self):
        tempos_de_mistura_a_imprimir = '\n    '.join([f'{tm[0]:.0f} s | {tm[0]/60:.2f} min' for tm in self.tempos_de_mistura])
        relatorio = f'''
RELATÓRIO POR {self.prefixo.upper()}

{self.prefixo}: {self.numero_prefixo}

Possíveis tempos de mistura ({self.porcentagem}%: {self.limite:.2f}):
    {tempos_de_mistura_a_imprimir}

Temperatura média: {self.temperatura_media:.1f} °C
'''
        print(relatorio)
        return relatorio
    
    def obter_condutividade_eletrica(self, normalizada=False, extendida=False):
        lista_de_eletrodos = [pd.DataFrame({condutivimetro.eletrodo: condutivimetro.obter_condutividade_eletrica(normalizada)}) for condutivimetro in self.condutivimetros]
        dados_condutividade_eletrica = pd.concat(lista_de_eletrodos, axis=1)
        if (normalizada and extendida):
            dados_condutividade_eletrica.fillna(1.0, inplace=True)
        else:
            dados_condutividade_eletrica.dropna(inplace=True)
        tempo = np.array(dados_condutividade_eletrica.index * self.intervalo_de_tempo)
        dados_condutividade_eletrica.insert(0, 'tempo', tempo)
        return dados_condutividade_eletrica

    def obter_logaritmo_da_variancia(self, extendida=False):
        dados_condutividade_eletrica =  self.obter_condutividade_eletrica(normalizada=True, extendida=extendida)
        n = dados_condutividade_eletrica.shape[1] - 1
        c = np.array(dados_condutividade_eletrica.iloc[:, 1:].copy())
        logaritmo_da_variancia = pd.DataFrame({'logaritmo_da_variancia': np.log10(np.sum(((c - 1)**2), axis=1)/n)})
        dados = pd.concat([dados_condutividade_eletrica, logaritmo_da_variancia], axis=1)
        return dados

    def plotar_condutividade_eletrica(self, normalizada=False, extendida=False, salvar=False, intervalo=None, caminho=None):
        condutividade = self.obter_condutividade_eletrica(normalizada, extendida)
        if normalizada:
            eixo_y = 'Condutividade elétrica normalizada'
            limite_y = [0, 2]
            nome_do_arquivo = f'fig_gr_{self.ensaio}_perfil_de_condutividade_eletrica_normalizada'
        else:
            eixo_y = 'Condutividade elétrica [mS]'
            limite_y = None
            nome_do_arquivo = f'fig_gr_{self.ensaio}_perfil_de_condutividade_eletrica'
        fig, ax = plt.subplots()
        for condutivimetro in self.condutivimetros:
            ax.plot(condutividade['tempo'] / 60, condutividade[condutivimetro.eletrodo],
                    label=f'Eletrodo {condutivimetro.numero_eletrodo}',
                    color=f'C{condutivimetro.numero_eletrodo-1}'
                    )
        if normalizada:
            ax.fill_between([0, np.array(condutividade['tempo'])[-1] / 60] if intervalo is None else intervalo,
                            [0.95, 0.95], [1.05, 1.05], color='gray', alpha=0.25)
        ax.set_title(f'{self.prefixo} {self.numero_prefixo} - Perfil de condutividade elétrica')
        ax.set_xlabel('Tempo [min]')
        ax.set_ylabel(eixo_y)
        ax.set_xlim([0, 15*((np.array(condutividade['tempo'])[-1]/60)//15)]) if intervalo is None else ax.set_xlim(intervalo)
        ax.set_ylim(limite_y)
        ax.xaxis.set_major_locator(ticker.MultipleLocator(5))
        ax.legend()
        plt.show()
        if salvar:
            if caminho is None:
                caminho = self.caminho
            else:
                caminho = caminho
            fig.savefig(os.path.join(caminho, f'{nome_do_arquivo}.png'))
            fig.savefig(os.path.join(caminho, f'{nome_do_arquivo}.pdf'))

    def plotar_logaritmo_da_variancia(self, extendida=False, salvar=False, intervalo=None, caminho=None):
        dados = self.obter_logaritmo_da_variancia(extendida)
        logaritmo_da_variancia = np.array(dados['logaritmo_da_variancia'])
        tempo = np.array(dados['tempo'])
        fig, ax = plt.subplots()
        ax.plot(tempo / 60, logaritmo_da_variancia,
                color=f'C{self.color_id}',
                ls=dashes[self.ls_id],
                label=f'{self.prefixo} {self.numero_prefixo}')
        ax.plot([0, tempo[-1]/60] if intervalo is None else intervalo,
                [self.limite]*2, color='gray', ls='--')
        ax.text(0, self.limite, f'{self.porcentagem}%: {self.limite:.2f}', color='gray', fontsize='xx-small')
        ax.set_title(f'Logaritmo da variância RMS por tempo')
        ax.set_xlabel('Tempo [min]')
        ax.set_ylabel('Logaritmo da variância RMS da\ncondutividade elétrica normalizada')
        ax.set_xlim([0, 15*((tempo[-1]/60)//15)]) if intervalo is None else ax.set_xlim(intervalo)
        ax.xaxis.set_major_locator(ticker.MultipleLocator(5))
        ax.grid(which='minor')
        ax.legend()
        plt.show()
        if salvar:
            nome_do_arquivo = f'fig_gr_{self.ensaio}_logaritmo_da_variancia'
            if caminho is None:
                caminho = self.caminho
            else:
                caminho = caminho
            fig.savefig(os.path.join(caminho, f'{nome_do_arquivo}.png'))
            fig.savefig(os.path.join(caminho, f'{nome_do_arquivo}.pdf'))

    def _obter_diretorio(self):
        diretorio = os.path.basename(self.caminho)
        if padrao_diretorio.search(diretorio):
            self._diretorio = diretorio
            self._obter_identificacao()
        else:
            pass
    
    def _obter_identificacao(self):
        self._prefixo = padrao_diretorio.search(self.diretorio).group(1)
        self._numero_prefixo = int(padrao_diretorio.search(self.diretorio).group(2))

    def _instanciar_condutivimetros(self):
        lista_de_arquivos = os.listdir(self.caminho)
        # Verificar como ordenar os eletrodos:
        # lista_de_arquivos.sort(key=lambda arquivo: int(padrao_csv.search(arquivo).group(4)))
        self._condutivimetros = [Condutivimetro(os.path.join(self.caminho, arquivo)) for arquivo in lista_de_arquivos if padrao_csv.search(arquivo)]
    
    def _obter_tempos_de_mistura(self):
        dados = self.obter_logaritmo_da_variancia(extendida=True)
        numero_de_pontos = dados.shape[0]
        tempos_de_mistura = list()
        for i in range(numero_de_pontos):
            if i == 0:
                continue
            else:
                if dados['logaritmo_da_variancia'][i] <= self.limite and dados['logaritmo_da_variancia'][i-1] > self.limite:
                    tempos_de_mistura.append((dados['tempo'][i], dados['logaritmo_da_variancia'][i]))
        return tempos_de_mistura
    
    def _corrigir_horarios_iniciais(self):
        dados = self._dados_correcao_horarios
        if type(dados) is list:
            dados = Experimento._importar_dados_do_google_sheets(*dados)
        dados = dados.astype(str)
        dados['data'] = dados['data'].apply(lambda x: datetime.strptime(x, '%d/%m/%Y'))
        lista_de_eletrodos = [coluna for coluna in dados.columns if re.search('eletrodo_\d+', coluna) and (coluna in self.condutivimetros_dict)]
        for eletrodo in lista_de_eletrodos:
            dados[eletrodo] = dados[eletrodo].apply(lambda x: datetime.strptime(x, '%H:%M:%S'))
        for eletrodo in lista_de_eletrodos:
            dados[f'{eletrodo}_normalizado'] = dados[eletrodo] - dados[lista_de_eletrodos].min(axis=1)
        lista_de_eletrodos_normalizados = [f'{eletrodo}_normalizado' for eletrodo in lista_de_eletrodos]
        dados_por_dia = dados[lista_de_eletrodos_normalizados].groupby(dados['data']).mean().copy()
        dados_por_dia = dados_por_dia.map(lambda x: x.seconds)
        colunas_a_renomear = {eletrodo_normalizado: eletrodo for eletrodo, eletrodo_normalizado in zip(lista_de_eletrodos, lista_de_eletrodos_normalizados)}
        dados_por_dia.rename(columns=colunas_a_renomear, inplace=True)
        lista_de_horarios_iniciais = list()
        for eletrodo in self.condutivimetros_dict:
            data_eletrodo = datetime.strptime(self[eletrodo].data, '%d/%m/%Y')
            data_correcao = max([data for data in dados_por_dia.index if data <= data_eletrodo])
            fator_de_correcao = int(dados_por_dia.loc[data_correcao, eletrodo])
            self[eletrodo]._dados_tratados['horario'] = self[eletrodo]._dados_tratados['horario'].apply(lambda x: x - timedelta(seconds=fator_de_correcao))
            horario_inicial = self[eletrodo].dados_tratados['horario'][0]
            valores = [eletrodo, data_eletrodo, data_correcao, fator_de_correcao, horario_inicial]
            lista_de_horarios_iniciais.append(valores)
        colunas = ['eletrodo', 'data_eletrodo', 'data_correcao', 'fator_de_correcao', 'horario_inicial']
        dados_de_correcao = pd.DataFrame(lista_de_horarios_iniciais, columns=colunas)
        tabela_ultimo_tempo_inicial = dados_de_correcao['horario_inicial'].groupby(dados_de_correcao['data_correcao']).max()
        for eletrodo in self.condutivimetros_dict:
            data_correcao = dados_de_correcao['data_correcao'][dados_de_correcao['eletrodo'] == eletrodo]
            ultimo_tempo_inicial = tabela_ultimo_tempo_inicial[data_correcao].iloc[0]
            selecao = self[eletrodo].dados_tratados['horario'] >= ultimo_tempo_inicial
            self[eletrodo]._dados_tratados = self[eletrodo]._dados_tratados[selecao].copy()
            self[eletrodo]._dados_tratados.reset_index(drop=True, inplace=True)
            

class Experimento:

    def __init__(self, caminho, lista=None, dados_correcao_horarios=None):
        self._caminho = caminho
        self._lista = lista
        self._dados_correcao_horarios = dados_correcao_horarios
        self._instanciar_ensaios()
        self._redefinir_ids()

    @property
    def caminho(self):
        return self._caminho
    
    @property
    def lista(self):
        return self._lista
    
    @property
    def ensaios(self):
        return self._ensaios
    
    @property
    def ensaios_dict(self):
        return {ensaio.ensaio: ensaio for ensaio in self.ensaios}
    
    def __getitem__(self, chave):
        return self.ensaios_dict[chave]
    
    def obter_resultados(self, diretorio='resultados'):
        diretorio_resultados = os.path.join(self.caminho, diretorio)
        diretorio_figuras = os.path.join(diretorio_resultados, 'figuras')
        if os.path.exists(diretorio_resultados):
            shutil.rmtree(diretorio_resultados)
        os.mkdir(diretorio_resultados)
        os.mkdir(diretorio_figuras)
        self.plotar_logaritmo_da_variancia(salvar=True, caminho=diretorio_figuras)
        with open(os.path.join(diretorio_resultados, 'relatorio.txt'), 'w') as arquivo_relatorio:
            arquivo_relatorio.write('RELATÓRIO DO EXPERIMENTO\n')
            for ensaio in self.ensaios:
                ensaio.plotar_condutividade_eletrica(normalizada=True, salvar=True, caminho=diretorio_figuras)
                ensaio.plotar_logaritmo_da_variancia(salvar=True, caminho=diretorio_figuras)
                arquivo_relatorio.write('\n' + '-' * 80 + f' {ensaio.numero_prefixo:02}' + '\n')
                arquivo_relatorio.write(ensaio.imprimir_relatorio())
                for eletrodo in ensaio.condutivimetros:
                    arquivo_relatorio.write(eletrodo.imprimir_relatorio())
        arquivo_relatorio.close()

    def plotar_condutividade_eletrica(self, combinacao, normalizada=False, extendida=False, salvar=False, intervalo=None, caminho=None):
        if normalizada:
            eixo_y = 'Condutividade elétrica normalizada'
            limite_y = [0, 2]
            nome_do_arquivo = f'fig_gr_perfil_de_condutividade_eletrica_normalizada'
        else:
            eixo_y = 'Condutividade elétrica [mS]'
            limite_y = None
            nome_do_arquivo = f'fig_gr_perfil_de_condutividade_eletrica'
        lista_de_tempos = list()
        fig, ax = plt.subplots()
        for ensaio in combinacao:
            for eletrodo in combinacao[ensaio]:
                condutividade = self[f'ensaio_{ensaio}'][f'eletrodo_{eletrodo}'].obter_condutividade_eletrica(normalizada)
                tempo = self[f'ensaio_{ensaio}'][f'eletrodo_{eletrodo}'].tempo
                lista_de_tempos.append(tempo[-1])
                ax.plot(tempo / 60, condutividade,
                        label=f'Ens. {ensaio} - El. {eletrodo}'
                        )
        tempo_maximo = max(lista_de_tempos)
        if normalizada:
            ax.fill_between([0, tempo_maximo/60] if intervalo is None else intervalo,
                            [0.95, 0.95], [1.05, 1.05], color='gray', alpha=0.25)
        ax.set_title(f'Perfil de condutividade elétrica')
        ax.set_xlabel('Tempo [min]')
        ax.set_ylabel(eixo_y)
        ax.set_xlim([0, 15*((tempo_maximo/60)//15)]) if intervalo is None else ax.set_xlim(intervalo)
        ax.set_ylim(limite_y)
        ax.xaxis.set_major_locator(ticker.MultipleLocator(5))
        ax.legend(loc='center left', bbox_to_anchor=(1, 0.5), fontsize='x-small')
        plt.show()
        if salvar:
            if caminho is None:
                caminho = self.caminho
            else:
                caminho = caminho
            fig.savefig(os.path.join(caminho, f'{nome_do_arquivo}.png'))
            fig.savefig(os.path.join(caminho, f'{nome_do_arquivo}.pdf'))

    def plotar_logaritmo_da_variancia(self, extendida=False, salvar=False, intervalo=None, caminho=None):
        fig, ax = plt.subplots(figsize=(7, 3.5))
        lista_de_tempos = list()
        for ensaio in self.ensaios:
            dados = ensaio.obter_logaritmo_da_variancia(extendida)
            logaritmo_da_variancia = np.array(dados['logaritmo_da_variancia'])
            tempo = np.array(dados['tempo'])
            lista_de_tempos.append(tempo[-1])
            limite, porcentagem = ensaio.limite, ensaio.porcentagem
            ax.plot(tempo / 60, logaritmo_da_variancia,
                color=f'C{ensaio.color_id}',
                ls=dashes[ensaio.ls_id],
                label=f'{ensaio.prefixo} {ensaio.numero_prefixo}')
        tempo_maximo = max(lista_de_tempos)
        # Refatorar as duas linhas a baixo, pois pega limite e porcentagem do último ensaio
        ax.plot([0, tempo_maximo/60] if intervalo is None else intervalo,
                [limite]*2, color='gray', ls='--')
        ax.text(0, limite, f'{porcentagem}%: {limite:.2f}', color='gray', fontsize='xx-small')
        ax.set_title(f'Logaritmo da variância RMS por tempo')
        ax.set_xlabel('Tempo [min]')
        ax.set_ylabel('Logaritmo da variância RMS da\ncondutividade elétrica normalizada')
        ax.set_xlim([0, 15*((tempo_maximo/60)//15)]) if intervalo is None else ax.set_xlim(intervalo)
        ax.xaxis.set_major_locator(ticker.MultipleLocator(5))
        ax.grid(which='minor')
        ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
        plt.tight_layout()
        plt.show()
        if salvar:
            nome_do_arquivo = f'fig_gr_logaritmo_da_variancia'
            if caminho is None:
                caminho = self.caminho
            else:
                caminho = caminho
            fig.savefig(os.path.join(caminho, f'{nome_do_arquivo}.png'))
            fig.savefig(os.path.join(caminho, f'{nome_do_arquivo}.pdf'))
    
    def combinar_ensaios(self, dados, prefixo='ensaio', diretorio='ensaios_novo', colunas=None, lista=None, dados_correcao_horarios=None):
        if type(dados) is list:
            dados = __class__._importar_dados_do_google_sheets(*dados)
        if colunas is None:
            colunas = ['ensaio_antigo', 'ensaio_novo', 'eletrodos_antigo', 'eletrodos_novo']
        diretorio = os.path.join(self.caminho, diretorio)
        if os.path.exists(diretorio):
            shutil.rmtree(diretorio)
        os.mkdir(diretorio)
        for i in dados.index:
            ensaio_antigo = f'{prefixo}_{dados[colunas[0]][i]}'
            ensaio_novo = f'{prefixo}_{dados[colunas[1]][i]}'
            eletrodos_antigo = dados[colunas[2]][i].split('_')
            eletrodos_antigo = [f'eletrodo_{eletrodo_antigo}' for eletrodo_antigo in eletrodos_antigo]
            eletrodos_novo = dados[colunas[3]][i].split('_')
            eletrodos_novo = [f'eletrodo_{eletrodo_novo}' for eletrodo_novo in eletrodos_novo]
            diretorio_ensaio_antigo = self[ensaio_antigo].caminho
            diretorio_ensaio_novo = os.path.join(diretorio, ensaio_novo)
            if ensaio_antigo in self.ensaios_dict:
                if not os.path.exists(diretorio_ensaio_novo):
                    os.mkdir(diretorio_ensaio_novo)
                for eletrodo_antigo, eletrodo_novo in zip(eletrodos_antigo, eletrodos_novo):
                    arquivo_antigo = os.path.join(diretorio_ensaio_antigo, f'{ensaio_antigo}_{eletrodo_antigo}.csv')
                    arquivo_novo = os.path.join(diretorio_ensaio_novo, f'{ensaio_novo}_{eletrodo_novo}.csv')
                    shutil.copy(arquivo_antigo, arquivo_novo)
        return __class__(diretorio, lista=lista, dados_correcao_horarios=dados_correcao_horarios)

    def _obter_lista_de_ensaios(self):
        lista_de_diretorios = os.listdir(self.caminho)
        lista_de_ensaios = list()
        for ensaio in lista_de_diretorios:
            if padrao_diretorio.search(ensaio):
                numero_do_ensaio = int(padrao_diretorio.search(ensaio).group(2))
                if self.lista is None:
                    lista_de_ensaios.append(ensaio)
                elif numero_do_ensaio in self._lista:
                    lista_de_ensaios.append(ensaio)
        lista_de_ensaios.sort(key=lambda ensaio: int(padrao_diretorio.search(ensaio).group(2)))
        return lista_de_ensaios
    
    def _instanciar_ensaios(self):
        lista_de_ensaios = self._obter_lista_de_ensaios()
        self._ensaios = [Ensaio(os.path.join(self.caminho, diretorio), dados_correcao_horarios = self._dados_correcao_horarios) for diretorio in lista_de_ensaios]

    def _redefinir_ids(self):
        for id, ensaio in enumerate(self.ensaios):
            ensaio.color_id = id % 8
            ensaio.ls_id = id // 8

    @staticmethod
    def _importar_dados_do_google_sheets(url_planilha, aba_planilha):
        id_planilha = re.search('https://docs.google.com/spreadsheets/d/(.*)/', url_planilha).group(1)
        url = f'https://docs.google.com/spreadsheets/d/{id_planilha}/gviz/tq?tqx=out:csv&sheet={aba_planilha}'
        return pd.read_csv(url)
    

class Simulacao:

    def __init__(self, caminho):
        self._caminho = caminho

    @property
    def caminho(self):
        return self._caminho
    
    @property
    def diretorio(self):
        return os.path.basename(self.caminho)
    
    @property
    def numero_da_simulacao(self):
        return re.search('^(\d{2})_.*', self.diretorio).group(1)

    @property
    def caminho_cases(self):
        return os.path.join(self._caminho, 'cases')

    @property
    def caminho_running(self):
        return os.path.join(self.caminho_cases, 'running')

    def obter_outputlog(self):
        coluna_iteracao = ['iter']
        colunas_residuos = ['continuity', 'x-velocity', 'y-velocity', 'z-velocity', 'k', 'omega']
        arquivos_log = [os.path.join(self.caminho_running, arquivo) \
                        for arquivo in os.listdir(self.caminho_running) \
                        if re.search('output.*\.log', arquivo)]
        outputlog = list()
        for arquivo_log in arquivos_log:
            flag = False
            dados = list()
            with open(arquivo_log, 'r', encoding='utf-8') as arquivo:
                for linha in arquivo:
                    if linha.strip().startswith('iter') and flag is False:
                        colunas = linha.strip().split()[0:-1]
                        colunas_reports = [coluna for coluna in colunas \
                                          if coluna not in (coluna_iteracao + colunas_residuos)]
                        flag = True
                    if flag and re.search('\d$', linha):
                        dados.append(linha.strip().split()[0:-2])
            arquivo.close()
            dados = pd.DataFrame(dados, columns=colunas)
            dados[coluna_iteracao] = dados[coluna_iteracao].astype(int)
            dados[colunas_residuos] = dados[colunas_residuos].astype(float)
            dados[colunas_reports] = dados[colunas_reports].astype(float)
            outputlog.append(dados)
        outputlog = pd.concat(outputlog)
        outputlog.sort_values('iter', inplace=True)
        outputlog.reset_index(drop=True, inplace=True)
        return outputlog

    def plotar_outputlog(self, disposicao, graficos, salvar=False):
        outputlog = self.obter_outputlog()
        indices = self._gerar_indices_dos_graficos(disposicao)
        fig, axs = plt.subplots(*disposicao, figsize=(16, 9), dpi=600)
        for indice, parametros in zip(indices, graficos):
            self._gerar_grafico_individual_outputlog(axs[*indice], outputlog, **parametros)
        plt.yscale('log')
        parametros_residuos = {
            'titulo': 'Resíduos',
            'eixo_y': 'Resíduos',
            'variaveis': ['continuity', 'x-velocity', 'y-velocity', 'z-velocity', 'k', 'omega']
        }
        self._gerar_grafico_individual_outputlog(axs[*indices[-1]], outputlog, **parametros_residuos)
        plt.show()
        if salvar:
            fig.savefig(os.path.join(self.caminho_running, f'fig_gr_case_{self.numero_da_simulacao}_outputlog.pdf'))
            fig.savefig(os.path.join(self.caminho_running, f'fig_gr_case_{self.numero_da_simulacao}_outputlog.png'))

    @staticmethod
    def _gerar_grafico_individual_outputlog(ax, dados, titulo, eixo_y, variaveis, legendas=None, eixo_x='Iteração'):
        x = dados['iter']
        if legendas is None:
            legendas = variaveis
        for variavel, legenda in zip(variaveis, legendas):
            y = dados[variavel]
            ax.plot(x, y, label=legenda, lw=1)
        ax.set_title(titulo)
        ax.set_ylabel(eixo_y)
        ax.set_xlabel(eixo_x)
        if len(legendas) != 1:
            ax.legend()

    @staticmethod
    def _gerar_indices_dos_graficos(disposicao):
        indices = list()
        if 1 in disposicao:
            for i in range(math.prod(list(disposicao))):
                indices.append([i])
        else:
            for i in range(disposicao[0]):
                for j in range(disposicao[1]):
                    indices.append((i, j))
        return indices
    
    @staticmethod
    def determinar_gci(h, phi):
        r = list()
        epsilon = list()
        for i in range(2):
            r.append(h[i+1] / h[i])
            epsilon.append(phi[i+1] - phi[i])

        def eq3(x, r, epsilon):
            p, q, s = x
            eq3a = p - (1/np.log(r[0]))*np.abs(np.log(np.abs(epsilon[1]/epsilon[0])) + q)
            eq3b = q - np.log((r[0]**p - s)/(r[1]**p - s))
            eq3c = s - np.sign(epsilon[1] / epsilon[0])
            return [eq3a, eq3b, eq3c]
        
        p = fsolve(eq3, [1, 1, 1], args=(r, epsilon))[0]
        phi_ext = ((r[0]**p)*phi[0] - phi[1]) / (r[0]**p - 1)
        e_a = np.abs((phi[0] - phi[1]) / (phi[0]))
        e_ext = np.abs((phi_ext - phi[0]) / (phi_ext))
        gci_fine = (1.25*e_a) / (r[0]**p - 1)
        dados = pd.DataFrame([[h, *r, p, *phi, phi_ext, f'{e_a:.2%}', f'{e_ext:.2%}', f'{gci_fine:.2%}']],
                            columns=['h', 'r21', 'r32', 'p',
                                    'phi_1', 'phi_2', 'phi_3', 'phi_ext',
                                    'e_a', 'e_ext', 'gci_fine'],
                            index = ['gci']).transpose()
        return dados