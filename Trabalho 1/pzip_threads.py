#!/usr/bin/python
# -*- coding:utf-8 -*-

import argparse
from zipfile import ZipFile
from multiprocessing import Semaphore
from threading import Thread
import os
import sys


def handle_files(files, t):
    """
    Faz zip e  unzip de ficheiros.
    Requires: files é uma lista de ficheiros, t é um boolean
    Ensures: Zip/unzip de ficheiros.
    """
    global totalFiles
    global totalFilesSem
    global error_flag
    global pointer
    global sem
    while pointer.value < len(files) and ((errorChecker == 0 and t) or not t) and errorChecker < 2:
        # Se o modo for t so pode avançar se errorChecker for 0 (nao ha erro) e ainda houver ficheiros
        # Se o modo nao for t entao pode avancar sem restricoes enquanto houver ficheiros
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
                totalFilesSem.release()
            else:
                print "O ficheiro", File, "não existe."  # Se nao exister, avisa o utilizador
                errorChecker = 1  # Ha erro e a flag atualiza


def main(args):
    global totalFiles
    totalFiles = 0
    global totalFilesSem
    totalFilesSem = Semaphore(1)
    global error_flag
    error_flag = False
    global pointer
    pointer = 0
    global sem
    sem = Semaphore(1)
    files = args.files
    t = args.t
    threadList = [Thread(target=handle_files, args=(files, t)) for _ in
                  range((args.parallel[0] if args.parallel[0] <= len(args.files) else len(args.files)))]
    for i in range(len(threadList)):
        threadList[i].start()
    for i in range(len(threadList)):
        threadList[i].join()
    print "Foram", ("comprimidos" if mode == 'c' else "descomprimidos"), str(totalFiles), "ficheiros."


"""
Argparse e' usado para fazer parsing dos argumentos da linha de comando.
"""
description = 'Comprime e descomprime conjuntos de ficheiros paralelamente'
parser = argparse.ArgumentParser(description=description)
group = parser.add_mutually_exclusive_group(required=True)  # Grupo exclusivo para -c ou -d (zip ou unzip)
group.add_argument("-c", dest="mode", help="Comprimir ficheiros", action="store_const", const="c")
group.add_argument("-d", dest="mode", help="Descomprimir ficheiros", action="store_const", const="d")
parser.add_argument("-p", metavar="processes", dest="parallel", help="Numero de processos permitidos", type=int,
                    nargs=1, default=[1])
parser.add_argument("-t", dest="t", help="Obriga a suspensao de execucao caso um ficheiro seja "
                                         "nao existente", action="store_true")  # True or false para modo t
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
main(args)
