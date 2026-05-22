# Política de Idiomas — Real Estate Opportunity Engine

**Data:** 2026-05-05  
**Versão:** 1.0

---

## 📋 Visão Geral

Este documento define a política de idiomas para todo o projeto, incluindo código, documentação, comentários e comunicação.

## 🎯 Idioma Principal

**Português (PT-PT)** é o idioma principal do projeto para:
- Documentação de utilizador
- Manuais de uso
- Documentos de planeamento
- Interface do utilizador (dashboard)
- Mensagens de erro visíveis ao utilizador

## 📐 Idiomas por Categoria

### Código e Comentários

**Inglês** para:
- Nomes de variáveis, funções, classes, módulos
- Comentários de código
- Docstrings (PEP 257)
- Nomes de ficheiros e pastas
- Commit messages (Git)

**Racional:** Inglês é a língua padrão da indústria de software, facilitando colaboração e manutenção.

### Documentação Técnica

**Inglês** para:
- Documentação de API
- Arquitetura técnica detalhada
- Especificações técnicas
- Diagramas e documentação de banco de dados

**Português** para:
- Documentação geral do projeto (README.md)
- Manuais de utilização
- Guias de instalação
- Troubleshooting para utilizadores

### Documentação de Planeamento

**Português** para:
- Todos os documentos em `planeamento/`
- Roadmaps e estratégias
- Documentos de decisão técnica (quando dirigidos à equipa local)

### Testes

**Inglês** para:
- Nomes de testes
- Mensagens de assert
- Comentários em testes
- Descrições de fixtures

**Racional:** Testes são frequentemente revisados por desenvolvedores de diferentes origens.

### Scripts de Automação

**Inglês** para:
- Nomes de scripts
- Argumentos de linha de comando
- Mensagens de help
- Comentários em scripts

**Português** para:
- Mensagens de output visíveis ao utilizador final
- Mensagens de erro em scripts de produção

## 🔓 Exceções

### Terminologia Técnica

Manter termos técnicos em inglês quando não houver tradução adequada:
- "API" (não "Interface de Programação de Aplicações")
- "Dashboard" (não "Painel de Controlo")
- "Pipeline" (não "Linha de Processamento")
- "Scraping" (não "Raspagem de Dados")
- "Endpoint" (não "Ponto Final")
- "Deployment" (não "Implementação")

### Código Legado

Código existente que não segue esta política deve ser atualizado gradualmente, não como um bloqueador para outras tarefas.

### Bibliotecas de Terceiros

Manter a língua original da documentação de bibliotecas de terceiros.

## 📝 Regras Práticas

### Nomes de Variáveis e Funções

```python
# ✅ CORRETO
def calculate_discount(price: float, discount_rate: float) -> float:
    """Calculate the discounted price."""
    return price * (1 - discount_rate)

# ❌ INCORRETO
def calcular_desconto(preco: float, taxa_desconto: float) -> float:
    """Calcular o preço com desconto."""
    return preco * (1 - taxa_desconto)
```

### Docstrings

```python
# ✅ CORRETO
def fetch_listings(portal: str) -> List[Dict]:
    """Fetch listings from the specified portal.
    
    Args:
        portal: Name of the real estate portal (e.g., 'idealista', 'remax')
        
    Returns:
        List of listing dictionaries
        
    Raises:
        ConnectionError: If the portal is unreachable
    """
    pass

# ❌ INCORRETO
def buscar_anuncios(portal: str) -> List[Dict]:
    """Busca anúncios do portal especificado.
    
    Argumentos:
        portal: Nome do portal imobiliário
        
    Retorna:
        Lista de dicionários de anúncios
        
    Levanta:
        ConnectionError: Se o portal estiver inacessível
    """
    pass
```

### Comentários

```python
# ✅ CORRETO
# Calculate the weighted score using the formula:
# score = discount * 0.45 + location * 0.20 + condition * 0.15
weighted_score = discount * 0.45 + location * 0.20 + condition * 0.15

# ❌ INCORRETO
# Calcula o score ponderado usando a fórmula:
# score = desconto * 0.45 + localizacao * 0.20 + condicao * 0.15
score_ponderado = desconto * 0.45 + localizacao * 0.20 + condicao * 0.15
```

### Mensagens de Utilizador

```python
# ✅ CORRETO (para utilizador final)
print("Erro: Não foi possível conectar ao banco de dados")
print("A iniciar scraping do portal Idealista...")

# ❌ INCORRETO (para utilizador final)
print("Error: Failed to connect to database")
print("Starting scraping of Idealista portal...")
```

### Commit Messages

```bash
# ✅ CORRETO
git commit -m "Add XGBoost model for valuation"
git commit -m "Fix memory leak in spider manager"
git commit -m "Update README with installation instructions"

# ❌ INCORRETO
git commit -m "Adicionar modelo XGBoost para valuation"
git commit -m "Corrigir leak de memória no spider manager"
```

## 🔄 Migração

### Código Existente

Para código existente que não segue esta política:
1. Priorizar atualização de código ativamente modificado
2. Não bloquear novas features por causa de idioma
3. Atualizar gradualmente durante refatoração natural

### Documentação Existente

Para documentação existente:
1. Atualizar documentos ativamente usados primeiro
2. Arquivar documentos desatualizados
3. Traduzir documentos críticos quando possível

## ✅ Checklist

Ao criar novo conteúdo:
- [ ] Código: variáveis, funções, classes em inglês
- [ ] Comentários de código em inglês
- [ ] Docstrings em inglês
- [ ] Commit messages em inglês
- [ ] Documentação técnica em inglês
- [ ] Documentação de utilizador em português
- [ ] Mensagens de utilizador em português
- [ ] Planeamento em português

## 📞 Dúvidas

Se houver dúvidas sobre qual idioma usar:
1. Consultar este documento
2. Verificar exemplos similares no código existente
3. Perguntar na equipa

---

**Última atualização:** 2026-05-05  
**Próxima revisão:** 2026-08-05 (3 meses)
