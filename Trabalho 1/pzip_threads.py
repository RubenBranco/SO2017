#!/usr/bin/python
# -*- coding:utf-8 -*-

import argparse
from zipfile import ZipFile
from multiprocessing import Semaphore
from threading import Thread
import os
import sys


class PZip:
    def __init__(self, Files, mode, t, threads):
        """
        Construtor de PZip.
        Requires: files e' uma lista de strings, mode e' um a string que toma valores c ou d, t e' um boolean e threads
        e' um int.
        Ensures: Zip ou unzip de ficheiros contidos em 'files'
        """
        self.files = Files
        global pointer
        pointer = 0
        self.sem = Semaphore(1)
        self.t = t
        self.totalFilesSem = Semaphore(1)
        global totalFiles
        totalFiles = 0
        global error_flag
        error_flag = False
        threadList = [Thread(target=(self.zip if mode == 'c' else self.unzip)) for i in range((threads[0] if threads[0] <= len(Files) else len(Files)))]
        for thread in threadList:
            thread.start()
        for thread in threadList:
            thread.join()
        print "Foram", ("comprimidos" if mode == 'c' else "descomprimidos"), str(totalFiles), "ficheiros."

    def zip(self):
        """
        Faz zip de ficheiros.
        Requires: objeto self.
        Ensures: Zip de ficheiros.
        """
        global pointer
        global error_flag
        global totalFiles
        while pointer < len(self.files) and ((self.t and not error_flag) or not self.t):
            # Se o modo e' t e a error_flag nao for false entao pode avancar
            # Se o modo nao for t pode avancar sem restricoes
            self.sem.acquire()
            iterator = pointer
            pointer += 1
            self.sem.release()
            if iterator < len(self.files):  # Iterator e' o ficheiro que deve ser utilizado pela thread
                File = self.files[iterator]
                if os.path.isfile(File):  # Ver se o ficheiro existe
                    with ZipFile(File + '.zip', 'w') as zipfile:
                        zipfile.write(File)  # Zip
                    self.totalFilesSem.acquire()
                    totalFiles += 1
                    self.totalFilesSem.release()
                else:
                    print "O ficheiro", File, "não existe."  # Se nao existir, avisa o utilizador
                    error_flag = True  # Atualiza a sua propria flag

    def unzip(self):
        """
        Faz unzip de um ficheiro zip.
        Requires: objeto self.
        Ensures: O unzip de um ficheiro zip.
        """
        global pointer
        global error_flag
        global totalFiles
        while pointer < len(self.files) and ((self.t and not error_flag) or not self.t):
            # Se o modo nao for t pode avancar sem restricoes
            # Se o modo e' t e a error_flag nao for false entao pode avancar
            self.sem.acquire()
            iterator = pointer
            pointer += 1
            self.sem.release()
            if iterator < len(self.files):  # Iterator e' o ficheiro que deve ser utilizado pela thread
                File = self.files[iterator]
                if os.path.isfile(File):  # Ver se o ficheiro existe
                    with ZipFile(File, 'r') as zipfile:
                        zipfile.extractall('.')  # Unzip
                    self.totalFilesSem.acquire()
                    totalFiles += 1
                    self.totalFilesSem.release()
                else:
                    print "O ficheiro", File, "não existe."  # Se nao exister, avisa o utilizador
                    error_flag = True  # Atualiza a sua propria flag


if __name__ == '__main__':
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
    parser.add_argument("-t", dest="t", help="Obriga a suspensao de execucao caso um ficheiro seja"
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
    PZip(args.files, args.mode, args.t, args.parallel)
