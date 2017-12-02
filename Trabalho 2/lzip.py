#!/usr/bin/python
# -*- coding:utf-8 -*-

import argparse
import sys
import struct
import time
import datetime


def read_log(file):
    date = 'Início da execução da compressão/descompressão: '
    duration = 'Duração da execução: '
    pointer = 0
    holder = []
    stats = {}
    pid = 0
    size_counter = 0
    with open(file, "rb") as fr:
        for i in range(3):
            date += str(struct.unpack("i", fr.read(4))[0]) + ('/' if i < 2 else '')
        date += ', '
        for i in range(4):
            date += str(struct.unpack("i", fr.read(4))[0]) + (':' if i < 3 else '')
        duration += datetime.datetime.utcfromtimestamp(
            struct.unpack("d", fr.read(8))[0]).strftime("%H:%M:%S:%f")
        while fr.read(1):
            fr.seek(-1, 1)
            if pointer == 0:
                pid = struct.unpack("i", fr.read(4))[0]
                if pid not in stats:
                    stats[pid] = []
                    pointer += 1
            elif pointer == 1:
                size = struct.unpack("B", fr.read(1))[0]
                name = struct.unpack("%ds" % size, fr.read(size))[0]
                holder.append(name)
                pointer += 1
            elif pointer == 2:
                size_file = struct.unpack("i", fr.read(4))[0]
                holder.append(size_file)
                pointer += 1
            elif pointer == 3:
                timer = struct.unpack("d", fr.read(8))[0]
                holder.append(timer)
                stats[pid].append(holder)
                holder = []
                pointer = 0
    print date
    print duration
    for process in stats:
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
    """
    description = "Lê o histórico de execução do programa pzip"
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("file", type=str, metavar="file", help="Ficheiro de log", nargs=1)
    args = parser.parse_args()
    if not args.file and not sys.stdin.isatty():
        args.file = filter(lambda x: x != '', sys.stdin.read().split("\n"))
    if not args.file and sys.stdin.isatty():
        args.file = filter(lambda x: x != '', sys.stdin.read().split("\n"))
    read_log(args.file[0])
