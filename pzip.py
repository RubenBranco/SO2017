#!/usr/bin/python

import argparse
from zipfile import ZipFile
from multiprocessing import Process, Value, Array, Semaphore, Queue
from ctypes import c_char_p
import os


class PZip:
    def __init__(self, files, mode, t, processes):
        self.files = Array(c_char_p, len(files))
        self.pointer = Value("i", 0)
        self.file_init(files)
        self.sem = Semaphore(1)
        self.t = t
        self.errorChecker = Value('i', 0)
        for i in range(processes[0]):
            newP = Process(target=(self.zip if mode == 'c' else self.unzip))
            newP.start()

    def file_init(self, files):
        for i in range(len(files)):
            self.files[i] = files[i]

    def zip(self):
        while self.pointer.value < len(self.files) and ((self.errorChecker.value == 0 and self.t) or not self.t):
            self.sem.acquire()
            iterator = self.pointer.value
            self.pointer.value += 1
            self.sem.release()
            if iterator < len(self.files):
                File = self.files[iterator]
                if os.path.isfile(File):
                    with ZipFile(File + '.zip', 'w') as zipfile:
                        zipfile.write(File)
                else:
                    self.errorChecker.value = 1

    def unzip(self):
        while self.pointer.value < len(self.files) and ((self.errorChecker.value == 0 and self.t) or not self.t):
            self.sem.acquire()
            iterator = self.pointer.value
            self.pointer.value += 1
            self.sem.release()
            if iterator < len(self.files):
                File = self.files[iterator]
                if os.path.isfile(File):
                    with ZipFile(File, 'r') as zipfile:
                        zipfile.extractall('.')
                else:
                    self.errorChecker.value = 1


if __name__ == '__main__':
    description = 'Comprime e descomprime conjuntos de ficheiros paralelamente'
    parser = argparse.ArgumentParser(description=description)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-c", dest="mode", help="Comprimir ficheiros", action="store_const", const="c")
    group.add_argument("-d", dest="mode", help="Descomprimir ficheiros", action="store_const", const="d")
    parser.add_argument("-p", metavar="configs", dest="parallel", help="Numero de processos permitidos", type=int,
                        nargs=1, default=[1])
    parser.add_argument("-t", dest="t", help="Obriga a suspensao de execucao caso um ficheiro seja"
                                                                "nao existente", action="store_true")
    parser.add_argument("files", type=str, metavar="files", nargs="+", help="Ficheiros para comprimir/descomprimir")
    args = parser.parse_args()
    zipper = PZip(args.files, args.mode, args.t, args.parallel)
