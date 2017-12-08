#!/usr/bin/python
# -*- coding:utf-8 -*-

import argparse
from zipfile import ZipFile
from multiprocessing import Process, Value, Semaphore, Array
from ctypes import c_char_p
import signal
import time
import os
import sys
import datetime
import struct

totalFiles = Value('i', 0)
totalFilesSem = Semaphore(1)
errorChecker = Value('i', 0)
volume = Value("i", 0)
pointer = Value("i", 0)
sem = Semaphore(1)


def handle_files(files, t, f, names, times, sizes, pid):
    """
    Faz zip e  unzip de ficheiros.
    Requires: files é uma lista de ficheiros, t é um boolean, f é uma string ou None, names, times, sizes e pid
    sao None ou Array()
    Ensures: Zip/unzip de ficheiros.
    """
    while pointer.value < len(files) and ((errorChecker.value == 0 and t) or not t) and errorChecker.value < 2:
        # Se o modo for t so pode avançar se errorChecker for 0 (nao ha erro) e ainda houver ficheiros
        # Se o modo nao for t entao pode avancar sem restricoes enquanto houver ficheiros
        time1 = time.time()
        sem.acquire()  # Mutex para garantir que um ficheiro so e' zipado por um processo
        iterator = pointer.value
        pointer.value += 1
        sem.release()
        if iterator < len(files):  # Iterator e' o ficheiro que deve ser utilizado pelo processo
            File = files[iterator]
            if os.path.isfile(File):  # Ver se o ficheiro existe
                if mode == 'c':
                    with ZipFile(File + '.zip', 'w') as zipfile:
                        zipfile.write(File)  # Zip
                else:
                    with ZipFile(File, 'r') as zipfile:
                        zipfile.extractall('.')  # Unzip
                totalFilesSem.acquire()
                totalFiles.value += 1
                file_size = (os.path.getsize(File + '.zip') if mode == 'c' else os.path.getsize(File.strip(".zip")))
                volume.value += file_size
                totalFilesSem.release()
                # Por informacoes do processo e ficheiro para os arrays para serem escritos em ficheiro binario
                if f is not None:
                    names[iterator] = File
                    times[iterator] = time.time() - time1
                    sizes[iterator] = file_size
                    pid[iterator] = os.getpid()
            else:
                print "O ficheiro", File, "não existe."  # Se nao exister, avisa o utilizador
                errorChecker.value = 1  # Ha erro e a flag atualiza


def sigint_handler(sig, NULL):
    """
    Handler de sinal de SO SIGINT para terminar a execucao
    """
    errorChecker.value = 2  # Faz com que parem de processar ficheiros


def sigalrm_handler(sig, NULL):
    """
    Handler de sinal de SO SIGALRM que imprime o estado do programa
    """
    print "Foram", ("comprimidos" if mode == 'c' else "descomprimidos"), \
        str(totalFiles.value), "ficheiros."
    print "Foram", ("comprimidos" if mode == 'c' else "descomprimidos"), \
        str(volume.value / 1024), "Kb de ficheiros"
    print "Tempo de execucao:", (time.time() - timer) * 1000


def log_writer(files, date, end_timer, pid, names, sizes, times, f):
    """
    Escreve um ficheiro log binario com os estados da execucao do programa

    Requires: self object
    Ensures: A escrita de um ficheiro binario log
    """
    status = []
    for i in range(len(files)):
        if pid[i] != 0:
            status.append([pid[i], names[i], sizes[i], times[i]])
    with open(f, "wb") as fw:
        for num in [date.day, date.month, date.year, date.hour,
                             date.minute, date.second, date.microsecond]:
            fw.write(struct.pack("i", num))  # Escrever a data de comeco
        fw.write(struct.pack("d", end_timer))  # Escrever data do fim
        for stat in status:
            # Para cada ficheiro e' escrito na memoria sequencialmente
            size = len(bytes(stat[1]))
            fw.write(struct.pack("i", stat[0]))  # pid do processo que trabalho no ficheiro
            fw.write(struct.pack("i", size))
            fw.write(struct.pack("%ds" % size, stat[1]))  # Nome do ficheiro
            fw.write(struct.pack("i", stat[2]))  # Tamanho do ficheiro apos
            fw.write(struct.pack("d", stat[3]))  # Tempo que demorou a comprimir/descomprimir


