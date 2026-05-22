# Como Usar o Projeto

Este guia explica o projeto de forma simples, como se eu estivesse a apresentá-lo a outra pessoa. A ideia é que alguém consiga perceber **o que ele faz**, **para que serve** e **como começar a usar** sem precisar de já conhecer a base de código.

## O que é este projeto

Este projeto é uma plataforma de inteligência imobiliária para o mercado português, com foco forte na zona do Porto. Em termos simples, ele faz três coisas principais:

1. **Recolhe anúncios imobiliários** de portais online.
2. **Analisa e avalia os imóveis** com modelos e regras internas.
3. **Mostra os resultados num dashboard** para facilitar a consulta e a tomada de decisão.

O objetivo não é apenas guardar imóveis. O objetivo é ajudar a encontrar oportunidades, perceber se um imóvel está caro ou barato e acompanhar o mercado com mais clareza.

## Para que serve na prática

Pensa nisto como uma central de análise imobiliária.

- Se quiseres ver **novos imóveis** recolhidos automaticamente, o projeto faz isso.
- Se quiseres saber **quanto vale um imóvel** aproximadamente, o projeto calcula isso.
- Se quiseres descobrir **se um imóvel parece bom negócio**, o sistema dá uma pontuação.
- Se quiseres acompanhar tudo de forma visual, tens o **dashboard**.
- Se quiseres ver se está tudo saudável, tens os **checks de monitorização**.

## As partes principais do projeto

### 1. Backend API
É a parte que expõe os dados e a lógica do sistema.

Serve para:
- verificar o estado da aplicação
- consultar listings
- calcular valuation
- calcular scoring
- alimentar o dashboard

### 2. Dashboard
É a interface visual, em Streamlit.

Serve para:
- pesquisar imóveis
- filtrar resultados
- abrir páginas de análise
- ver monitorização
- gerir listas e ferramentas do investidor

### 3. Scraping e ETL
Esta parte trata da recolha e limpeza de dados.

Serve para:
- ir aos portais buscar anúncios
- normalizar os dados
- remover duplicados
- preparar os imóveis para análise

### 4. Valuation
É o motor que tenta estimar o valor justo do imóvel.

Serve para:
- comparar preço pedido com valor estimado
- dar intervalos de confiança
- usar contexto de mercado

### 5. Scoring
É o motor que avalia se o imóvel parece interessante como oportunidade.

Serve para:
- calcular uma pontuação final
- explicar os fatores da pontuação
- mostrar alertas e pontos fracos

### 6. Monitoring
É a parte que confirma se o sistema está vivo e funcional.

Serve para:
- health checks
- métricas
- estado do backend
- verificação de componentes internos

## Estrutura mais importante das pastas

- `realestate_engine/` — código principal da aplicação
- `tests/` — testes automáticos
- `scripts/` — scripts operacionais e utilitários
- `docs/` — documentação principal
- `docs/reports/` — relatórios, validações e documentação de apoio
- `macos/` — arranque simplificado para macOS
- `logs/` — logs e ficheiros de execução
- `data/` — base de dados, cache, backups e exportações

## Como começar a usar

### Opção 1: usar o arranque rápido no Windows

Se estiveres no Windows, o mais simples é usar os ficheiros de arranque na pasta `scripts/`.

Normalmente vais ter:
- `scripts/start_engine_24h.bat` para o motor autónomo 24h
- `scripts/start_dashboard_backend.bat` para API + dashboard
- `scripts/start_all.bat` para arrancar tudo ao mesmo tempo

Passos:
1. abre um terminal na raiz do projeto
2. entra na pasta certa se necessário
3. executa o ficheiro `.bat`
4. espera que o motor e/ou a API + dashboard arranquem
5. abre o dashboard no browser

### Opção 2: usar o macOS

Na pasta `macos/` existe um arranque simples para quem estiver em macOS.

O ficheiro principal é:
- `macos/start_all.sh`

O que ele faz:
- inicia a API
- inicia o dashboard
- tenta abrir o Brave Browser no dashboard

Para usar:

```bash
chmod +x macos/start_all.sh
./macos/start_all.sh
```

### Opção 3: usar a aplicação manualmente

Se preferires arrancar tudo à mão, podes fazê-lo em dois passos:

1. arrancar a API
2. arrancar o dashboard

Isto é útil quando queres debugar, testar ou observar logs separados.

## Como entrar na aplicação

Depois de arrancada, os endereços mais importantes são:

- **Dashboard**: `http://localhost:8501`
- **API**: `http://localhost:8000`
- **Documentação da API**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## Como funciona o fluxo completo

O fluxo do sistema é mais ou menos assim:

1. o sistema recolhe imóveis dos portais
2. limpa e normaliza os dados
3. guarda os dados na base de dados
4. calcula valor justo
5. calcula scoring
6. apresenta os resultados no dashboard
7. regista logs e métricas para monitorização

## Como usar o dashboard

No dashboard vais encontrar várias áreas. As mais úteis são:

- **Overview** — visão geral do mercado e oportunidades
- **Pesquisa** — pesquisa e filtros
- **Análise de mercado** — visão de mercado e tendências
- **Ferramentas de investidor** — ferramentas de apoio à decisão
- **Sistema** — estado geral do sistema
- **Monitorização** — saúde e métricas
- **Telegram** — notificações

### Exemplo de uso rápido

Se quiseres avaliar um imóvel:

1. vai ao dashboard
2. procura o imóvel na pesquisa
3. abre a página de detalhe
4. vê o valor estimado
5. vê a pontuação
6. compara com imóveis semelhantes
7. decide se vale a pena avançar

## Como usar os testes

Os testes servem para confirmar que o projeto continua funcional depois de alterações.

Os principais estão em `tests/`.

O teste de validação final é:

```bash
python tests/test_final_validation.py
```

Esse teste confirma:
- botões do dashboard
- monitorização
- endpoints da API
- operações da base de dados
- documentação
- configuração

## Onde ver documentação importante

Se quiseres perceber melhor o projeto, olha para estes ficheiros:

- `docs/README.md` — índice geral da documentação
- `docs/ARCHITECTURE.md` — visão da arquitetura
- `docs/API.md` — documentação dos endpoints
- `docs/reports/SALE_DOCUMENTATION.md` — documentação comercial completa
- `docs/reports/PRODUCTION_READINESS.md` — checklist de produção
- `CONTRIBUTING.md` — guia de contribuição

## O que uma pessoa nova precisa mesmo de saber

Se eu tivesse de explicar isto a alguém em 30 segundos, diria:

> Este projeto é uma plataforma que recolhe anúncios imobiliários, trata os dados, avalia os imóveis e mostra tudo num dashboard fácil de usar. Serve para encontrar oportunidades, perceber o valor dos imóveis e acompanhar o mercado de forma organizada.

## Conselhos práticos

- Não mexas nos ficheiros temporários da raiz sem saber se ainda são usados.
- Usa os scripts de `scripts/` para arrancar e testar.
- Consulta `docs/reports/` para relatórios antigos ou históricos.
- Se algo falhar, começa por ver os logs em `logs/`.
- Se mudaste código, corre a validação final antes de considerar a alteração concluída.

## Resumo final

Este projeto junta recolha de dados, análise imobiliária, scoring, monitorização e dashboard num só lugar. O mais importante é que ele foi pensado para ser usado de forma prática: arrancas, consultas o dashboard, verificas oportunidades e acompanhas o estado do sistema.

Se quiseres, este ficheiro pode ser lido por outra pessoa como um ponto de entrada rápido para perceber o projeto sem precisar de abrir o código.
