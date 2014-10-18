#!/usr/bin/env python
#-*- coding:utf-8 -*-

# cuidado! bem inseguro pra usar fora de um ambiente
# controlado!
#

from socket import socket, SOL_SOCKET, SO_REUSEADDR
from binascii import *
import time, subprocess
import sys, os

class Conexao:
    def __init__(self, c):
        self.c = c
        self.buf = ''
    
    def envia(self, cmd, args):
        self.c.sendall( '%20s ' % cmd )
        self.envia_dados( args )

    def recebe_linha(self):
        linha = ''
        while True:
            nl = self.buf.find('\n')
            if nl >= 0:
                linha = self.buf[0:nl]
                self.buf = self.buf[nl+1:]
                break
            resp = self.c.recv(4096)
            if resp == None or len(resp) == 0: break
            self.buf += resp

        linha = linha.strip()
        return linha

    def recebe_cmd(self):
        linha = self.recebe_linha()
        spc = linha.find(' ')
        if spc == -1:
            cmd = linha
            all_args = ''
        else:
            cmd = linha[0:spc]
            dat = linha[spc+1:].strip()
            if len(dat) > 0: dat = a2b_hex(dat).strip()
            all_args = dat
        args = all_args.split()
        return cmd, args, all_args

    def envia_dados(self, dat):
        if len(dat) == 0: dat = ''
        else: dat = b2a_hex(dat)
        self.c.sendall( dat + '\n' )

    def recebe_dados(self):
        dat = self.recebe_linha()
        if len(dat) > 0: dat = a2b_hex(dat)
        return dat

    def encerra(self):
        self.c.close()

class Config:
    def __init__(self):
        self.porta = 1234
        filename = os.path.join( os.path.dirname(__file__), 'config.dat' )
        print "- Minhas Configurações: %s" % filename
        print "- Diretório atual: %s" % os.getcwd()
        f = open( filename )
        lines = f.readlines()
        f.close()
        for line in lines:
            line = line.strip()
            if len(line) == 0: continue
            if line[0] == '#': continue
            termos = line.split()
            if len(termos) != 2: continue
            if termos[0] == 'porta': self.porta = int(termos[1])



def trata_conexao(c, info):
    print "- Servidor %s conectou aqui" % str(info)

    node_id = 'node_sem_nome'
    exec_args = ''
    exec_output = ''
    
    while True:
        cmd, args, all_args = c.recebe_cmd()
        
        if cmd == 'set_id':
            node_id = args[0]
            print "- Meu novo ID é: %s" % node_id
            
        elif cmd == 'set_args':
            exec_args = all_args
            print "- Argumentos recebidos: %s" % exec_args

        elif cmd == 'envia':
            nome_arq = args[0]

            print "- Recebendo arquivo <%s>..." % nome_arq
            data_arq = c.recebe_dados()
            
            f = open( nome_arq, 'w')
            f.write(data_arq)
            f.close()
            
            print "- Arquivo <%s> recebido, tamanho %d." % (nome_arq, len(data_arq))
        
        elif cmd == 'recebe':
            arq = all_args
            
            print "- Obtendo dados do arquivo <%s>..." % arq
            f = open(arq)
            data = f.read()
            f.close()
            
            c.envia_dados(data)
            print "- Dados enviados."

        elif cmd == 'exec':
            s = all_args
            s += " " + exec_args
            
            exec_output = ''
            print "- Executando comando: %s..." % s
            p = subprocess.Popen(s, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
            exec_output = p.stdout.read() + p.stderr.read()
            print "- Comando executado."

        elif cmd == 'resp':
            c.envia_dados( exec_output )

        elif cmd == 'check':
            arqs = os.listdir( os.path.dirname(__file__) )
            #arqs.remove( 'config.dat' )
            for i in range(len(arqs)):
                arq = arqs[i]
                t = time.localtime( os.path.getmtime(arq) )
                st = time.strftime("%Y-%m-%d %H:%M:%S",t)
                size = os.path.getsize(arq)
                arqs[i] += '  %s  %d bytes' % (st, size) 
            linhas = '\n'.join(arqs)
            c.envia_dados( linhas )
                        
        elif cmd == 'ping':
            print "- Recebido ping %s" % args[0]
            c.envia_dados( 'pong %s' % args[0] )
            
        elif cmd == 'encerra':
            print "- Encerrando..."
            time.sleep(1.0)        
            c.encerra()
            break
            
        else:
            print "- Erro: comando desconhecido: %s" % cmd
            print "- Fechando conexão..."
            break


print "- Inicializando Node..."
cfg = Config()

s = socket()
s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1) 
s.bind( ('localhost', cfg.porta) )

while True:
    print "- Escutando nova conexão na porta %d..." % cfg.porta
    s.listen( 1 )
    c, info = s.accept()
    trata_conexao( Conexao(c), info )

