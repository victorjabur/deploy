#! /usr/bin/python
# -*- coding: iso-8859-1 -*-

import SFTPLocaweb, Mapeamento

sftpLocaweb = SFTPLocaweb.SFTPLocaweb('../../python_conf/julianajabur/settings.ini')

mapeamentos = []
listaIncluidos = []
listaExcluidos = []

origem='C:/Users/Victor/pythonProjects/wsgi_apps/julianajabur'
destino = '/home/storage/c/6e/e5/julianajabur/wsgi_apps/julianajabur'
listaIncluidos.append('*')
listaExcluidos.append('C:/Users/Victor/pythonProjects/wsgi_apps/julianajabur/julianajaburapp/public_html')
mapeamento = Mapeamento.Mapeamento(origem, destino, listaIncluidos, listaExcluidos)
mapeamentos.append(mapeamento)

origem='C:/Users/Victor/pythonProjects/wsgi_apps/julianajabur/julianajaburapp/public_html'
destino='/home/storage/c/6e/e5/julianajabur/public_html/julianajabur'
mapeamento = Mapeamento.Mapeamento(origem, destino)
mapeamentos.append(mapeamento)

sftpLocaweb.sincronizarPastas(mapeamentos)