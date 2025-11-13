# LABORATÓRIO 04 — Visualização de Dados Utilizando uma Ferramenta de BI

Os dados utilizados neste laboratório foram coletados durante o **Trabalho Interdisciplinar 6**, intitulado _“Análise Empírica da Migração para Funções Nativas JavaScript: Um Estudo sobre Maturidade de Software”_.

O conjunto de dados é composto por informações de **diversos repositórios JavaScript hospedados no GitHub**, cada um contendo métricas relacionadas à sua **popularidade**, **dependências** e **vulnerabilidades**.

## Seção 1: Introdução

Hoje em dia, quando vamos criar um projeto javascript, é comum utilizarmos diversas bibliotecas externas, sendo muitas dessas bibliotecas que não conheçemos, e muitas vezes nem sabemos se são seguras. Essas bibliotecas podem introduzir vulnerabilidades no código, seja por falhas de segurança conhecidas ou por práticas de codificação inadequadas.

Recentemente, houve problemas graves de segunraça envolvendo bibliotecas populares do ecossistema JavaScript, como o caso de um acontecimento desse mesmo ano [disponivel nesse link](https://forklog.com/en/hackers-target-javascript-ecosystem-to-hijack-crypto-wallets), onde hackers conseguiram explorar vulnerabilidades em bibliotecas amplamente utilizadas para comprometer carteiras de criptomoedas.

A ideia do trabalho é investigar como a adoção de **funções nativas do JavaScript** (em vez de bibliotecas externas) pode impactar a **segurança** e a **complexidade** do código-fonte dos projetos.

## Seção 2: Caracterização do Dataset

```json
  {
    "repo": "vercel/next.js",
    "stars": 135363,
    "forks": 29706,
    "dependencies": 5,
    "dev_dependencies": 221,
    "vulnerable_deps": 3,
    "cves": [
      "GHSA-566m-qj78-rww5",
      "GHSA-7fh5-64p2-3v2j",
      "GHSA-hwj9-h5mp-3pm3"
    ],
    "path_usado": "packages/next",
    "size_kb": 2404838,
    "lines_of_code": 844493,
    "avg_complexity": 2.9,
  },
```

Nosso dataset consiste em um arquivo JSON gerado pelo script app/scripts/analyze.py, nele é contido um array onde cada objeto representa um repositório analisado. Neste objeto é possível encontrar os seguintes campos:

- **repo** → Nome do repositório analisado
- **stars** → Número total de estrelas (indicador de popularidade e engajamento da comunidade)
- **forks** → Quantidade de cópias (“_forks_”) do repositório
- **dependencies** → Número de dependências diretas do projeto
- **dev_dependencies** → Número de dependências utilizadas apenas em ambiente de desenvolvimento
- **vulnerable_deps** → Quantidade de dependências que apresentam vulnerabilidades conhecidas
- **size_kb** → Tamanho total do código-fonte em kilobytes
- **lines_of_code** → Número total de linhas de código no repositório

---

### `cves`

O campo **`cves`** representa a lista de vulnerabilidades identificadas
nas dependências do repositório analisado. Cada item presente nessa
lista está associado a um identificador público padronizado --- seja no
formato **CVE** (Common Vulnerabilities and Exposures) ou **GHSA**
(GitHub Security Advisory). Esses identificadores são fundamentais no
ecossistema de segurança da informação, pois permitem registrar,
rastrear e consultar vulnerabilidades conhecidas de maneira estruturada
e confiável.

A presença de entradas em `cves` indica que uma ou mais dependências do
projeto possuem **vulnerabilidades catalogadas**, o que pode ter
impactos diretos na segurança da aplicação, na integridade dos dados e
na confiabilidade do sistema. Ao incluir essa lista no dataset, nossa
análise ganha uma perspectiva crítica sobre o **risco de segurança**
associado ao conjunto de bibliotecas utilizadas --- tanto de produção
quanto de desenvolvimento.

#### O que representam CVE e GHSA?

Os identificadores **CVE** fazem parte de um banco de dados global
gerido pela MITRE Corporation e amplamente utilizado por empresas,
governos e comunidades de desenvolvimento para padronizar
vulnerabilidades.\
Cada CVE segue o formato:

    CVE-AAAA-NNNNN

onde `AAAA` representa o ano de descoberta e `NNNNN` é um número
sequencial único.

Já os identificadores **GHSA** (GitHub Security Advisory) fazem parte do
banco de vulnerabilidades mantido pelo GitHub e geralmente seguem o
formato:

    GHSA-xxxx-yyyy-zzzz

Assim como os CVEs, eles indicam falhas de segurança em bibliotecas,
frameworks e ferramentas amplamente utilizadas no ecossistema
JavaScript/Node.js --- foco da nossa análise.

#### Como essas vulnerabilidades chegam ao dataset?

Durante a coleta de dados, executamos ferramentas de análise de
dependências (como `npm audit` ou APIs de inspeção de vulnerabilidades)
que verificam:

- dependências diretas (`dependencies`)
- dependências de desenvolvimento (`dev_dependencies`)
- dependências transitivas

Ao identificar que uma biblioteca instalada contém vulnerabilidade
catalogada, essas ferramentas retornam os **advisories
correspondentes**, normalmente no formato GHSA, que são inseridos
diretamente na lista `cves`.

Exemplo real:

```json
"cves": [
  "GHSA-566m-qj78-rww5",
  "GHSA-7fh5-64p2-3v2j",
  "GHSA-hwj9-h5mp-3pm3"
]
```

#### Interpretação e importância

A lista de `cves` funciona como um indicador direto da **superfície de
ataque** do projeto e permite avaliações importantes:

- Arrays vazios sugerem ausência de vulnerabilidades detectadas.
- Arrays com múltiplos itens indicam riscos associados, como execução
  remota de código, negação de serviço, vazamento de dados, entre
  outros.

Além disso, `cves` complementa o campo `vulnerable_deps`, oferecendo não
apenas a quantidade, mas **quais vulnerabilidades específicas** estão
presentes.

#### Relevância para o estudo

Esse campo é essencial para entendermos:

1.  A relação entre maturidade/popularidade de um projeto e sua
    exposição a vulnerabilidades.
2.  O impacto de decisões arquiteturais --- como a adoção de funções
    nativas --- na segurança.
3.  A evolução histórica do risco de segurança antes e depois de
    mudanças estruturais no código.

A análise do campo `cves` evidencia um ponto crítico da engenharia de
software moderna:

> Quanto maior o número de dependências, maior a probabilidade de herdar
> vulnerabilidades.

Assim, essa métrica não apenas revela aspectos técnicos, mas também
destaca a importância de uma gestão cuidadosa de dependências em
projetos complexos.

---

### `avg_complexity`

A métrica **`avg_complexity`** representa a complexidade média do
código-fonte de um repositório. Ela funciona como um indicador essencial
da **manutenibilidade**, **legibilidade** e **qualidade estrutural** do
software, demonstrando o quanto o código pode ser difícil de
compreender, testar e evoluir. Projetos com alta complexidade tendem a
exigir maior esforço de manutenção e apresentam maior risco de
introdução de bugs durante modificações.

O cálculo dessa métrica está fundamentado no conceito de **complexidade
ciclomática**, que mensura a quantidade de caminhos lineares
independentes existentes em uma função ou método. Estruturas de controle
como `if`, `for`, `while`, `try`, `catch`, entre outras, aumentam essa
medida --- e, consequentemente, elevam o custo cognitivo para
desenvolvedores.

Durante o processo de análise, utilizamos duas bibliotecas Python
amplamente reconhecidas: **Radon** e **Lizard**. Ambas realizam análise
estática de código e geram métricas de complexidade por função. No caso
específico da biblioteca Lizard, utilizamos o método:

    lizard.analyze_file(str(file_path))

Esse método analisa cada arquivo individualmente e retorna um objeto
contendo diversas informações sobre o código, incluindo a complexidade
ciclomática de cada função encontrada. A partir desses dados, acumulamos
todas as complexidades registradas em uma lista e aplicamos a fórmula:

```python
avg_complexity = sum(complexities) / len(complexities)
```

Em outras palavras, somamos a complexidade de todas as funções
analisadas (`complexities`) e dividimos pela quantidade total de funções
(`len(complexities)`). Quando nenhum arquivo válido é encontrado --- ou
quando o repositório não contém funções analisáveis --- o valor padrão
retornado é **0.0**, garantindo consistência nos resultados.

Essa métrica é especialmente valiosa para nosso estudo, pois nos permite
comparar repositórios entre si e avaliar a evolução interna de cada um.
Em particular, ela desempenha um papel importante na análise do impacto
da **migração para funções nativas**, permitindo observar se essa
prática reduz, mantém ou aumenta a complexidade estrutural do código.
Dessa forma, `avg_complexity` se torna um indicador objetivo na
avaliação da eficácia dessas práticas de modernização e simplificação do
código.

---

Esses dados permitem investigar **relações entre popularidade, maturidade e segurança de software**.

Por exemplo, o **eixo X** de um gráfico pode representar o número de dependências (ou `dev_dependencies`), enquanto o **eixo Y** pode mostrar o número de vulnerabilidades (`vulnerable_deps`) ou o total de estrelas (`stars`).  
Assim, é possível visualizar se repositórios mais populares tendem a possuir **mais ou menos vulnerabilidades**, ou se a **quantidade de dependências influencia a exposição a riscos de segurança**.

---

### `path_usado`

O campo **`path_usado`** identifica o caminho exato dentro do
repositório onde a análise foi realizada. Ele desempenha um papel
crucial no contexto do nosso estudo, principalmente porque muitos
projetos --- especialmente os maiores e mais maduros, como _monorepos_
--- não concentram todo seu código-fonte em um único diretório. Em vez
disso, eles são organizados em múltiplos pacotes, módulos e subsistemas
internos.

Ao registrar o valor de `path_usado`, conseguimos documentar
precisamente **qual parte do repositório foi analisada**, garantindo
reprodutibilidade, rastreabilidade e clareza durante a interpretação dos
resultados. Isso é particularmente relevante em repositórios que possuem
múltiplos componentes independentes, como bibliotecas, CLIs, aplicações
internas, exemplos e ambientes de teste.

Por exemplo, no caso do repositório:

    "path_usado": "packages/next"

isso indica que nossa análise não foi aplicada ao repositório inteiro,
mas especificamente ao diretório **`packages/next`** --- onde se
localiza o pacote principal do framework Next.js dentro da estrutura
maior do monorepo da Vercel. Assim, métricas como complexidade média,
número de dependências e vulnerabilidades são extraídas exclusivamente
dessa parte do código, evitando interferência de componentes auxiliares
que não representam o núcleo funcional do projeto.

Registrar esse caminho também permite distinguir entre diferentes áreas
de um mesmo repositório que podem ter objetivos, padrões de codificação
ou níveis de maturidade muito diferentes. Por exemplo:

- `packages/core` pode conter o núcleo do sistema;
- `packages/runtime` pode incluir implementações específicas da VM ou
  ambiente de execução;
- `examples/*` muitas vezes contém apenas demonstrações e não deve ser
  incluído na análise;
- `tests/` em geral não representa o comportamento real do código em
  produção.

Assim, `path_usado` funciona como um marcador que contextualiza todas as
demais métricas coletadas. Sem ele, seria difícil garantir que análises
comparativas entre repositórios fossem justas ou que as métricas
realmente correspondessem às partes mais relevantes do código.

Em síntese, esse campo garante **precisão**, **consistência** e
**transparência** no processo de coleta, permitindo que a análise seja
fiel ao módulo ou pacote que realmente compõe o objeto de estudo.

## Seção 3: Questões de Pesquisa

### RQ1 — A substituição de bibliotecas externas reduz a superfície de ataque e a exposição a vulnerabilidades conhecidas no ecossistema do projeto?

Para responder a essa questão, analisam-se as métricas de **dependências** e **vulnerabilidades conhecidas** (`deps` e `cves.length`).

Os gráficos demonstram que repositórios com **maior dependência de bibliotecas externas** tendem a apresentar **maior exposição a CVEs**, embora existam exceções em projetos mais maduros, que mantêm suas dependências **atualizadas e monitoradas**.

![Gráfico RQ1 — Relação entre dependências e vulnerabilidades](/imgs/chart_cve.png)

Essa análise sugere que a **redução de dependências externas**, substituindo-as por **funções nativas**, pode efetivamente **diminuir a superfície de ataque**, contribuindo para a **melhoria da segurança** do ecossistema.

---

### RQ2 — A migração para funções nativas impacta a complexidade e o tamanho do código-fonte mantido pela equipe?

Com base no gráfico que analisa a soma de **avg_complexity**, **lines_of_code**, **size_kb** e **dependencies**, observa-se que repositórios maiores e mais complexos — como `vercel/next.js` — apresentam naturalmente **maior complexidade** e **volume de código**.

Ao substituir bibliotecas externas por funções nativas, espera-se uma **redução gradual da complexidade média e do tamanho do código**, devido à **eliminação de dependências redundantes** e à **simplificação da base**.

![Gráfico RQ2 — Complexidade e tamanho do código por repositório](/imgs/chart_complexity.png)

Essas visualizações indicam que projetos com **menor número de dependências** tendem a apresentar **complexidade mais controlada**, reforçando a hipótese de que a **migração para funções nativas** pode tornar o código **mais estável, eficiente e de manutenção mais simples**.

## Seção 4: Resultados

As visualizações produzidas evidenciam que:

- Há uma **correlação direta entre o número de dependências e o risco de vulnerabilidades**;
- A **migração para funções nativas** pode contribuir tanto para a **redução da superfície de ataque** quanto para a **diminuição da complexidade** do código-fonte;
- Projetos maduros, com políticas de atualização contínua, conseguem manter um **equilíbrio entre dependências e segurança**, mesmo em ecossistemas complexos.
