#!/usr/bin/python
# -*- coding:utf-8 -*-

import argparse
from zipfile import ZipFile
from multiprocessing import Process, Value, Array
from ctypes import c_char_p
from multiprocessing import Semaphore, Queue
import os


class PZip:
    def __init__(self, files, mode, t, processes):
        """
        Construtor de PZip.

        Requires: files e' uma lista de strings, mode e' um a string que toma valores c ou d, t e' um boolean e processes
        e' um int.
        Ensures: Zip ou unzip de ficheiros contidos em 'files'
        """
        self.files = Array(c_char_p, len(files))
        self.pointer = Value("i", 0)
        self.file_init(files)
        self.sem = Semaphore(1)
        self.t = t
        self.queue = Queue()
        for i in range((processes[0] if processes[0] <= len(files) else len(files))):
            newP = Process(target=(self.zip if mode == 'c' else self.unzip))
            newP.start()

    def file_init(self, files):
        """
        Inicializa o array de memoria partilhada com os ficheiros passados no construtor.

        Requires: Files e' uma lista de strings.
        Ensures: A populacao do array de memoria partilhada self.files com as strings contidas em 'files'.
        """
        for i in range(len(files)):
            self.files[i] = files[i]

    def zip(self):
        """
        Faz zip de ficheiros.

        Requires: objeto self.
        Ensures: Zip de ficheiros.
        """
        error_flag = False  # Flag que indica se neste ou noutro processo ocorreu um erro.
        while self.pointer.value < len(self.files) and not error_flag:
            if (self.t and self.queue.empty()) or not self.t:
                # Se o modo e' t e a queue estiver empty pode avancar, a queue nao esta empty se houver um erro
                # Se o modo nao for t pode avancar sem restricoes
                self.sem.acquire()
                iterator = self.pointer.value
                self.pointer.value += 1
                self.sem.release()
                if iterator < len(self.files):  # Iterator e' o ficheiro que deve ser utilizado pelo processo
                    File = self.files[iterator]
                    if os.path.isfile(File):  # Ver se o ficheiro existe
                        with ZipFile(File + '.zip', 'w') as zipfile:
                            zipfile.write(File)  # Zip
                    else:
                        print "O ficheiro", File, "não existe."  # Se nao exister, avisa o utilizador
                        self.queue.put('1')  # Mete um '1' na queue para assinalar que ha um erro
                        error_flag = True  # Atualiza a sua propria flag
            else:
                error_flag = True  # Se for t e a queue nao esta vazia entao existe erro, por flag a true e sair

    def unzip(self):
        """
        Faz unzip de um ficheiro zip.

        Requires: objeto self.
        Ensures: O unzip de um ficheiro zip.
        """
        error_flag = False
        while self.pointer.value < len(self.files) and not error_flag:
            if (self.t and self.queue.empty()) or not self.t:
                # Se o modo e' t e a queue estiver empty pode avancar, a queue nao esta empty se houver um erro
                # Se o modo nao for t pode avancar sem restricoes
                self.sem.acquire()
                iterator = self.pointer.value
                self.pointer.value += 1
                self.sem.release()
                if iterator < len(self.files):  # Iterator e' o ficheiro que deve ser utilizado pelo processo
                    File = self.files[iterator]
                    if os.path.isfile(File):  # Ver se o ficheiro existe
                        with ZipFile(File, 'r') as zipfile:
                            zipfile.extractall('.')  # Unzip
                    else:
                        print "O ficheiro", File, "não existe."  # Se nao exister, avisa o utilizador
                        self.queue.put('1')  # Mete um '1' na queue para assinalar que ha um erro
                        error_flag = True  # Atualiza a sua propria flag
            else:
                error_flag = True  # Se for t e a queue nao esta vazia entao existe erro, por flag a true e sair 


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
