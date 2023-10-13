import os
import re
from datetime import datetime
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


class Condutivimetro:

    padrao_csv = re.compile('(\w+)_(\d+)_(\w+)_(\d+).csv')

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
    
    def imprimir_relatorio(self):
        print(
f'''
Relatório: {self.prefixo} {self.numero_prefixo} - Eletrodo {self.numero_eletrodo}

Data: {self.data}
Horário de início: {self.horario_de_inicio}
Horário de término: {self.horario_de_termino}

Intervalo entre cada observação: {self.intervalo_de_tempo} s

Condutividade elétrica inicial: {self.condutividade_inicial:.1f} mS
Condutividade elétrica final: {self.condutividade_final:.1f} mS
Condutividade elétrica máxima: {self.condutividade_maxima:.1f} mS

Temperatura média: {self.temperatura_media:.1f} °C
'''
        )

    def resetar_dados(self):
        self.dados_tratados = self.dados_originais.copy()

    def _obter_arquivo(self):
        arquivo = os.path.basename(self._caminho)
        if __class__.padrao_csv.search(arquivo):
            self._arquivo = arquivo
            self._obter_identificacao()
        else:
            pass
    
    def _obter_identificacao(self):
        self._prefixo = __class__.padrao_csv.search(self._arquivo).group(1)
        self._numero_prefixo = __class__.padrao_csv.search(self._arquivo).group(2) 
        self._numero_eletrodo = __class__.padrao_csv.search(self._arquivo).group(4) 

    def _obter_base_de_dados(self):
        self._dados_originais = pd.read_csv(self._caminho, encoding='latin1', sep=';', decimal=',')

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
    