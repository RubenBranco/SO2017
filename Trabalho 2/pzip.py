#!/usr/bin/python
# -*- coding:utf-8 -*-

import argparse
from zipfile import ZipFile
from multiprocessing import Process, Value, Semaphore
import signal
import time
import os
import sys


class PZip:
    def __init__(self, timer, files, mode, t, processes, f, a):
        """
        Construtor de PZip.
        Requires: files e' uma lista de strings, mode e' um a string que toma valores c ou d, t e' um boolean e
        processes e' um int.
        Ensures: Zip ou unzip de ficheiros contidos em 'files'
        """
        self.files = files
        self.pointer = Value("i", 0)
        self.sem = Semaphore(1)
        self.t = t
        self.f = f
        signal.signal(signal.SIGINT, self.sigint_handler)
        if a is not None:
            signal.signal(signal.SIGALRM, self.sigalrm_handler)
            signal.setitimer(signal.ITIMER_REAL, 1, a)
        self.mode = mode
        self.timer = timer
        self.totalFiles = Value('i', 0)
        self.totalFilesSem = Semaphore(1)
        self.errorChecker = Value('i', 0)
        self.volume = Value("i", 0)
        processos = [Process(target=(self.zip if mode == 'c' else self.unzip)) for i
                     in range((processes[0] if processes[0] <= len(files) else len(files)))]
        for i in range(len(processos)):
            processos[i].start()
        for i in range(len(processos)):
            processos[i].join()
        print "Foram", ("comprimidos" if mode == 'c' else "descomprimidos"), str(self.totalFiles.value), "ficheiros."
        print "Foram", ("comprimidos" if mode == 'c' else "descomprimidos"), str(self.volume.value / 1024), \
            "Kb de ficheiros"
        print "Tempo de execucao:", time.time() - timer

    def zip(self):
        """
        Faz zip de ficheiros.
        Requires: objeto self.
        Ensures: Zip de ficheiros.
        """
        while self.pointer.value < len(self.files) and ((self.errorChecker.value == 0 and self.t) or not self.t):
            # Se o modo for t so pode avançar se errorChecker for 0 (nao ha erro) e ainda houver ficheiros
            # Se o modo nao for t entao pode avancar sem restricoes enquanto houver ficheiros
            self.sem.acquire()  # Mutex para garantir que um ficheiro so e' zipado por um processo
            iterator = self.pointer.value
            self.pointer.value += 1
            self.sem.release()
            if iterator < len(self.files):  # Iterator e' o ficheiro que deve ser utilizado pelo processo
                File = self.files[iterator]
                if os.path.isfile(File):  # Ver se o ficheiro existe
                    with ZipFile(File + '.zip', 'w') as zipfile:
                        zipfile.write(File)  # Zip
                    self.totalFilesSem.acquire()
                    self.totalFiles.value += 1
                    self.volume.value += os.path.getsize(File)
                    self.totalFilesSem.release()
                else:
                    print "O ficheiro", File, "não existe."  # Se nao exister, avisa o utilizador
                    self.errorChecker.value = 1  # Ha erro e a flag atualiza

    def unzip(self):
        """
        Faz unzip de um ficheiro zip.
        Requires: objeto self.
        Ensures: O unzip de um ficheiro zip.
        """
        while self.pointer.value < len(self.files) and ((self.errorChecker.value == 0 and self.t) or not self.t):
            # Se o modo for t so pode avançar se errorChecker for 0 (nao ha erro) e ainda houver ficheiros
            # Se o modo nao for t entao pode avancar sem restricoes enquanto houver ficheiros
            self.sem.acquire()  # Mutex para garantir que um ficheiro so e' unzipado por um processo
            iterator = self.pointer.value
            self.pointer.value += 1
            self.sem.release()
            if iterator < len(self.files):  # Iterator e' o ficheiro que deve ser utilizado pelo processo
                File = self.files[iterator]
                if os.path.isfile(File):  # Ver se o ficheiro existe
                    with ZipFile(File, 'r') as zipfile:
                        zipfile.extractall('.')  # Unzip
                    self.totalFilesSem.acquire()
                    self.totalFiles.value += 1
                    self.volume.value += os.path.getsize(File)
                    self.totalFilesSem.release()
                else:
                    print "O ficheiro", File, "não existe."  # Se nao exister, avisa o utilizador
                    self.errorChecker.value = 1  # Ha erro e a flag atualiza

    def sigint_handler(self, sig, NULL):
        self.errorChecker.value = 1
        self.t = True

    def sigalrm_handler(self, sig, NULL):
        print "Foram", ("comprimidos" if self.mode == 'c' else "descomprimidos"), \
            str(self.totalFiles.value), "ficheiros."
        print "Foram", ("comprimidos" if self.mode == 'c' else "descomprimidos"), \
            str(self.volume.value / 1024), "Kb de ficheiros"
        print "Tempo de execucao:", time.time() - timer


if __name__ == '__main__':
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
    PZip(timer, args.files, args.mode, args.t, args.parallel, args.f, args.a)
