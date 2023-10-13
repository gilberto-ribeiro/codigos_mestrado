import os
import re
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
    def numero_eletrodo(self):
        return self._numero_eletrodo
    
    @property
    def eletrodo(self):
        return f'eletrodo_{self.numero_eletrodo}'
    
    @property
    def dados_originais(self):
        return self._dados_originais
    
    @property
    def dados_tratados(self):
        return self._dados_tratados
    
    @property
    def temperatura_media(self):
        return self._dados_tratados['temperatura'].mean()

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
        colunas_renomeadas = ['data', 'horario', 'condutividade_eletrica', 'temperatura']
        colunas_mapeadas = {i: j for i, j in zip(dados.columns, colunas_renomeadas)}
        dados.rename(columns=colunas_mapeadas, inplace=True)
        self._dados_tratados = dados
