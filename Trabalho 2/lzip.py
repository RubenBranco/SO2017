#!/usr/bin/python
# -*- coding:utf-8 -*-

import argparse
import sys
import struct
import datetime


def read_log(file):
    """
    Lê um ficheiro file, binario, que contem os estados de uma execucao do programa
    Requires: file e' uma string
    Ensures: A impressao para stdout do estado de execucao do programa contido em file
    """
    date = 'Início da execução da compressão/descompressão: '
    duration = 'Duração da execução: '
    holder = []
    stats = {}
    pid = 0
    size_counter = 0
    with open(file, "rb") as fr:
        for i in range(3):
            # A data tem dia / mes / ano, portanto e necessario ler 3 vezes e concatenar
            date += str(struct.unpack("i", fr.read(4))[0]) + ('/' if i < 2 else '')
        date += ', '
        for i in range(4):
            # Tempo tem hh:mm:ss:ms portanto e' necessario ler 4 vezes e concatenar
            date += str(struct.unpack("i", fr.read(4))[0]) + (':' if i < 3 else '')
        duration += datetime.datetime.utcfromtimestamp(
            struct.unpack("d", fr.read(8))[0]).strftime("%H:%M:%S:%f")  # Indicar a estrutura da string do timestamp,
        while fr.read(1):                                               # Que e' a duracao de programa
            fr.seek(-1, 1)  # Ver se existe ainda algo no ficheiro e voltar atras
            pid = struct.unpack("i", fr.read(4))[0]
            if pid not in stats:
                stats[pid] = []
            size = struct.unpack("i", fr.read(4))[0]  # Tamanho da string
            name = struct.unpack("%ds" % size, fr.read(size))[0]  # Ir buscar a string com tamanho size
            holder.append(name)
            size_file = struct.unpack("i", fr.read(4))[0]
            holder.append(size_file)
            timer = struct.unpack("d", fr.read(8))[0]
            holder.append(timer)
            stats[pid].append(holder)
            holder = []
    print date  # A partir daqui e' imprimir os dados recolhidos
    print duration
    for process in stats:  # Para cada processo, imprimir os ficheiros que fez
        process_counter = 0
        print "Processo: " + str(process) + ""
        for processed_file in stats[process]:
            print "\tFicheiro processado: " + processed_file[0]
            print "\t\ttempo de compressão/descompressão: " + datetime.datetime.utcfromtimestamp(
                processed_file[2]).strftime("%H:%M:%S:%f")
            print "\t\tdimensão do ficheiro depois de comprimido/descomprimido: " + str(processed_file[1])
            process_counter += processed_file[1]
        size_counter += process_counter
        print "\tVolume total de dados escritos em ficheiros: " + str(process_counter)
    print "Volume total de dados escritos em todos os ficheiros: " + str(size_counter)


if __name__ == "__main__":
    """
    Argparse e' usado para fazer parsing dos argumentos da linha de comando.
    
    description = "Lê o histórico de execução do programa pzip"
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("file", type=str, metavar="file", help="Ficheiro de log", nargs=1)
    args = parser.parse_args()
    if not args.file and not sys.stdin.isatty():
        args.file = filter(lambda x: x != '', sys.stdin.read().split("\n"))
    if not args.file and sys.stdin.isatty():
        args.file = filter(lambda x: x != '', sys.stdin.read().split("\n"))
    read_log(args.file[0])
    """
    read_log("stat")
