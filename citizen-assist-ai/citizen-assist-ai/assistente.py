"""Classe Assistente: conversa com o cidadão, guarda o histórico e calcula indicadores."""

import csv
import json
import os
import time
from datetime import datetime

from base_conhecimento import LIMITE_ALTA, LIMITE_MEDIA

CAMPOS_CSV = ["sessao", "data", "origem", "pergunta", "orientacao_id",
              "encontrou", "ajudou", "tentativas", "tempo_s", "nota_facilidade"]


class Assistente:
    """Faz o atendimento (composição: tem uma BaseConhecimento)."""

    def __init__(self, nome, base, caminho_historico="data/historico.json",
                 caminho_csv="data/atendimentos.csv"):
        self.nome = nome
        self.base = base
        self.caminho_historico = caminho_historico
        self.caminho_csv = caminho_csv
        self.historico = []
        self.sessao = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.carregar_historico()

    # ---------- entrada de dados segura ----------
    @staticmethod
    def ler(prompt):
        """input() que nunca derruba o programa (Ctrl+C / fim da entrada = '0')."""
        try:
            return input(prompt).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return "0"

    def ler_opcao(self, prompt, maximo, minimo=0):
        """Repete até o usuário digitar um número inteiro entre minimo e maximo."""
        while True:
            texto = self.ler(prompt)
            if texto.isdecimal() and minimo <= int(texto) <= maximo:
                return int(texto)
            print(f"Opção inválida. Digite um número de {minimo} a {maximo}.")

    def ler_sn(self, prompt):
        """Repete até receber s ou n. '0' conta como 'n' (evita laço infinito)."""
        while True:
            texto = self.ler(prompt).lower()
            if texto in ("s", "sim"):
                return True
            if texto in ("n", "nao", "não", "0"):
                return False
            print("Resposta inválida. Digite s para sim ou n para não.")

    # ---------- regras de segurança ----------
    @staticmethod
    def contem_dado_pessoal(texto):
        """8 ou mais dígitos (CPF, telefone...) ou '@' (e-mail) = dado pessoal."""
        digitos = sum(1 for caractere in texto if caractere.isdigit())
        return digitos >= 8 or "@" in texto

    @staticmethod
    def nivel_confianca(pontos):
        if pontos >= LIMITE_ALTA:
            return "ALTA"
        if pontos >= LIMITE_MEDIA:
            return "MÉDIA"
        return None

    # ---------- atendimento ----------
    def iniciar(self):
        """Menu principal."""
        print(f"\n=== {self.nome}: orientação para imigrantes no Brasil ===")
        print("Respondo só com informações de fontes oficiais, sempre mostrando a fonte.")
        print("Não peço nem guardo nome, CPF, telefone ou e-mail. Não digite dados pessoais.")
        print("Aviso: este assistente NÃO é um canal oficial.")
        while True:
            print("\n--- Menu ---")
            print("1. Fazer uma pergunta")
            print("2. Navegar por categorias")
            print("3. Ver indicadores")
            print("4. Exportar atendimentos para CSV")
            print("0. Sair")
            opcao = self.ler_opcao("Escolha uma opção: ", 4)
            if opcao == 1:
                self.perguntar()
            elif opcao == 2:
                self.navegar()
            elif opcao == 3:
                self.exibir_indicadores()
            elif opcao == 4:
                self.exportar_csv()
            else:
                self.encerrar()
                return

    def perguntar(self):
        """Atendimentos por texto livre. Cada dúvida resolvida (ou abandonada com 0) é
        um atendimento; depois dela o assistente pede a próxima dúvida."""
        while True:
            if not self._atendimento_pergunta():
                return

    def _atendimento_pergunta(self):
        """Um atendimento. Devolve False quando o usuário digita 0 para voltar."""
        inicio = time.time()
        tentativas = 0
        encontrou = False
        ultima = None
        ultima_pergunta = ""
        while True:
            texto = self.ler("\nDigite sua dúvida (0 para voltar): ")
            if texto == "0":
                if tentativas > 0:  # desistiu sem resolver: o atendimento fica registrado
                    self.registrar("pergunta", ultima_pergunta,
                                   ultima.id if ultima else None, encontrou, False,
                                   tentativas, round(time.time() - inicio, 1))
                return False
            if texto == "":
                print("Atenção: a pergunta está vazia. Escreva sua dúvida ou digite 0 para voltar.")
                continue
            if self.contem_dado_pessoal(texto):
                # bloqueado: não conta como tentativa e NÃO é registrado
                print("Atenção: não digite CPF, telefone ou e-mail. Reescreva.")
                continue

            tentativas += 1
            ultima_pergunta = texto
            resultados = self.base.buscar(texto)
            if not resultados or resultados[0][0] < LIMITE_MEDIA:
                self.mostrar_nao_encontrei()
                continue

            encontrou = True
            ultima = resultados[0][1]
            self.mostrar_resultado(resultados)
            if self.ler_sn("\nEssa orientação respondeu sua dúvida? (s/n): "):
                self.registrar("pergunta", texto, ultima.id, True, True,
                               tentativas, round(time.time() - inicio, 1))
                return True
            print("Tudo bem. Tente reescrever com outras palavras ou digite 0 para voltar.")

    def mostrar_resultado(self, resultados):
        pontos, melhor = resultados[0]
        print(f"\nConfiança da resposta: {self.nivel_confianca(pontos)} ({pontos} pontos)")
        melhor.exibir()
        alternativas = [o for p, o in resultados[1:3] if p >= LIMITE_MEDIA]
        if alternativas:
            print("\nOutras orientações que podem ajudar:")
            for orientacao in alternativas:
                print(f"  - {orientacao.titulo} [{orientacao.categoria}]")

    def mostrar_nao_encontrei(self):
        print("\nNão encontrei uma orientação para essa dúvida.")
        print("Tente outras palavras (por exemplo: refúgio, CPF, escola, vacina) "
              "ou use a navegação por categorias (opção 2 do menu).")
        if self.base.categorias():
            print("Categorias: " + ", ".join(self.base.categorias()))

    def navegar(self):
        """Navegação por categorias, com '0 para voltar' em todas as telas."""
        while True:
            categorias = self.base.categorias()
            if not categorias:
                print("\nNão há categorias disponíveis (base de conhecimento vazia).")
                return
            print("\n=== Categorias ===")
            for numero, categoria in enumerate(categorias, 1):
                print(f"{numero}. {categoria}")
            print("0. Voltar")
            escolha = self.ler_opcao("Escolha uma categoria: ", len(categorias))
            if escolha == 0:
                return
            self._navegar_categoria(categorias[escolha - 1])

    def _navegar_categoria(self, categoria):
        while True:
            orientacoes = self.base.por_categoria(categoria)
            print(f"\n=== {categoria} ===")
            for numero, orientacao in enumerate(orientacoes, 1):
                print(f"{numero}. {orientacao.titulo}")
            print("0. Voltar")
            escolha = self.ler_opcao("Escolha uma orientação: ", len(orientacoes))
            if escolha == 0:
                return
            inicio = time.time()
            orientacao = orientacoes[escolha - 1]
            orientacao.exibir()
            ajudou = self.ler_sn("\nEssa orientação respondeu sua dúvida? (s/n): ")
            self.registrar("categoria", "", orientacao.id, True, ajudou, 1,
                           round(time.time() - inicio, 1))

    # ---------- histórico ----------
    def registrar(self, origem, pergunta, orientacao_id, encontrou, ajudou,
                  tentativas, tempo_s):
        """Guarda um atendimento (dicionário) e salva em data/historico.json."""
        atendimento = {
            "sessao": self.sessao,
            "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "origem": origem,
            "pergunta": pergunta,
            "orientacao_id": orientacao_id,
            "encontrou": encontrou,
            "ajudou": ajudou,
            "tentativas": tentativas,
            "tempo_s": tempo_s,
            "nota_facilidade": None,
        }
        self.historico.append(atendimento)
        self.salvar_historico()

    def carregar_historico(self):
        """Lê o histórico; arquivo ausente ou corrompido nunca trava o programa."""
        self.historico = []
        if not os.path.exists(self.caminho_historico):
            return
        try:
            with open(self.caminho_historico, "r", encoding="utf-8") as arquivo:
                dados = json.load(arquivo)
            if not isinstance(dados, list):
                raise ValueError("formato inesperado")
            self.historico = [item for item in dados if isinstance(item, dict)]
        except (OSError, ValueError, UnicodeDecodeError):  # JSONDecodeError é ValueError
            print("Atenção: o histórico estava corrompido; começando um histórico novo.")
            try:
                os.replace(self.caminho_historico, self.caminho_historico + ".corrompido")
            except OSError:
                pass
            self.historico = []

    def salvar_historico(self):
        try:
            os.makedirs(os.path.dirname(self.caminho_historico) or ".", exist_ok=True)
            with open(self.caminho_historico, "w", encoding="utf-8") as arquivo:
                json.dump(self.historico, arquivo, ensure_ascii=False, indent=2)
        except OSError:
            print("Atenção: não foi possível salvar o histórico.")

    # ---------- indicadores ----------
    @staticmethod
    def _media(valores):
        numeros = [v for v in valores if isinstance(v, (int, float)) and not isinstance(v, bool)]
        return round(sum(numeros) / len(numeros), 1) if numeros else None

    def indicadores(self):
        """Calcula os indicadores a partir do histórico (devolve None se vazio)."""
        total = len(self.historico)
        if total == 0:
            return None
        encontrados = [a for a in self.historico if a.get("encontrou")]
        ajudaram = [a for a in self.historico if a.get("ajudou")]

        notas_por_sessao = {}  # uma nota por sessão, para não pesar mais quem fez mais perguntas
        for atendimento in self.historico:
            if atendimento.get("nota_facilidade") is not None:
                notas_por_sessao[atendimento.get("sessao")] = atendimento["nota_facilidade"]

        sem_solucao = []
        for atendimento in self.historico:
            pergunta = atendimento.get("pergunta")
            if (not atendimento.get("ajudou") and atendimento.get("origem") == "pergunta"
                    and pergunta and pergunta not in sem_solucao):
                sem_solucao.append(pergunta)

        return {
            "total": total,
            "encontrada_pct": round(100 * len(encontrados) / total, 1),
            "acerto_pct": round(100 * len(ajudaram) / total, 1),
            "tempo_medio": self._media([a.get("tempo_s") for a in encontrados]),
            "tentativas_media": self._media([a.get("tentativas") for a in self.historico]),
            "facilidade": self._media(list(notas_por_sessao.values())),
            "sessoes_avaliadas": len(notas_por_sessao),
            "sem_solucao": sem_solucao,
        }

    def exibir_indicadores(self):
        ind = self.indicadores()
        if ind is None:
            print("\nAinda não há atendimentos registrados.")
            return
        print("\n=== Indicadores ===")
        print(f"Atendimentos registrados:    {ind['total']}")
        print(f"Resposta encontrada:         {ind['encontrada_pct']}%")
        print(f"Taxa de acerto (ajudou):     {ind['acerto_pct']}%")
        tempo = ind["tempo_medio"]
        print(f"Tempo médio para encontrar:  {tempo if tempo is not None else '-'} s")
        print(f"Tentativas por atendimento:  {ind['tentativas_media']}")
        if ind["facilidade"] is None:
            print("Facilidade de uso (1 a 5):   ainda sem notas")
        else:
            print(f"Facilidade de uso (1 a 5):   {ind['facilidade']} "
                  f"({ind['sessoes_avaliadas']} sessão(ões) avaliada(s))")
        if ind["sem_solucao"]:
            print("Dúvidas sem solução:")
            for pergunta in ind["sem_solucao"]:
                print(f"  - {pergunta}")
        else:
            print("Dúvidas sem solução:         nenhuma")

    # ---------- CSV ----------
    def exportar_csv(self):
        """Exporta o histórico para data/atendimentos.csv com csv.DictWriter."""
        if not self.historico:
            print("\nNão há atendimentos para exportar.")
            return
        try:
            os.makedirs(os.path.dirname(self.caminho_csv) or ".", exist_ok=True)
            # utf-8-sig: o Excel abre os acentos corretamente
            with open(self.caminho_csv, "w", newline="", encoding="utf-8-sig") as arquivo:
                escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_CSV, extrasaction="ignore")
                escritor.writeheader()
                escritor.writerows(self.historico)
            print(f"\n{len(self.historico)} atendimento(s) exportado(s) para {self.caminho_csv}")
        except OSError:
            print("Atenção: não foi possível exportar o CSV.")

    # ---------- saída ----------
    def encerrar(self):
        """Pede a nota de facilidade (se houve atendimento nesta sessão) e exporta o CSV."""
        da_sessao = [a for a in self.historico if a.get("sessao") == self.sessao]
        if da_sessao:
            print("\nAntes de sair: de 1 a 5, qual a facilidade de usar o assistente?")
            nota = self.ler_opcao("(1 = difícil, 5 = muito fácil, 0 para pular): ", 5)
            if nota > 0:
                for atendimento in da_sessao:
                    atendimento["nota_facilidade"] = nota
                self.salvar_historico()
            self.exportar_csv()
        print("\nObrigado por usar o Citizen Assist AI. Lembre-se: confirme sempre nos canais oficiais.")
