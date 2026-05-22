# Scripts do Real Estate Engine

Este diretório contém scripts de automação, manutenção e desenvolvimento para o projeto.

## 📁 Estrutura

```
scripts/
├── production/           # Scripts de produção
│   ├── maintenance/      # Scripts de manutenção do sistema
│   │   └── clean_db.py  # Limpeza de banco de dados
│   └── verify/          # Scripts de verificação
│       ├── debug_remax.py     # Debug REMAX consolidado
│       └── verify_all.py      # Verificação unificada do sistema
├── debug/               # Scripts de debug (não versionados no Git)
├── archive/             # Scripts arquivados
│   └── temp_debug/      # Scripts temporários arquivados
└── archive/             # Relatórios e scripts antigos
```

## 🚀 Scripts de Produção

### Manutenção

#### clean_db.py
Script unificado para limpeza de banco de dados.

**Uso:**
```bash
python scripts/production/maintenance/clean_db.py raw-empty-area      # Limpar raw listings com area vazio
python scripts/production/maintenance/clean_db.py clean-empty-source  # Limpar clean listings com source_id vazio
python scripts/production/maintenance/clean_db.py raw-empty-source   # Limpar raw listings com source_id vazio
python scripts/production/maintenance/clean_db.py full                # Limpeza completa com recuperação e deduplicação
```

**Modos:**
- `raw-empty-area` - Remove raw listings com area_text vazio
- `clean-empty-source` - Remove clean listings com source_id vazio
- `raw-empty-source` - Remove raw listings com source_id vazio
- `full` - Limpeza completa com recuperação de source_ids e remoção de duplicados

### Verificação

#### verify_all.py
Script unificado para verificação do sistema.

**Uso:**
```bash
python scripts/production/verify/verify_all.py db      # Verificações de banco de dados
python scripts/production/verify/verify_all.py data    # Verificações de qualidade de dados
python scripts/production/verify/verify_all.py system  # Verificações de saúde do sistema
python scripts/production/verify/verify_all.py all     # Todas as verificações
```

**Modos:**
- `db` - Verifica conexão, qualidade de dados e duplicados no banco
- `data` - Verifica qualidade de dados, valuations e scores
- `system` - Verifica dependências, configuração e conexão
- `all` - Executa todas as verificações

#### debug_remax.py
Script consolidado para debug do spider REMAX.

**Uso:**
```bash
python scripts/production/verify/debug_remax.py probe <url>          # Probe simples de URL
python scripts/production/verify/debug_remax.py direct [limit]       # Debug do spider direto
python scripts/production/verify/debug_remax.py html <url>           # Análise de estrutura HTML
python scripts/production/verify/debug_remax.py simple <url>         # Verificação simples de padrões
```

**Modos:**
- `probe` - Fetch e análise simples de uma URL
- `direct` - Debug do spider REMAXDirectSpider
- `html` - Análise da estrutura HTML
- `simple` - Verificação simples de padrões

## 🔧 Scripts de Debug

A pasta `scripts/debug/` contém scripts de desenvolvimento e debug. **Estes scripts não são versionados no Git** (ver `.gitignore`).

### Scripts Temporários

Scripts temporários (com prefixo `_`) devem ser movidos para `scripts/archive/temp_debug/` quando não forem mais necessários.

### Scripts Ativos

Scripts sem prefixo `_` podem ser mantidos em `scripts/debug/` se forem usados ativamente para desenvolvimento.

## 📦 Scripts Arquivados

### temp_debug/
Contém scripts temporários que foram arquivados. Inclui:
- Scripts de probe (_probe_*.py)
- Scripts de teste (_test_*.py)
- Scripts de debug (_debug_*.py)
- Scripts de verificação antigos (check_*.py, verify_*.py)

**Nota:** Estes scripts não devem ser usados em produção. Use os scripts consolidados em `scripts/production/`.

## 📝 Convenções de Naming

### Prefixos

- `check_` - Scripts de verificação rápida
- `verify_` - Scripts de verificação detalhada
- `debug_` - Scripts de debug
- `probe_` - Scripts de probe/teste de componentes
- `clean_` - Scripts de limpeza
- `run_` - Scripts para executar pipelines
- `analyze_` - Scripts de análise de dados

### Nomes de Ficheiros

- Usar `snake_case` para todos os scripts
- Nomes descritivos que indicam a função
- Evitar números de versão (ex: `script_v2.py`)
- Evitar sufixos como `_final`, `_ok`, `_new`

### Exemplos

✅ **CORRETO:**
- `clean_db.py`
- `verify_all.py`
- `debug_remax.py`
- `run_scraping.py`

❌ **INCORRETO:**
- `script_final_v2.py`
- `test123.py`
- `debug_script_ok.py`
- `my_script_new.py`

## 🔒 Scripts no Gitignore

Os seguintes padrões estão no `.gitignore`:
- `scripts/debug/` - Scripts de debug não versionados
- `scripts/__pycache__/` - Cache Python
- `*.bak` - Ficheiros de backup
- `*.tmp` - Ficheiros temporários

Scripts de produção em `scripts/production/` DEVEM ser versionados.

## 📋 Critérios de Manutenção

### Quando Arquivar um Script

Arquivar um script quando:
- Não foi usado nos últimos 30 dias
- Foi substituído por um script consolidado
- É um script de teste one-off
- Tem prefixo `_` indicando natureza temporária

### Quando Consolidar Scripts

Consolidar scripts quando:
- Múltiplos scripts fazem a mesma coisa com pequenas variações
- Scripts têm nomes similares (ex: `probe_remax.py`, `probe_remax2.py`)
- Funcionalidade pode ser organizada com modos/argumentos

### Quando Remover Scripts

Remover scripts quando:
- Estão completamente obsoletos
- Têm bugs críticos que não serão corrigidos
- Foram substituídos há mais de 6 meses

## 🚨 Avisos de Segurança

- Scripts de limpeza (`clean_`) podem apagar dados - sempre fazer backup primeiro
- Scripts de manutenção podem afetar o sistema em produção - testar em ambiente de dev primeiro
- Scripts de debug podem ter código experimental - não usar em produção

## 📞 Suporte

Para dúvidas sobre scripts, consulte:
- Documentação do projeto em `docs/`
- README principal na raiz
- Política de idiomas em `docs/LANGUAGE_POLICY.md`

---

**Última atualização:** 2026-05-05  
**Versão:** 1.0
