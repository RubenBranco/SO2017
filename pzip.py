#!/usr/bin/python

import argparse
from zipfile import ZipFile
from multiprocessing import Process, Value, Array
import ctypes


class PZip:
    def __init__(self, files, mode, t, processes=1):
        self.files = Array(ctypes.c_char_p, files)
        self.processes = processes
        self.mode = mode
        self.t = t
        file1 = self.files.pop()
        print(file1)
        print(self.files[0])
if __name__ == '__main__':
    description = 'Comprime e descomprime conjuntos de ficheiros paralelamente'
    parser = argparse.ArgumentParser(description=description)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-c", dest="mode", help="Comprimir ficheiros", action="store_const", const="c")
    group.add_argument("-d", dest="mode", help="Descomprimir ficheiros", action="store_const", const="d")
    parser.add_argument("-p", metavar="configs", dest="parallel", help="Numero de processos permitidos", type=int,
                        nargs=1)
    parser.add_argument("-t", dest="t", help="Obriga a suspensao de execucao caso um ficheiro seja"
                                                                "nao existente", action="store_true")
    parser.add_argument("files", type=str, metavar="files", nargs="+", help="Ficheiros para comprimir/descomprimir")
    args = parser.parse_args()
    zipper = PZip(args.files, args.mode, args.t, args.parallel)
