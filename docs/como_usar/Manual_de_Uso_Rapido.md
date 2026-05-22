# Manual de Uso Rápido

Este manual foi escrito para uma pessoa comum conseguir usar o projeto sem precisar de conhecer o código por dentro.

## O que este projeto faz

Este projeto é uma plataforma de inteligência imobiliária para o mercado português. Ele recolhe anúncios, limpa os dados, avalia imóveis, calcula uma pontuação de oportunidade e mostra tudo num dashboard visual.

Em termos simples, o projeto ajuda a responder a perguntas como:
- este imóvel está caro ou barato?
- parece uma boa oportunidade?
- há imóveis parecidos no mercado?
- o sistema está a funcionar corretamente?

## Como começar

### 1. Preparar o ambiente

No Windows, o arranque normal faz-se com o ambiente virtual `venv312`.

### 2. Instalar dependências

Na pasta do projeto:
```bash
pip install -r realestate_engine/requirements.txt
```

### 3. Abrir a aplicação

Os ficheiros principais para arrancar o sistema estão em `scripts/`.

Os mais importantes são:
- `scripts/start_engine_24h.bat` — motor autónomo 24h
- `scripts/start_dashboard_backend.bat` — dashboard + API
- `scripts/start_all.bat` — arranque completo
- `macos/start_all.sh` — arranque simplificado para macOS

## Onde usar o projeto

### Dashboard
O dashboard é o sítio mais fácil para trabalhar com o sistema.

Abre em:
- `http://localhost:8501`

Lá podes:
- pesquisar imóveis
- ver oportunidades
- analisar pontuações
- consultar o estado do sistema
- usar ferramentas do investidor

### API
A API serve para integração e para o backend do sistema.

Abre em:
- `http://localhost:8000`

Documentação automática:
- `http://localhost:8000/docs`
- `http://localhost:8000/redoc`

## O fluxo normal de utilização

1. O sistema recolhe anúncios de portais imobiliários.
2. Os dados são tratados e normalizados.
3. O valor justo do imóvel é estimado.
4. O scoring indica se o imóvel parece interessante.
5. O dashboard mostra os resultados.
6. Os logs e métricas ajudam a confirmar que tudo está saudável.

## Como interpretar o resultado

Quando vês um imóvel no dashboard, normalmente deves olhar para:
- **Preço pedido** — quanto o vendedor quer
- **Valor estimado** — quanto o sistema acha que vale
- **Score** — quão boa parece a oportunidade
- **Alertas** — riscos ou pontos a investigar
- **Contexto de mercado** — comparação com a zona

## Como verificar se está tudo bem

Se quiseres confirmar que o sistema está saudável, corre a validação final:

```bash
python tests/test_final_validation.py
```

Esse teste confirma:
- botões do dashboard
- monitorização
- API
- base de dados
- documentação
- configuração

## Estrutura que interessa conhecer

- `realestate_engine/` — lógica principal
- `tests/` — testes automáticos
- `scripts/` — comandos e utilitários
- `docs/` — documentação
- `docs/reports/` — relatórios e validações
- `macos/` — arranque para macOS
- `logs/` — registos e arquivos de execução

## Dicas práticas

- Se estiveres a apresentar o projeto a alguém, começa pelo dashboard.
- Se algo falhar, vê primeiro os logs.
- Se alterares código, corre os testes antes de entregar.
- Evita deixar ficheiros temporários na raiz do projeto.

## Resumo em uma frase

Este projeto serve para recolher, analisar e apresentar oportunidades imobiliárias de forma organizada, automática e fácil de usar.
