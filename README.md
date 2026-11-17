# Citizen Assist AI — Orientação para imigrantes no Brasil

Assistente de terminal em Python que responde dúvidas de imigrantes com base em informações de **fontes oficiais**, mostrando sempre a fonte, a data de verificação e o aviso de que ele **não é um canal oficial**. O assistente **não pede nem guarda dados pessoais**.

> Projeto da Global Solution 2026.2 — Pensamento Computacional e Automação com Python (FIAP, 1CCPI)

## Integrantes

| Nome | RM |
|------|----|
| Nathan Hiroshi Watanabe | 572806 |
| Mateus de Oliveira Fernandes Neves | 572431 |

## Público e problema escolhidos

**Público:** imigrantes e refugiados que vivem (ou estão chegando) no Brasil.

**Problema:** a informação sobre documentos (refúgio, residência, CRNM, CPF), saúde, escola e trabalho existe, mas está espalhada em vários sites, em linguagem técnica e misturada com páginas que parecem oficiais e não são. O assistente reúne as orientações principais em um só lugar, em linguagem simples, sempre apontando a fonte oficial.

## ODS relacionados

- **ODS 10** — Redução das desigualdades (acesso à informação para imigrantes)
- **ODS 16** — Paz, justiça e instituições eficazes (acesso à informação e a instituições públicas)
- **ODS 3** — Saúde e bem-estar (orientações sobre SUS e vacinação)
- **ODS 4** — Educação de qualidade (orientações sobre matrícula e diploma)

## Como executar

Requisitos: Python 3.8 ou superior. **Nenhuma biblioteca externa.**

```bash
python main.py
```

Menu principal: (1) fazer uma pergunta em texto livre, (2) navegar por categorias, (3) ver indicadores, (4) exportar CSV, (0) sair. Em todas as telas, `0` volta.

## Estrutura

```
citizen-assist-ai/
├── README.md
├── main.py                  # inicia o programa
├── orientacao.py            # classe Orientacao
├── base_conhecimento.py     # classe BaseConhecimento + normalizar()
├── assistente.py            # classe Assistente
└── data/
    ├── base_conhecimento.json   # 13 orientações, 4 categorias
    ├── historico.json           # atendimentos (gerado pelo programa)
    └── atendimentos.csv         # exportação (gerada pelo programa)
```

### Classes (composição)

```
Assistente
 └── base: BaseConhecimento
      └── orientacoes: [Orientacao, Orientacao, ...]
```

- **Orientacao**: guarda um registro do JSON e o exibe (`exibir()`).
- **BaseConhecimento**: lê o JSON (`carregar()`), lista categorias (`categorias()`, `por_categoria()`) e busca a melhor orientação (`pontuar()`, `buscar()`).
- **Assistente**: faz o atendimento (`perguntar()`, `navegar()`), guarda o histórico (`registrar()`), calcula `indicadores()` e `exportar_csv()`.

## Regra de pontuação

A pergunta e as palavras-chave/título são normalizadas (minúsculas, sem acentos, sem pontuação). Cada orientação recebe pontos:

| Regra | Pontos |
|-------|--------|
| Palavra-chave da orientação que aparece na pergunta | +3 |
| Palavra da pergunta (4 letras ou mais) que aparece no título | +1 |

| Melhor orientação | Resultado |
|-------------------|-----------|
| 6 pontos ou mais | Confiança **ALTA** |
| 3 a 5 pontos | Confiança **MÉDIA** |
| Menos de 3 pontos | "Não encontrei": sugere outras palavras e as categorias |

`buscar()` devolve uma lista de tuplas `(pontos, orientacao)` da maior para a menor pontuação. O assistente mostra a melhor orientação e até duas alternativas (só as que também têm 3 pontos ou mais).

**Ajustes feitos em relação ao enunciado (explicados aqui e no vídeo):**
- Uma lista curta de *stopwords* (como, para, onde, fazer, tirar...) não vale ponto no título, para que palavras muito comuns não decidam o resultado.
- A palavra do título conta uma vez só, mesmo que apareça repetida na pergunta.
- A comparação é por palavra inteira (`" cpf "`), não por pedaço de palavra.
- Empates são resolvidos pelo menor `id`.

## Regras de atendimento

- **Dados pessoais:** pergunta com 8 ou mais dígitos ou com `@` é recusada e **não é registrada**.
- **Entradas inválidas:** letras, números fora da faixa, entrada vazia e s/n inválido nunca encerram o programa.
- **Transparência:** toda resposta mostra fonte, data de verificação e o aviso "este assistente NÃO é um canal oficial".
- **Arquivos:** JSON da base ausente ou corrompido gera aviso e o programa continua; histórico corrompido é movido para `historico.json.corrompido` e um novo é criado.

## Indicadores

Calculados a partir de `data/historico.json`: resposta encontrada (%), taxa de acerto — ajudou (%), tempo médio para encontrar, tentativas por atendimento, facilidade de uso (nota de 1 a 5 pedida ao sair, uma por sessão) e lista de dúvidas sem solução.

## Fontes consultadas

Todas estão no campo `fonte` de cada orientação em `data/base_conhecimento.json`:

- Portal gov.br — serviços de refúgio, autorização de residência, registro e CRNM, segunda via da CRNM e inscrição no CPF
- Lei de Migração (Lei nº 13.445/2017), Planalto
- Ministério da Saúde, Ministério do Trabalho e Emprego, MEC, Ministério do Desenvolvimento e Assistência Social
- Defensoria Pública da União

## Integrações com outras disciplinas

Nenhuma. O projeto usa apenas Python padrão e a busca por pontuação.



## Limitações

- O assistente só responde com o que está na base (13 orientações); dúvidas fora dela retornam "não encontrei".
- A busca é por palavras-chave exatas: não entende sinônimos, erros de digitação nem variações como o plural, a menos que estejam nas palavras-chave.
- As regras migratórias mudam; cada resposta mostra a data de verificação e deve ser conferida no site oficial.
- O assistente está em português e não substitui o atendimento oficial nem uma orientação jurídica.



> **PREENCHER:** link do YouTube (não listado)
