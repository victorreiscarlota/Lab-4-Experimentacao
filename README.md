# 🧪 LABORATÓRIO 04 — Visualização de Dados Utilizando uma Ferramenta de BI

Os dados utilizados neste laboratório foram coletados durante o **Trabalho Interdisciplinar 6**, intitulado _“Análise Empírica da Migração para Funções Nativas JavaScript: Um Estudo sobre Maturidade de Software”_.

O conjunto de dados é composto por informações de **diversos repositórios JavaScript hospedados no GitHub**, cada um contendo métricas relacionadas à sua **popularidade**, **dependências** e **vulnerabilidades**.

## 📊 Estrutura do Dataset

Cada item do conjunto possui os seguintes campos:

- **repo** → Nome do repositório analisado
- **stars** → Número total de estrelas (indicador de popularidade e engajamento da comunidade)
- **forks** → Quantidade de cópias (“_forks_”) do repositório
- **dependencies** → Número de dependências diretas do projeto
- **dev_dependencies** → Número de dependências utilizadas apenas em ambiente de desenvolvimento
- **vulnerable_deps** → Quantidade de dependências que apresentam vulnerabilidades conhecidas
- **cves** → Lista de identificadores de vulnerabilidades (`CVE` ou `GHSA`) encontradas
- **path_usado** → Caminho no repositório onde a análise foi aplicada

Esses dados permitem investigar **relações entre popularidade, maturidade e segurança de software**.

Por exemplo, o **eixo X** de um gráfico pode representar o número de dependências (ou `dev_dependencies`), enquanto o **eixo Y** pode mostrar o número de vulnerabilidades (`vulnerable_deps`) ou o total de estrelas (`stars`).  
Assim, é possível visualizar se repositórios mais populares tendem a possuir **mais ou menos vulnerabilidades**, ou se a **quantidade de dependências influencia a exposição a riscos de segurança**.

---

### RQ1 — A substituição de bibliotecas externas reduz a superfície de ataque e a exposição a vulnerabilidades conhecidas no ecossistema do projeto?

Para responder a essa questão, analisam-se as métricas de **dependências** e **vulnerabilidades conhecidas** (`vulnerable_deps` e `vuln_ratio`).

Os gráficos demonstram que repositórios com **maior dependência de bibliotecas externas** tendem a apresentar **maior exposição a CVEs**, embora existam exceções em projetos mais maduros, que mantêm suas dependências **atualizadas e monitoradas**.

![Gráfico RQ1 — Relação entre dependências e vulnerabilidades](/results/chart_cve.png)

Essa análise sugere que a **redução de dependências externas**, substituindo-as por **funções nativas**, pode efetivamente **diminuir a superfície de ataque**, contribuindo para a **melhoria da segurança** do ecossistema.

---

### RQ2 — A migração para funções nativas impacta a complexidade e o tamanho do código-fonte mantido pela equipe?

Com base no gráfico que analisa a soma de **avg_complexity**, **lines_of_code**, **size_kb** e **dependencies**, observa-se que repositórios maiores e mais complexos — como `vercel/next.js` — apresentam naturalmente **maior complexidade** e **volume de código**.

Ao substituir bibliotecas externas por funções nativas, espera-se uma **redução gradual da complexidade média e do tamanho do código**, devido à **eliminação de dependências redundantes** e à **simplificação da base**.

![Gráfico RQ2 — Complexidade e tamanho do código por repositório](/results/chart.png)

Essas visualizações indicam que projetos com **menor número de dependências** tendem a apresentar **complexidade mais controlada**, reforçando a hipótese de que a **migração para funções nativas** pode tornar o código **mais estável, eficiente e de manutenção mais simples**.

## 🧠 Conclusão

As visualizações produzidas evidenciam que:

- Há uma **correlação direta entre o número de dependências e o risco de vulnerabilidades**;
- A **migração para funções nativas** pode contribuir tanto para a **redução da superfície de ataque** quanto para a **diminuição da complexidade** do código-fonte;
- Projetos maduros, com políticas de atualização contínua, conseguem manter um **equilíbrio entre dependências e segurança**, mesmo em ecossistemas complexos.
