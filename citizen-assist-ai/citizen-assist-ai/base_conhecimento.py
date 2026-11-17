"""Classe BaseConhecimento: lê o JSON, lista categorias e busca a melhor orientação."""

import json

from orientacao import Orientacao

# ---------- Regras da busca (explicadas no README) ----------
PESO_PALAVRA_CHAVE = 3   # palavra-chave da orientação que aparece na pergunta
PESO_TITULO = 1          # palavra da pergunta (4+ letras) que aparece no título
LIMITE_ALTA = 6          # melhor orientação com 6 pontos ou mais -> ALTA
LIMITE_MEDIA = 3         # de 3 a 5 pontos -> MÉDIA; abaixo de 3 -> "não encontrei"

# Palavras muito comuns que não ajudam a achar o assunto (não valem ponto no título).
STOPWORDS = {"como", "para", "onde", "qual", "quais", "preciso", "posso", "pode",
             "quero", "tenho", "minha", "meus", "minhas", "sobre", "quando",
             "quem", "esse", "essa", "isso", "esta", "este", "voce", "fazer",
             "faco", "gostaria", "saber", "tirar"}

ACENTOS = {"á": "a", "à": "a", "ã": "a", "â": "a", "ä": "a",
           "é": "e", "è": "e", "ê": "e", "ë": "e",
           "í": "i", "ì": "i", "î": "i", "ï": "i",
           "ó": "o", "ò": "o", "õ": "o", "ô": "o", "ö": "o",
           "ú": "u", "ù": "u", "û": "u", "ü": "u",
           "ç": "c", "ñ": "n"}

SINAIS = "?!.,;:()[]\"'/-¿¡"

CAMPOS_OBRIGATORIOS = ["id", "categoria", "titulo", "palavras_chave", "resposta",
                       "documentos", "onde", "fonte", "verificado_em"]


def normalizar(texto):
    """Minúsculas, sem acentos e sem pontuação. Devolve o texto entre espaços
    (" cartao do sus "), o que permite achar palavras inteiras com `in`."""
    texto = str(texto).lower().strip()
    for letra, troca in ACENTOS.items():
        texto = texto.replace(letra, troca)
    for sinal in SINAIS:
        texto = texto.replace(sinal, " ")
    return " " + " ".join(texto.split()) + " "


class BaseConhecimento:
    """Conjunto de todas as orientações (composição: tem uma lista de Orientacao)."""

    def __init__(self, caminho):
        self.caminho = caminho
        self.orientacoes = []

    def carregar(self):
        """Lê o JSON e cria os objetos Orientacao. Nunca trava o programa:
        arquivo ausente ou corrompido gera um aviso e devolve False."""
        self.orientacoes = []
        try:
            with open(self.caminho, "r", encoding="utf-8") as arquivo:
                dados = json.load(arquivo)
        except FileNotFoundError:
            print(f"Atenção: arquivo da base de conhecimento não encontrado ({self.caminho}).")
            return False
        except (json.JSONDecodeError, UnicodeDecodeError):
            print("Atenção: o arquivo da base de conhecimento está corrompido (JSON inválido).")
            return False
        except OSError:
            print("Atenção: não foi possível ler o arquivo da base de conhecimento.")
            return False

        if not isinstance(dados, list):
            print("Atenção: a base de conhecimento deve ser uma lista de orientações.")
            return False

        ignorados = 0
        for registro in dados:
            orientacao = self._criar_orientacao(registro)
            if orientacao is None:
                ignorados += 1
            else:
                self.orientacoes.append(orientacao)

        if ignorados:
            print(f"Atenção: {ignorados} registro(s) inválido(s) foram ignorados.")
        if not self.orientacoes:
            print("Atenção: nenhuma orientação foi carregada.")
            return False
        return True

    @staticmethod
    def _criar_orientacao(registro):
        """Transforma um dicionário do JSON em Orientacao (ou None se inválido)."""
        if not isinstance(registro, dict):
            return None
        for campo in CAMPOS_OBRIGATORIOS:
            if campo not in registro:
                return None
        if not isinstance(registro["palavras_chave"], list):
            return None
        if not isinstance(registro["documentos"], list):
            return None
        dados = {campo: registro[campo] for campo in CAMPOS_OBRIGATORIOS}
        dados["palavras_chave"] = [str(p) for p in dados["palavras_chave"]]
        dados["documentos"] = [str(d) for d in dados["documentos"]]
        return Orientacao(**dados)

    def categorias(self):
        """Lista de categorias sem repetição, na ordem em que aparecem no JSON."""
        lista = []
        for orientacao in self.orientacoes:
            if orientacao.categoria not in lista:
                lista.append(orientacao.categoria)
        return lista

    def por_categoria(self, categoria):
        """Orientações de uma categoria."""
        return [o for o in self.orientacoes if o.categoria == categoria]

    def pontuar(self, pergunta, orientacao):
        """Pontos de UMA orientação para uma pergunta já normalizada."""
        pontos = 0
        for palavra in orientacao.palavras_chave:
            chave = normalizar(palavra)
            if chave.strip() and chave in pergunta:
                pontos += PESO_PALAVRA_CHAVE
        titulo = normalizar(orientacao.titulo)
        for palavra in set(pergunta.split()):
            if len(palavra) >= 4 and palavra not in STOPWORDS and f" {palavra} " in titulo:
                pontos += PESO_TITULO
        return pontos

    def buscar(self, pergunta):
        """Lista de tuplas (pontos, orientacao), da maior para a menor pontuação."""
        pergunta = normalizar(pergunta)
        resultados = []
        for orientacao in self.orientacoes:
            pontos = self.pontuar(pergunta, orientacao)
            if pontos > 0:
                resultados.append((pontos, orientacao))
        resultados.sort(key=lambda tupla: (-tupla[0], tupla[1].id))
        return resultados
