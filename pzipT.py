#!/usr/bin/python
# -*- coding:utf-8 -*-

import argparse
from zipfile import ZipFile
from multiprocessing import Semaphore
from ctypes import c_char_p
from threading import Thread
import os


class PZip:
    def __init__(self, Files, mode, t, threads):
        """
        Construtor de PZip.
        Requires: files e' uma lista de strings, mode e' um a string que toma valores c ou d, t e' um boolean e threads
        e' um int.
        Ensures: Zip ou unzip de ficheiros contidos em 'files'
        """
        global files
        files = Files
        global pointer
        pointer = 0
        self.sem = Semaphore(1)
        self.t = t
        global error_flag
        error_flag = False
        for i in range((threads[0] if threads[0] <= len(files) else len(files))):
            newT = Thread(target=(self.zip if mode == 'c' else self.unzip))
            newT.start()

    def zip(self):
        """
        Faz zip de ficheiros.
        Requires: objeto self.
        Ensures: Zip de ficheiros.
        """
        global pointer
        global files
        global error_flag
        while pointer < len(files) and ((self.t and not error_flag) or not self.t):
                # Se o modo e' t e a error_flag nao for false entao pode avancar
                # Se o modo nao for t pode avancar sem restricoes
                self.sem.acquire()
                iterator = pointer
                pointer += 1
                self.sem.release()
                if iterator < len(files):  # Iterator e' o ficheiro que deve ser utilizado pela thread
                    File = files[iterator]
                    if os.path.isfile(File):  # Ver se o ficheiro existe
                        with ZipFile(File + '.zip', 'w') as zipfile:
                            zipfile.write(File)  # Zip
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
        global files
        global error_flag
        while pointer < len(files) and ((self.t and not error_flag) or not self.t):
                # Se o modo nao for t pode avancar sem restricoes
                # Se o modo e' t e a error_flag nao for false entao pode avancar
                self.sem.acquire()
                iterator = pointer
                pointer += 1
                self.sem.release()
                if iterator < len(files):  # Iterator e' o ficheiro que deve ser utilizado pela thread
                    File = files[iterator]
                    if os.path.isfile(File):  # Ver se o ficheiro existe
                        with ZipFile(File, 'r') as zipfile:
                            zipfile.extractall('.')  # Unzip
                    else:
                        print "O ficheiro", File, "não existe."  # Se nao exister, avisa o utilizador
                        error_flag = True  # Atualiza a sua propria flag


if __name__ == '__main__':
    """
    Argparse e' usado para fazer parsing dos argumentos da linha de comando.
    """
    description = 'Comprime e descomprime conjuntos de ficheiros paralelamente'
    parser = argparse.ArgumentParser(description=description)
    group = parser.add_mutually_exclusive_group()  # Grupo exclusivo para -c ou -d (zip ou unzip)
    group.add_argument("-c", dest="mode", help="Comprimir ficheiros", action="store_const", const="c")
    group.add_argument("-d", dest="mode", help="Descomprimir ficheiros", action="store_const", const="d")
    parser.add_argument("-p", metavar="configs", dest="parallel", help="Numero de processos permitidos", type=int,
                        nargs=1, default=[1])
    parser.add_argument("-t", dest="t", help="Obriga a suspensao de execucao caso um ficheiro seja"
                                             "nao existente", action="store_true")
    parser.add_argument("files", type=str, metavar="files", nargs="+", help="Ficheiros para comprimir/descomprimir")
    args = parser.parse_args()
    zipper = PZip(args.files, args.mode, args.t, args.parallel)
