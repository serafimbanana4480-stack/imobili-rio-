"""Test enricher amenities extraction."""
from realestate_engine.etl.enricher import Enricher

e = Enricher()
test = {
    'titulo': 'T3 com garagem e cozinha separada', 
    'descricao': 'Apartamento com ar condicionado, cozinha separada, máquina de lavar e fogão'
}
result = e.enrich_amenities(test)
print(f'Garagem: {result.get("tem_garagem")}')
print(f'CozSep: {result.get("cozinha_separada")}')
print(f'AC: {result.get("tem_ac")}')
print(f'MaqLavar: {result.get("tem_maquina_lavar")}')
print(f'Fogao: {result.get("tem_fogao")}')
