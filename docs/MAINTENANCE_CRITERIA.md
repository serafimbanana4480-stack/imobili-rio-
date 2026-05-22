# Critérios de Manutenção — Real Estate Engine

**Data:** 2026-05-05  
**Versão:** 1.0

---

## 📋 Visão Geral

Este documento define os critérios para manutenção do projeto, incluindo quando arquivar, consolidar, remover ou atualizar ficheiros e componentes.

## 🗂️ Critérios de Arquivamento

### Scripts

**Arquivar quando:**
- Script não foi usado nos últimos 30 dias
- Script foi substituído por versão consolidada
- Script é one-off (teste único, não será reutilizado)
- Script é experimental (não destinado a produção)
- Script tem prefixo `_` indicando natureza temporária

**Processo:**
1. Mover para `scripts/archive/temp_debug/`
2. Adicionar comentário no README do archive explicando motivo
3. Atualizar `scripts/README.md` se necessário

**Exceções:**
- Scripts de produção em `scripts/production/` NUNCA devem ser arquivados sem revisão
- Scripts críticos de segurança devem ser mantidos mesmo que não usados

### Relatórios

**Arquivar quando:**
- Relatório tem data específica no nome e existe versão mais recente
- Informação foi consolidada em outro relatório
- Relatório está obsoleto (informação não mais relevante)
- Auditoria de fase específica já foi implementada

**Processo:**
1. Mover para `docs/reports/archive/`
2. Adicionar entrada no README do archive
3. Atualizar `docs/INDEX.md` para remover referência

### Documentação

**Arquivar quando:**
- Documento desatualizado e não será atualizado
- Documento substituído por versão mais recente
- Documento sobre funcionalidade removida

**Processo:**
1. Mover para `docs/archive/` (criar se necessário)
2. Adicionar entrada no README do archive
3. Atualizar índices de documentação

## 🔄 Critérios de Consolidação

### Scripts

**Consolidar quando:**
- Múltiplos scripts fazem a mesma coisa com pequenas variações
- Scripts têm nomes similares (ex: `probe_remax.py`, `probe_remax2.py`)
- Funcionalidade pode ser organizada com modos/argumentos
- Scripts duplicam código significativo

**Exemplo:**
```
# Antes
probe_remax.py
probe_remax2.py
debug_remax.py
debug_remax_html.py

# Depois
debug_remax.py (com modos: probe, direct, html, simple)
```

**Processo:**
1. Criar script unificado com argumentos/modes
2. Testar todas as funcionalidades
3. Arquivar scripts originais
4. Atualizar documentação

### Documentação

**Consolidar quando:**
- Múltiplos READMEs com conteúdo sobreposto
- Informação espalhada em vários ficheiros
- Documentos de mesmo tipo em locais diferentes

**Exemplo:**
```
# Antes
README.md (raiz)
realestate_engine/README.md
docs/README.md
docs/como_usar/README.md

# Depois
README.md (raiz) - principal
realestate_engine/README.md - índice simples apontando para raiz
docs/README.md - índice de documentação
docs/como_usar/README.md - índice local
```

## 🗑️ Critérios de Remoção

### Scripts

**Remover quando:**
- Script está arquivado há mais de 6 meses
- Funcionalidade foi completamente removida do sistema
- Script tem bugs críticos que não serão corrigidos
- Script foi substituído há mais de 6 meses

**Processo:**
1. Verificar se há referências ao script em outros lugares
2. Confirmar que não há valor histórico
3. Remover do archive
4. Atualizar READMEs se necessário

### Relatórios

**Remover quando:**
- Arquivado há mais de 12 meses
- Informação completamente irrelevante
- Sem valor histórico ou de referência
- Backup existe em outro local

**Processo:**
1. Verificar se há referências em índices
2. Confirmar que não é necessário para auditoria
3. Remover do archive
4. Atualizar índices

### Ficheiros Temporários

