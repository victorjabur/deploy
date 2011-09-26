#! /usr/bin/python
# -*- coding: iso-8859-1 -*-
from ConfigParser import RawConfigParser

import SFTPLocaweb, Mapeamento, sys

sftpLocaweb = SFTPLocaweb.SFTPLocaweb('../../python_conf/julianajabur/settings.ini')

mapeamentos = []
listaIncluidos = []
listaExcluidos = []

config = sftpLocaweb.getConfigurationFile()
raiz_local = sftpLocaweb.raiz_local
raiz_remota = sftpLocaweb.raiz_remota

origem = raiz_local + '/wsgi_apps/julianajabur'
destino = raiz_remota + '/wsgi_apps/julianajabur'
listaIncluidos.append('*')
listaExcluidos.append(raiz_local + '/wsgi_apps/julianajabur/julianajaburapp/public_html')
mapeamento = Mapeamento.Mapeamento(origem, destino, listaIncluidos, listaExcluidos)
mapeamentos.append(mapeamento)

origem = raiz_local + '/wsgi_apps/julianajabur/julianajaburapp/public_html'
destino = raiz_remota + '/public_html/julianajabur'
mapeamento = Mapeamento.Mapeamento(origem, destino)
mapeamentos.append(mapeamento)

sftpLocaweb.sincronizarPastas(mapeamentos)