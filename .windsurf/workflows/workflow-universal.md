---
description: Workflow universal para todas as conversas - guia mestre com regras fundamentais
---

# Workflow Universal - Guia Mestre para Todas as Conversas

## PRINCÍPIOS FUNDAMENTAIS

### 1. NÃO ASSUMAS NADA
- **Nunca** presuma que o código funciona sem ver
- **Nunca** presuma que o teste passa sem executar
- **Nunca** presuma que a configuração está correta sem verificar
- **Nunca** presuma que o entendo do usuário está completo sem perguntar
- **Valida sempre** antes de afirmar qualquer coisa
- **Verifica sempre** com ferramentas antes de concluir

### 2. VALIDA COM EXEMPLOS
- Para cada afirmação técnica, mostra um exemplo concreto
- Para cada solução proposta, demonstra com código real
- Para cada problema identificado, mostra o cenário de teste
- Para cada mudança, justifica com antes/depois
- **Exemplos devem ser**:
  - Executáveis (não pseudocódigo)
  - Relevantes ao contexto atual
  - Completos (não snippets parciais)

### 3. IDENTIFICA CAUSAS RAIZ
- Não corrigas sintomas, corrige a origem
- Usa a técnica dos "5 porquês" para investigar
- Rastreia o problema até à fonte
- Documenta a cadeia de causalidade completa
- **Antes de corrigir**, pergunta:
  - Porque é que isto aconteceu?
  - O que permitiu que isto acontecesse?
  - Como podemos prevenir que volte a acontecer?

### 4. COMPARA COM SOLUÇÕES REAIS
- Pesquisa soluções existentes no códigobase
- Compara com padrões da indústria
- Referencia documentação oficial
- Analisa implementações similares
- **Justifica** porque a tua solução é melhor ou adequada

---

## FLUXO DE TRABALHO PADRÃO

### FASE 1: COMPREENSÃO
1. Lê o pedido do usuário completamente
2. **NÃO assumas** o contexto - verifica:
   - Lê arquivos relevantes
   - Verifica estado atual do código
   - Confirma dependências existentes
3. Pergunta se algo estiver ambíguo
4. **Valida** o entendimento com exemplos do que vais fazer

### FASE 2: ANÁLISE
1. Investiga o problema ou requisito
2. **Identifica causa raiz**:
   - Procura erros em logs
   - Rastreia stack traces
   - Examina código relacionado
3. **Compara com soluções reais**:
   - Procura padrões no códigobase
   - Verifica documentação
   - Analisa implementações similares
4. Documenta descobertas com exemplos concretos

### FASE 3: PLANEAMENTO
1. Crea plano detalhado (usa `todo_list` para tarefas complexas)
2. **Valida** plano com o usuário se necessário
3. Prioriza tarefas por impacto e risco
4. Identifica dependências entre tarefas

