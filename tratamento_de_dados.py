import os
import re
from datetime import datetime
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


paleta_gnuplot = ['#9400d3ff', '#009e73ff', '#56b4e9ff', '#e69f00ff', '#f0e442ff', '#0072b2ff', '#e51e10ff', '#000000ff']
dashes = ['-', '--', '-.', ':']
plt.rcParams['font.family'] = 'Courier New'

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
        relatorio = f'''{"-" * 80}
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
{"-" * 80}'''
        print(relatorio)

    def resetar_dados(self):
        self.dados_tratados = self.dados_originais.copy()

    def plotar_condutividade(self, normalizada=False, salvar=False, limite_eixo_x=None):
        condutividade = self.obter_condutividade_eletrica(normalizada)
        if normalizada:
            eixo_y = 'Condutividade elétrica normalizada'
            limite_y = 0
        else:
            eixo_y = 'Condutividade elétrica [mS]'
            limite_y = None
        fig, ax = plt.subplots()
        ax.plot(self.tempo / 60, condutividade,
                label=f'Eletrodo {self.numero_eletrodo}',
                color=paleta_gnuplot[self.numero_eletrodo-1]
                )
        ax.set_title(f'{self.prefixo} {self.numero_prefixo} - Perfil de condutividade elétrica')
        ax.set_xlabel('Tempo [min]')
        ax.set_ylabel(eixo_y)
        ax.set_xlim([0, 15*((self.tempo[-1]/60)//15)]) if limite_eixo_x is None else ax.set_xlim(limite_eixo_x)
        ax.set_ylim(limite_y)
        ax.legend()
        plt.show()

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

    def __init__(self, caminho):
        self._caminho = caminho
        self._obter_diretorio()
        self._instanciar_condutivimetros()

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
    def condutivimetros(self):
        return self._condutivimetros
    
    @property
    def condutivimetros_dict(self):
        return {condutivimetro.eletrodo: condutivimetro for condutivimetro in self.condutivimetros}

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
    
    def __getitem__(self, chave):
        return self.condutivimetros_dict[chave]
    
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

    def plotar_condutividade_eletrica(self, normalizada=False, extendida=False, salvar=False, limite_eixo_x=None):
        condutividade = self.obter_condutividade_eletrica(normalizada, extendida)
        if normalizada:
            eixo_y = 'Condutividade elétrica normalizada'
            limite_y = 0
        else:
            eixo_y = 'Condutividade elétrica [mS]'
            limite_y = None
        fig, ax = plt.subplots()
        for condutivimetro in self.condutivimetros:
            ax.plot(condutividade['tempo'] / 60, condutividade[condutivimetro.eletrodo],
                    label=f'Eletrodo {condutivimetro.numero_eletrodo}',
                    color=paleta_gnuplot[condutivimetro.numero_eletrodo-1]
                    )
        ax.set_title(f'{self.prefixo} {self.numero_prefixo} - Perfil de condutividade elétrica')
        ax.set_xlabel('Tempo [min]')
        ax.set_ylabel(eixo_y)
        ax.set_xlim([0, 15*((np.array(condutividade['tempo'])[-1]/60)//15)]) if limite_eixo_x is None else ax.set_xlim(limite_eixo_x)
        ax.set_ylim(limite_y)
        ax.legend()
        plt.show()

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
        self._condutivimetros = [Condutivimetro(os.path.join(self.caminho, arquivo)) for arquivo in lista_de_arquivos if padrao_csv.search(arquivo)]