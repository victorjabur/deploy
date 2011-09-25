#! /usr/bin/python
# -*- coding: iso-8859-1 -*-

class Mapeamento(object):

    def __init__(self, origem, destino, listaIncluidos = ['*'], listaExcluidos = []):
        self.origem = origem
        self.destino = destino
        self.listaIncluidos = listaIncluidos
        self.listaExcluidos = listaExcluidos