def main(args, timer):
    files = args.files
    t = args.t
    f = args.f
    date = datetime.datetime.now()
    names = (None if f is None else Array(c_char_p, len(files)))  # self.names, sizes e times sao usados como listas de informacao para se tiver que escrever
    sizes = (None if f is None else Array("i", len(files)))  # o ficheiro binario
    times = (None if f is None else Array("d", len(files)))
    pid = (None if f is None else Array("i", len(files)))
    signal.signal(signal.SIGINT, sigint_handler)  # SIGINT (CTRL^C) para terminar a execucao do programa
    if args.a is not None:
        signal.signal(signal.SIGALRM, sigalrm_handler)  # Handler do sinal
        signal.setitimer(signal.ITIMER_REAL, 1, args.a)  # Timer, a cada 'a' segundos envia um sinal SIGALRM q e apanhado
    processos = [Process(target=handle_files, args=(files, t, f, names, times, sizes, pid)) for _
                 in range((args.parallel[0] if args.parallel[0] <= len(files) else len(files)))]
    for i in range(len(processos)):
        processos[i].start()
    for i in range(len(processos)):
        processos[i].join()
    end_timer = time.time() - timer
    if f is not None:
        log_writer(files, date, end_timer, pid, names, sizes, times, f)
    print "Foram", ("comprimidos" if mode == 'c' else "descomprimidos"), str(totalFiles.value), "ficheiros."
    print "Foram", ("comprimidos" if mode == 'c' else "descomprimidos"), str(volume.value / 1024), \
        "Kb de ficheiros"
    print "Tempo de execucao:", end_timer


"""
Argparse e' usado para fazer parsing dos argumentos da linha de comando.
"""
timer = time.time()
description = 'Comprime e descomprime conjuntos de ficheiros paralelamente'
parser = argparse.ArgumentParser(description=description)
group = parser.add_mutually_exclusive_group(required=True)  # Grupo exclusivo para -c ou -d (zip ou unzip)
group.add_argument("-c", dest="mode", help="Comprimir ficheiros", action="store_const", const="c")
group.add_argument("-d", dest="mode", help="Descomprimir ficheiros", action="store_const", const="d")
parser.add_argument("-p", metavar="processes", dest="parallel", help="Numero de processos permitidos", type=int,
                    nargs=1, default=[1])
parser.add_argument("-t", dest="t", help="Obriga a suspensao de execucao caso um ficheiro seja "
                                         "nao existente", action="store_true")  # True or false para modo t
parser.add_argument("-a", dest="a", help="Escreve o estado da execucao a cada intervalo de tempo "
                                         "indicado", type=int)
parser.add_argument("-f", dest="f", help="Guardar o histórico da execucao do programa num ficheiro binario indicado"
                    , type=str)
parser.add_argument("files", type=str, metavar="files", nargs="*", help="Ficheiros para comprimir/descomprimir")
args = parser.parse_args()
if not args.files and not sys.stdin.isatty():
    # stdin.isatty retorna False se houver algo no stdin, ou seja, pzip -c|-d < ficheiro.txt
    args.files = filter(lambda x: x != '', sys.stdin.read().split("\n"))
elif not args.files and sys.stdin.isatty():
    # Se nao tiver algo no stdin e nao for especificado ficheiros, perguntar ao utilizador
    args.files = filter(lambda x: x != '', sys.stdin.read().split("\n"))
if args.parallel[0] <= 0:
    parser.error("Tem de criar 1 ou mais processos")
mode = args.mode
main(args, timer)
