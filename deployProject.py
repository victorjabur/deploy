#! /usr/bin/python
# coding: utf-8
import SFTPLocaweb, Mapeamento, sys

nome_projeto = sys.argv[1]

if nome_projeto == None or len(nome_projeto) == 0:
    print '*** Favor informar o parametro nome do projeto: %s: %s' % (e.__class__, e)
    sys.exit()

sftpLocaweb = SFTPLocaweb.SFTPLocaweb('../../python_conf/' + nome_projeto + '/settings.ini')

mapeamentos = []
listaIncluidos = []
listaExcluidos = []

config = sftpLocaweb.getConfigurationFile()
raiz_local = sftpLocaweb.raiz_local
raiz_remota = sftpLocaweb.raiz_remota

origem = raiz_local + '/' + nome_projeto
destino = raiz_remota + '/wsgi_apps/' + nome_projeto
listaIncluidos.append('*')
listaExcluidos.append(raiz_local + '/' + nome_projeto + '/' + nome_projeto + 'app/public_html')
listaExcluidos.append(raiz_local + '/' + nome_projeto + '/.git')
listaExcluidos.append(raiz_local + '/' + nome_projeto + '/.idea')
mapeamento = Mapeamento.Mapeamento(origem, destino, listaIncluidos, listaExcluidos)
mapeamentos.append(mapeamento)

origem = raiz_local + '/'+ nome_projeto + '/' + nome_projeto + 'app/public_html'
destino = raiz_remota + '/public_html/' + nome_projeto
listaIncluidos.append('*')
listaExcluidos.append(raiz_local + '/' + nome_projeto + '/' + nome_projeto + 'app/public_html/media/static')
mapeamento = Mapeamento.Mapeamento(origem, destino, listaIncluidos, listaExcluidos)
mapeamentos.append(mapeamento)

sftpLocaweb.sincronizarPastas(mapeamentos)
sftpLocaweb.coletarArquivosEstaticos()