**Remover imediatamente quando:**
- Ficheiros `.bak`, `.tmp`, `.old`
- Ficheiros de backup não versionados
- Ficheiros temporários de compilação
- Ficheiros de cache do IDE

## 📅 Revisão Periódica

### Mensal

Revisar:
- Scripts em `scripts/debug/` (arquivar se não usados)
- Scripts em `scripts/archive/temp_debug/` (remover se > 6 meses)
- Relatórios recentes (consolidar se necessário)

### Trimestral

Revisar:
- Estrutura geral de diretórios
- Documentação desatualizada
- Scripts de produção (consolidar se possível)
- Convenções de naming (atualizar se necessário)

### Semestral

Revisar:
- Relatórios arquivados (remover se > 12 meses)
- Entry points (avaliar consolidação)
- Dependências obsoletas
- Política de idiomas (atualizar se necessário)

## ✅ Checklist de Manutenção

### Antes de Arquivar
- [ ] Verificar se script/ficheiro ainda é necessário
- [ ] Confirmar que não há referências ativas
- [ ] Documentar motivo do arquivamento
- [ ] Atualizar READMEs relevantes
- [ ] Testar se sistema funciona sem o item

### Antes de Consolidar
- [ ] Identificar todos os ficheiros relacionados
- [ ] Criar plano de consolidação
- [ ] Testar versão consolidada
- [ ] Arquivar originais
- [ ] Atualizar documentação
- [ ] Comunicar mudança à equipa

### Antes de Remover
- [ ] Confirmar que item não é necessário
- [ ] Verificar se há valor histórico
- [ ] Remover referências em outros ficheiros
- [ ] Atualizar índices e READMEs
- [ ] Commit com mensagem clara

## 🚨 Avisos de Segurança

### Scripts de Limpeza
- Sempre fazer backup antes de executar
- Testar em ambiente de desenvolvimento
- Rever código antes de usar em produção
- Documentar o que o script faz

### Scripts de Manutenção
- Testar em ambiente de staging primeiro
- Verificar impactos em sistema em produção
- Ter plano de rollback
- Monitorizar após execução

### Remoção de Ficheiros
- Verificar se ficheiro é crítico
- Confirmar que não há dependências
- Ter backup disponível
- Comunicar mudança à equipa

## 📊 Métricas de Manutenção

### Indicadores a Monitorizar
- Número de scripts em `scripts/debug/`
- Número de scripts em `scripts/archive/`
- Idade de relatórios arquivados
- Número de READMEs duplicados
- Número de scripts não versionados

### Metas
- Scripts debug: < 10 ativos
- Scripts archive: < 30 (remover antigos)
- Relatórios archive: < 20 (remover antigos)
- READMEs duplicados: 0
- Scripts não versionados: 0 (exceto debug/)

## 📞 Processo de Decisão

### Dúvida sobre Arquivar vs Manter

1. **Usado nos últimos 30 dias?**
   - Sim: Manter
   - Não: Ir para 2

2. **Substituído por versão consolidada?**
   - Sim: Arquivar
   - Não: Ir para 3

3. **Valor histórico ou de referência?**
   - Sim: Arquivar
   - Não: Ir para 4

4. **Funcionalidade ainda relevante?**
   - Sim: Manter
   - Não: Remover

### Dúvida sobre Consolidar vs Não

1. **Funcionalidade sobreposta?**
   - Sim: Considerar consolidação
   - Não: Não consolidar

2. **Benefício da consolidação > custo?**
   - Sim: Consolidar
   - Não: Não consolidar

3. **Risco de quebrar funcionalidade?**
   - Alto: Não consolidar (ou fazer gradualmente)
   - Baixo: Consolidar

## 🔄 Ciclo de Vida de Componentes

```
Criação → Uso Ativo → Revisão (30 dias) →
  ↓                        ↓
Manter                   Arquivar (se não usado)
  ↓                        ↓
Revisão (6 meses) → Remover (se não necessário)
```

---

**Última atualização:** 2026-05-05  
**Próxima revisão:** 2026-08-05 (3 meses)
