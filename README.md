## LABORATÓRIO 04 - Visualização de dados utilizando uma ferramenta de bi.pdf

Os dados utilizados neste laboratório foram coletados durante o nosso Trabalho Interdisciplinar 6, intitulado _“Análise Empírica da Migração para Funções Nativas JavaScript: Um Estudo sobre Maturidade de Software”_.

O conjunto de dados é composto por informações de diversos repositórios javascript hospedados no github, cada um contendo métricas relacionadas à sua popularidade, dependências e vulnerabilidades.

### Cada item do conjunto possui os seguintes campos:

- repo: nome do repositório analisado;

- stars: número total de estrelas (indicador de popularidade e engajamento da comunidade);

- forks: quantidade de cópias (“`forks`”) do repositório;

- dependencies: número de dependências diretas do projeto;

- dev_dependencies: número de dependências utilizadas apenas em desenvolvimento;

- vulnerable_deps: quantidade de dependências que apresentam vulnerabilidades conhecidas;

- cves: lista de identificadores de vulnerabilidades (`CVE` ou `GHSA`) encontradas;

- path_usado: caminho no repositório onde a análise foi aplicada.

---

Esses dados permitem investigar relações entre popularidade, maturidade e segurança de software. O eixo X de um gráfico pode representar o número de dependências (ou `dev_dependencies`),enquanto o eixo Y pode mostrar o número de vulnerabilidades (`vulnerable_deps`) ou o total de estrelas (`stars`), por exemplo.

Assim, é possível visualizar se repositórios mais populares tendem a possuir mais ou menos vulnerabilidades, ou se a quantidade de dependências influencia a exposição a riscos de segurança.
