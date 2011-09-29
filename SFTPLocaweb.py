#! /usr/bin/python
# -*- coding: iso-8859-1 -*-

import os, paramiko, hashlib, sys, pickle, re, fnmatch
from stat import S_ISREG, S_ISDIR
from ConfigParser import RawConfigParser

class SFTPLocaweb:

    def __init__(self, caminhoArquivoConfiguracao):
        self.caminhoArquivoConfiguracao = caminhoArquivoConfiguracao
        self.config = self.getConfigurationFile()
        self.raiz_local = self.config.get('geral', 'RAIZ_LOCAL')
        self.raiz_remota = self.config.get('geral', 'RAIZ_REMOTA')
        self.hostname = self.getEntry('deploy', 'HOSTNAME')
        self.port = self.config.getint('deploy', 'PORT')
        self.username = self.getEntry('deploy', 'USERNAME')
        self.password = self.getEntry('deploy', 'PASSWORD')
        self.wsgi_local = self.getEntry('deploy', 'WSGI_LOCAL')
        self.wsgi_remoto = self.getEntry('deploy', 'WSGI_REMOTO')
        self.indice_md5_local = self.getEntry('deploy', 'INDICE_MD5_LOCAL')
        self.indice_md5_remoto = self.getEntry('deploy', 'INDICE_MD5_REMOTO')
        self.mapeamento = ''
        self.pastaOrigem = ''
        self.pastaDestino = ''
        self.sftp = None
        self.dicionario_md5 = {}
        self.statusTransferencia = 0    
        self.totais = {}    
        self.transport = None
  
    def getConfigurationFile(self):
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        PYTHON_CONF = os.path.abspath(self.pathJoin(BASE_DIR, self.caminhoArquivoConfiguracao))
        config = RawConfigParser()
        config.read(PYTHON_CONF)
        return config

    def getEntry(self, setor, chave):
        conf = self.config.get(setor, chave)
        if conf.startswith('RAIZ_LOCAL'):
            conf = conf.replace('RAIZ_LOCAL', self.raiz_local)
        if conf.startswith('RAIZ_REMOTA'):
            conf = conf.replace('RAIZ_REMOTA', self.raiz_remota)
        return conf
    
    def getConexaoSSH(self):
        try:
            print 'Estabelecendo conexao com: ', self.hostname, self.port, '...'
            self.transport = paramiko.Transport((self.hostname, self.port))
            self.transport.connect(username=self.username, password=self.password, hostkey=None)
            self.sftp = paramiko.SFTPClient.from_transport(self.transport)
        except Exception, e:
            print '*** Erro ao se conectar com o servidor: %s: %s' % (e.__class__, e)
            sys.exit()
            try:
                self.transport.close()
            except:
                pass
  
    def pathJoin(self, raiz, diretorio):
        return os.path.join(raiz, diretorio).replace('\\', '/')
    
    def criarDiretorioRemoto(self, diretorio):
        try:
            self.sftp.mkdir(diretorio)
            print '    (diretorio criado) ', diretorio
            return 1
        except IOError:
            #print '    (diretorio ja existe) ', diretorio
            return 0
  
    def getDiretorioRemotoFromLocal(self, diretorioLocal):
        return diretorioLocal.replace(self.pastaOrigem, self.pastaDestino)

    def getDiretorioLocalFromRemoto(self, diretorioRemoto):
        return diretorioRemoto.replace(self.pastaDestino, self.pastaOrigem)

    def existeArquivoIndice(self):
        try:
            if self.sftp.stat(self.indice_md5_remoto):
                return True
        except:
            return False
  
    def recuperaMd5(self, entrada):
        try:
            md5 = self.dicionario_md5[entrada]
            return md5
        except KeyError:
            return None
  
    def atualizarIndice(self):
        for key in self.dicionario_md5.keys():
            if key.startswith(self.pastaDestino):
                if not os.path.exists(self.getDiretorioLocalFromRemoto(key)):
                    self.dicionario_md5.pop(key)
  
    def carregarDicionarioMd5(self):
        if self.existeArquivoIndice():
            self.sftp.get(self.indice_md5_remoto, self.indice_md5_local)
            indice = open(self.indice_md5_local, 'rb')
            self.dicionario_md5 = pickle.load(indice)
            indice.close()
  
    def salvarDicionarioMd5(self):
        indice = open(self.indice_md5_local, 'wb')
        pickle.dump(self.dicionario_md5, indice)
        indice.close()  
        self.copiarArquivoParaServidor(self.indice_md5_local, self.indice_md5_remoto)
    
    def isArquivosIguaisMD5(self, local_file, remote_file):
        m_local = hashlib.md5()
        m_local.update(open(local_file, "rb").read())
        md5Local = m_local.digest()
        md5Remoto = self.recuperaMd5(remote_file)
        if md5Local == md5Remoto:
            return True
        else:
            return md5Local
  
    def calcularMd5(self, local_file):
        m_local = hashlib.md5()
        m_local.update(open(local_file, "rb").read())
        return m_local.digest()        
  
    def acompanharTransferenciaArquivo(self, tamanhoTransferido, tamanhoTotal):
        try:
            porcentagem = int((float(tamanhoTransferido) / float(tamanhoTotal)) * 100)
            pontos = porcentagem - self.statusTransferencia
            if pontos > 0:
                self.statusTransferencia = self.statusTransferencia + pontos
                sys.stdout.write(pontos * '.')
        except Exception, e:
            print '*** Exceçao Lançada: %s: %s' % (e.__class__, e)
  
    def copiarArquivoParaServidor(self, local_file, remote_file):
        tentativas = 0
        try:
            self.statusTransferencia = 0
            self.sftp.put(local_file, remote_file, self.acompanharTransferenciaArquivo)
            print ''
        except:
            tentativas += 1     
            print 'ERRO ao enviar o arquivo ', local_file
            self.copiarArquivoParaServidor(local_file, remote_file)
        return tentativas

    def sincronizarPastas(self, mapeamentos):
        self.getConexaoSSH()
        self.carregarDicionarioMd5()
        for mapeamento in mapeamentos:
            self.mapeamento = mapeamento
            self.totais = {}
            self.pastaOrigem = mapeamento.origem
            self.pastaDestino = mapeamento.destino
            self.executarCopia()
        self.atualizarIndice()
        print 'Copiando o indice md5: ',
        self.salvarDicionarioMd5()
        print 'Copiando o index.wsgi: ',
        self.copiarArquivoParaServidor(self.wsgi_local, self.wsgi_remoto)
        self.transport.close()
    
    def deletarRecursosRemotos(self, dirRemoto):
        try:
            #print 'PROCESSANDO A PASTA REMOTA - ', dirRemoto
            for entrada in  self.sftp.listdir(dirRemoto):
                remote_entry = self.pathJoin(dirRemoto, entrada)
                remote_entry = remote_entry.replace('\\','/')
                if self.isRemoteDir(remote_entry):
                    self.deletarRecursosRemotos(remote_entry)
                elif self.isRemoteFile(remote_entry):
                    local_file = self.getDiretorioLocalFromRemoto(remote_entry)
                    if not os.path.exists(local_file):
                        print "    (arquivo removido):", remote_entry, " (" + self.formataTamanhoArquivo(self.sftp.stat(remote_entry).st_size) + ") "
                        self.sftp.remove(remote_entry)
                        self.contabilizarTotais('arquivos_removidos', 1)
            if self.sftp.listdir != '' and not os.path.exists(self.getDiretorioLocalFromRemoto(dirRemoto)):
                print '    (diretorio removido): ', dirRemoto
                self.sftp.rmdir(dirRemoto)
                self.contabilizarTotais('diretorios_removidos', 1)
        except Exception, e:
            print '*** Exceçao Lançada ao deletar Recursos Remotos: %s: %s' % (e.__class__, e)
            sys.exit()
  
    def isRemoteDir (self, remote_path):
        try:
            st = self.sftp.stat( remote_path )
            return S_ISDIR(st.st_mode)
        except Exception:
            return False

    def isRemoteFile (self, remote_path):
        try:
            st = self.sftp.stat( remote_path )
            return S_ISREG(st.st_mode)
        except Exception:
            return False
  
    def formataTamanhoArquivo(self, tamanho):
        tipo = 1
        while(tamanho > 1024):
            tamanho = float(tamanho) / 1024.0
            tipo += 1
        if(tipo == 1):
            tamanho = "%.2f bytes" % (tamanho)
        elif(tipo == 2):
            tamanho = "%.2f Kb" % (tamanho)
        elif(tipo == 3):
            tamanho = "%.2f Mb" % (tamanho)
        elif(tipo == 4):
            tamanho = "%.2f Gb" % (tamanho)
        return tamanho.replace(".00", "")
          
    def contabilizarTotais(self, tipo, valor):
        self.totais[tipo] = self.getResultadoTotal(tipo) + valor
    
    def getResultadoTotal(self, chave):
        try:
            return self.totais[chave]
        except:
            return 0

    def executarCopia(self):
        print '=' * 60
        print 'Local = ' + self.pastaOrigem
        print 'Remoto = ' + self.pastaDestino
        print '=' * 60
        try:
            diretorioRemoto = self.pastaDestino
            self.contabilizarTotais('diretorios_criados', self.criarDiretorioRemoto(diretorioRemoto))
            incluidos = r'|'.join([fnmatch.translate(x) for x in self.mapeamento.listaIncluidos])
            excluidos = r'|'.join([fnmatch.translate(x) for x in self.mapeamento.listaExcluidos]) or r'$.'
            for raiz, diretorios, arquivos in os.walk(self.pastaOrigem):

                # filtro diretorios
                diretorios[:] = [os.path.join(raiz, d).replace('\\','/') for d in diretorios]
                diretorios[:] = [d for d in diretorios if not re.match(excluidos, d)]

                # filtro arquivos
                arquivos = [os.path.join(raiz, f).replace('\\','/') for f in arquivos]
                arquivos = [f for f in arquivos if not re.match(excluidos, f)]
                arquivos = [f for f in arquivos if re.match(incluidos, f)]

                #print 'PROCESSANDO A PASTA LOCAL - ', raiz
                for diretorio in diretorios:
                    self.contabilizarTotais('diretorios', 1)
                    diretorioRemoto = self.getDiretorioRemotoFromLocal(diretorio)
                    self.contabilizarTotais('diretorios_criados', self.criarDiretorioRemoto(diretorioRemoto))
                for arquivo in arquivos:
                    self.contabilizarTotais('arquivos', 1)
                    local_file = arquivo
                    remote_file = self.getDiretorioRemotoFromLocal(arquivo)
                    is_up_to_date = False
                    try:
                        # verifica se o arquivo remoto existe
                        if self.sftp.stat(remote_file):
                            md5 = self.isArquivosIguaisMD5(local_file, remote_file)
                            if md5 == True:
                                #print "    (nao modificado):", arquivo + " (" + self.formataTamanhoArquivo(os.path.getsize(local_file)) + ")"
                                self.contabilizarTotais('arquivos_naomodificados', 1)
                                is_up_to_date = True
                            else:
                                print "    (modificado):", arquivo + " (" + self.formataTamanhoArquivo(os.path.getsize(local_file)) + ") ",
                                self.dicionario_md5[remote_file] = md5
                                self.contabilizarTotais('arquivos_modificados', 1)
                    except:
                        print "    (novo):", arquivo + " (" + self.formataTamanhoArquivo(os.path.getsize(local_file)) + ") ",
                        self.contabilizarTotais('arquivos_novos', 1)
                        md5 = self.calcularMd5(local_file)
                        self.dicionario_md5[remote_file] = md5
                    if not is_up_to_date:
                        self.contabilizarTotais('tentativas', self.copiarArquivoParaServidor(local_file, remote_file))
            self.deletarRecursosRemotos(self.pastaDestino)
        except Exception, e:
            print '*** Exceçao Lançada ao copiar arquivo: %s: %s' % (e.__class__, e)
            sys.exit()
        print '=' * 60
        print 'Numero de tentativas para erro (retry):', self.getResultadoTotal('tentativas')
        print 'Total de diretorios criados:', self.getResultadoTotal('diretorios_criados')
        print 'Total de arquivos novos:', self.getResultadoTotal('arquivos_novos')
        print 'Total de arquivos modificados:', self.getResultadoTotal('arquivos_modificados')
        print 'Total de arquivos nao modificados:', self.getResultadoTotal('arquivos_naomodificados')
        print 'Total de diretorios remotos removidos:', self.getResultadoTotal('diretorios_removidos')
        print 'Total de arquivos remotos removidos:', self.getResultadoTotal('arquivos_removidos')
        print 'Total de diretorios:', self.getResultadoTotal('diretorios')
        print 'Total de arquivos:', self.getResultadoTotal('arquivos')
        print 'Completo!'
        print '=' * 60