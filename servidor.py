#!/usr/bin/env python
#-*- coding:utf-8 -*-

# cuidado! bem inseguro pra usar fora de um ambiente
# controlado!
#

import readline
from socket import socket
from binascii import *
from fnmatch import fnmatch
import os, random

class Conexao:
    def __init__(self, c):
        self.c = c
        self.buf = ''
    
    def envia(self, cmd, args=''):
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
        self.nodes = []
        filename = os.path.join( os.path.dirname(__file__), 'config.dat' )
        print "= Minhas Configurações: %s" % filename
        print "= Diretório atual: %s" % os.getcwd()
        f = open( filename )
        lines = f.readlines()
        f.close()
        for line in lines:
            line = line.strip()
            if len(line) == 0: continue
            if line[0] == '#': continue
            termos = line.split(':')
            if len(termos) != 2: continue
            fields,args = termos[0], termos[1]
            fields = fields.split()
            if len(fields) != 3: continue
            self.nodes.append( (fields[0], fields[1], int(fields[2]), args) )


print "= Inicializando servidor..."
cfg = Config()

sockets = []
for i in range(len(cfg.nodes)):
    node_id, node_host, node_port, node_args = cfg.nodes[i]
    print "= Conectando em %s (%s, porta %d)..." % (node_id, node_host, node_port)
    
    sc = socket()
    try:
        sc.connect( (node_host, node_port) )
    except:
        print "= !! Falhou ao conectar em %s !! " % node_id
        del cfg.nodes[i]
        i -= 1
        continue

    print "= Conectado em %s OK" % node_id

    c = Conexao(sc)
    c.envia( 'set_id', node_id )
    c.envia( 'set_args', node_args )

    sockets.append( (sc,c) )


print "= Conexões OK: %d; abrindo terminal. Para ajuda, digite <help>." % len(sockets)
while True:
    s = raw_input('> ')
    if len(s.strip()) == 0: continue
    
    termos = s.split()
    
    cmd = termos[0]
    args = termos[1:]
    if len(args) > 0:
        node_mask = args[0]
    else:
        node_mask = None
    args_resto = ' '.join(args[1:])

    selected_nodes = []
    if node_mask != None:
        for i in range(len(cfg.nodes)):
            node_id, node_host, node_porta, node_args = cfg.nodes[i]
            sc,c = sockets[i]
            if fnmatch( node_id, node_mask ):
                selected_nodes.append( (node_id,c) )

        
    if cmd == 'help':
        print "= Comandos:"
        print "=   set_id node* <nome>"
        print "=   set_args node* <xx yy...>"
        print "=   envia node* <arq>"
        print "=   recebe node* <arq>"
        print "=   exec node* <cmd>"
        print "=   resp node*"
        print "=   check node*"
        print "=   ping node*"
        print "=   encerra node*"
        print "=   list"        

    elif cmd == 'set_id':
        if len(selected_nodes) != 1:
            print "= Só pode mudar o ID de um node por vez"
        else:
            for i in range(len(cfg.nodes)):
                node_id, node_host, node_porta, node_args = cfg.nodes[i]
                if node_id != selected_nodes[0][0]: continue
                node_id = args_resto
                cfg.nodes[i] = node_id, node_host, node_porta, node_args
                break
            c.envia('set_id', args_resto )
                
    elif cmd == 'set_args':
        if len(selected_nodes) == 0: print "= Nenhum node selecionado"
        for node_id, c in selected_nodes:
            c.envia('set_args', args_resto )

    elif cmd == 'envia':
        if len(selected_nodes) == 0: print "= Nenhum node selecionado"

        arq = args_resto
        f = open(arq)
        dat = f.read()
        f.close()
        
        for node_id, c in selected_nodes:
            print "= Enviando dados do arquivo %s para %s..." % (arq, node_id)
            c.envia('envia', arq)
            c.envia_dados(dat)
            print "= OK"
        
    
    elif cmd == 'recebe':
        if len(selected_nodes) == 0: print "= Nenhum node selecionado"
        arq = args_resto

        for node_id, c in selected_nodes:
            print "= Obtendo arquivo %s de %s..." % (arq, node_id)
            c.envia( 'recebe', arq )
        
            dat = c.recebe_dados()
            f = open( 'from_' + node_id + ('_%s' % arq), 'w' )
            f.write(dat)
            f.close()
            
            print "= OK"


    elif cmd == 'exec':
        if len(selected_nodes) == 0: print "= Nenhum node selecionado"
        for node_id, c in selected_nodes:
            c.envia('exec', args_resto )

    elif cmd == 'resp':
        if len(selected_nodes) == 0: print "= Nenhum node selecionado"
        for node_id, c in selected_nodes:
            c.envia('resp')
            print "= %s: %s" % (node_id, c.recebe_dados())
                
    elif cmd == 'check':
        if len(selected_nodes) == 0: print "= Nenhum node selecionado"
        glinhas = {}
        for node_id, c in selected_nodes:
            c.envia('check')
            linhas = c.recebe_dados().split('\n')
            for linha in linhas:
                if not (linha in glinhas): glinhas[linha] = []
                glinhas[linha].append(node_id)
        for linha in glinhas:
            print '= %s: %s' % ( linha, str(glinhas[linha]) )

    elif cmd == 'ping':
        if len(selected_nodes) == 0: print "= Nenhum node selecionado"
        for node_id, c in selected_nodes:
            x = random.randint(1,100)
            print "= ping %d em %s..." % (x, node_id)
            c.envia('ping', '%d' % x )
            print "= %s: %s" % (node_id, c.recebe_dados() )
            
    elif cmd == 'encerra':
        for node_id, c in selected_nodes:
            c.envia('encerra')
            c.encerra()
        break

    elif cmd == 'list':
        for i in range(len(cfg.nodes)):
            node_id, node_host, node_porta, node_args = cfg.nodes[i]
            print "= %s (%s, porta %d)" % (node_id, node_host, node_porta)

    else:
        print "Comando inválido <%s>. Digite <help>." % cmd


