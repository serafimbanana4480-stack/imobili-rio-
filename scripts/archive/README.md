# Archive — Scripts

Esta pasta contém scripts arquivados que não são mais ativamente usados.

## 📁 Estrutura

### temp_debug/
Scripts temporários de debug que foram movidos de `scripts/debug/`.

**Contém:**
- Scripts com prefixo `_` (indicando natureza temporária)
- Scripts de probe e teste one-off
- Scripts de debug de componentes específicos
- Scripts de verificação antigos

**Critério de arquivo:**
- Scripts não usados nos últimos 30 dias
- Scripts substituídos por versões consolidadas
- Scripts de teste one-off
- Scripts experimentais

**Aviso:** Estes scripts não devem ser usados em produção. Use os scripts consolidados em `scripts/production/`.

## 📋 Critérios de Arquivo

Scripts são arquivados quando:
1. **Não utilizado:** Não foi usado nos últimos 30 dias
2. **Substituído:** Foi substituído por um script consolidado
3. **One-off:** Script de teste único que não será reutilizado
4. **Experimental:** Código experimental não destinado a produção
5. **Obsoleto:** Funcionalidade obsoleta ou removida

## 🔍 Quando Restaurar

Um script pode ser restaurado de `archive/` se:
- A funcionalidade é novamente necessária
- O script consolidado não cobre o caso de uso
- Há necessidade de debug específico

**Processo de restauração:**
1. Mover script de volta para local apropriado
2. Atualizar conforme necessário (imports, paths, etc.)
3. Testar antes de usar em produção
4. Remover de archive/ após confirmação

## 🗑️ Quando Apagar

Scripts podem ser apagados permanentemente se:
- Estão arquivados há mais de 6 meses
- A funcionalidade foi completamente removida do sistema
- Não há histórico de uso relevante
- Não há valor de referência para o futuro

## 📞 Suporte

Para dúvidas sobre scripts arquivados, consulte:
- `scripts/README.md` - Convenções e critérios
- Documentação do projeto em `docs/`

---

**Última atualização:** 2026-05-05  
**Versão:** 1.0
