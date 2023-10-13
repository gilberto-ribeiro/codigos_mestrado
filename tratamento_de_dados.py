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

    @staticmethod
    def _obter_arquivo(self):
        arquivo = os.path.basename(self._caminho)
        if __class__.padrao_csv.search(arquivo):
            self._arquivo = arquivo
            self._obter_identificacao()
        else:
            pass
    
    @staticmethod
    def _obter_identificacao(self):
        self._prefixo = __class__.padrao_csv.search(self._arquivo).group(1)
        self._numero_prefixo = __class__.padrao_csv.search(self._arquivo).group(2) 
        self._numero_eletrodo = __class__.padrao_csv.search(self._arquivo).group(4) 

    