### FASE 4: EXECUÇÃO
1. Implementa mudanças mínimas necessárias (RULE #2)
2. **Valida** cada mudança:
   - Executa testes relevantes
   - Verifica com exemplos
   - Confirma que resolve a causa raiz
3. Documenta código (RULE #5)
4. Adiciona testes quando apropriado (RULE #3)

### FASE 5: VERIFICAÇÃO
1. **Não assumas** que funciona - verifica:
   - Executa testes automatizados
   - Testa manualmente se necessário
   - Valida com exemplos reais
2. Compara resultado com expectativas
3. Confirma que causa raiz foi resolvida
4. Documenta o que foi feito e porquê

---

## REGRAS ESPECÍFICAS POR TIPO DE TAREFA

### DEBUGGING
1. **NÃO assumas** onde está o bug - investiga sistematicamente
2. Adiciona logging para rastrear estado
3. **Identifica causa raiz** antes de corrigir
4. **Valida** a correção com teste que reproduz o bug
5. **Compara** com correções similares no códigobase

### DESENVOLVIMENTO DE NOVAS FEATURES
1. Verifica `.planning/` para planos existentes (RULE #1)
2. **Não assumas** requisitos - clarifica com usuário
3. **Valida** arquitetura com exemplos de uso
4. **Compara** com features similares no sistema
5. Implementa mudanças mínimas (RULE #2)
6. Adiciona testes (RULE #3)

### REFACTORING
1. **NÃO assumas** que refactoring é necessário - justifica
2. **Identifica causa** do problema de design
3. **Compara** com padrões estabelecidos
4. **Valida** que não quebra funcionalidade
5. Executa testes antes e depois

### CORREÇÃO DE BUGS
1. **NÃO assumas** a correção - investiga primeiro
2. **Identifica causa raiz** (não sintomas)
3. **Valida** com teste que reproduz o bug
4. **Compara** com correções anteriores
5. Faz mudança mínima (RULE #2)
6. Adiciona teste de regressão

### OTIMIZAÇÃO DE PERFORMANCE
1. **NÃO assumas** que é lento - mede primeiro
2. **Identifica causa raiz** da lentidão
3. **Compara** com benchmarks
4. **Valida** melhoria com métricas
5. Documenta trade-offs

---

## CHECKLIST ANTES DE QUALQUER AÇÃO

### VERIFICAÇÃO INICIAL
- [ ] Li o pedido completamente?
- [ ] **NÃO assumi** nada sem verificar?
- [ ] Li arquivos relevantes?
- [ ] Entendi o contexto atual?
- [ ] Perguntei se algo está ambíguo?

### VALIDAÇÃO
- [ ] Posso **validar** com exemplos concretos?
- [ ] Posso **identificar causa raiz** do problema?
- [ ] Posso **comparar** com soluções existentes?
- [ ] Tenho evidências para minhas afirmações?

### EXECUÇÃO
- [ ] Consultei `.planning/` antes de mudar código? (RULE #1)
- [ ] A mudança é mínima possível? (RULE #2)
- [ ] Adicionei testes apropriados? (RULE #3)
- [ ] Verifiquei segurança? (RULE #4)
- [ ] Documentei a mudança? (RULE #5)
- [ ] Tratei erros adequadamente? (RULE #6)
- [ ] Considerei performance? (RULE #7)
- [ ] Sigo padrões de API? (RULE #8)

### VERIFICAÇÃO FINAL
- [ ] **NÃO assumi** que funciona - executei/testei?
- [ ] **Valido** resultado com exemplos?
- [ ] **Identifiquei** que causa raiz foi resolvida?
- [ ] **Comparei** com expectativas originais?
- [ ] Documentei o que foi feito?

---

## PADRÕES DE COMUNICAÇÃO

### AO REPORTAR PROBLEMAS
1. Descreve o problema com exemplos concretos
2. Mostra evidências (logs, erros, screenshots)
3. **Identifica causa raiz** com análise
4. **Compara** com comportamento esperado
5. Propõe solução com justificação

### AO PROPOR SOLUÇÕES
1. **Não assumas** que a solução é óbvia
2. **Valida** com exemplos de código
3. **Identifica** porque resolve a causa raiz
4. **Compara** com alternativas
5. Justifica trade-offs

### AO FAZER MUDANÇAS
1. Explica o que vais fazer e porquê
2. **Valida** entendimento com exemplos
3. Mostra antes/depois quando relevante
4. **Identifica** impactos secundários
5. **Compara** com estado anterior

---

## FERRAMENTAS E TÉCNICAS

### INVESTIGAÇÃO
- Usa `Grep` para procurar padrões
- Usa `read_file` para ver código real
- Usa `find_by_name` para localizar arquivos
- Usa `bash` para executar comandos de diagnóstico
- **Nunca** confies em memória - verifica sempre

### VALIDAÇÃO
- Executa testes com `pytest`
- Roda aplicação para verificar
- Usa logs para rastrear comportamento
- Compara saída com expectativas
- Testa com dados reais quando possível

### DOCUMENTAÇÃO
- Adiciona comentários explicando PORQUÊ
- Usa docstrings para APIs públicas
- Atualiza README para mudanças de usuário
- Documenta decisões em `.planning/`
- Mantém documentação sincronizada com código

---

## TRATAMENTO DE INCERTEZA

### QUANDO NÃO TENS CERTEZA
1. **NÃO assumas** - admite incerteza
2. Investiga mais antes de agir
3. Pergunta ao usuário para clarificar
4. **Valida** hipóteses com testes
5. Documenta suposições explicitamente

### QUANDO HÁ MÚLTIPLAS SOLUÇÕES
1. **Compara** todas as opções
2. **Identifica** trade-offs de cada
3. **Valida** com protótipos se necessário
4. Apresenta ao usuário com recomendação
5. Justifica recomendação com evidências

---

## MÉTRICAS DE SUCESSO

### PARA CADA TAREFA
- [ ] Causa raiz identificada e documentada?
- [ ] Solução validada com exemplos?
- [ ] Comparado com soluções existentes?
- [ ] Testes adicionados quando apropriado?
- [ ] Documentação atualizada?
- [ ] Nenhuma suposição não verificada?

---

## REFERÊNCIAS RÁPIDAS

### REGRAS GLOBAIS DO USUÁRIO
- RULE #1: Consulta `.planning/` antes de mudanças
- RULE #2: Faz mudanças mínimas
- RULE #3: Desenvolvimento orientado a testes
- RULE #4: Abordagem security-first
- RULE #5: Requisitos de documentação
- RULE #6: Padrões de tratamento de erros
- RULE #7: Consciência de performance
- RULE #8: Princípios de design de API

### COMANDOS ÚTEIS
- `/gsd-plan-phase` - Criar plano para fase
- `/gsd-progress` - Ver progresso do projeto
- `/gsd-help` - Ver comandos disponíveis

### ARQUIVOS CHAVE
- `.planning/` - Planos e decisões do projeto
- `docs/` - Documentação do sistema
- `tests/` - Suíte de testes
- `README.md` - Documentação principal

---

## NOTA FINAL

**ESTE WORKFLOW É OBRIGATÓRIO PARA TODAS AS CONVERSAS.**

Antes de qualquer ação, pergunta:
1. **NÃO assumi** nada sem verificar?
2. **Vou validar** com exemplos?
3. **Identifiquei** a causa raiz?
4. **Comparei** com soluções reais?

Se a resposta for "não" para qualquer uma, PARA e investiga mais.
