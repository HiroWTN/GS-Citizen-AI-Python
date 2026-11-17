"""Citizen Assist AI: assistente de terminal para orientar imigrantes no Brasil."""

import os
import sys

from base_conhecimento import BaseConhecimento
from assistente import Assistente

PASTA = os.path.dirname(os.path.abspath(__file__))


def main():
    try:  # garante acentos corretos em terminais que não usam UTF-8 por padrão
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass

    base = BaseConhecimento(os.path.join(PASTA, "data", "base_conhecimento.json"))
    base.carregar()  # lê o JSON e cria os objetos Orientacao

    assistente = Assistente("Citizen Assist AI", base,
                            os.path.join(PASTA, "data", "historico.json"),
                            os.path.join(PASTA, "data", "atendimentos.csv"))
    assistente.iniciar()


if __name__ == "__main__":
    main()
