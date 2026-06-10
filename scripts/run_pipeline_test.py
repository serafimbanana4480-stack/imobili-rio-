"""Script para executar o pipeline de valuation e scoring com dados INE atualizados."""
import sys, os, sqlite3

# Carregar .env explicitamente da raiz do projeto antes de qualquer import
from dotenv import load_dotenv
project_root = r'C:\Users\rodri\Desktop\Projeto analize mercado imobeleario'
load_dotenv(os.path.join(project_root, '.env'))

sys.path.insert(0, project_root)
os.environ['REE_CHROME_PATH'] = r'C:\Program Files\Google\Chrome\Application\chrome.exe'

from realestate_engine.database.repository import DatabaseRepository
from realestate_engine.valuation.valuation_engine import ValuationEngine
from realestate_engine.database.models import Valuation

repo = DatabaseRepository()

# Verificar dados existentes
conn = sqlite3.connect(os.path.join(project_root, 'data', 'db', 'realestate.db'))
c = conn.cursor()
c.execute('SELECT COUNT(*) FROM clean_listings')
total_listings = c.fetchone()[0]
c.execute('SELECT COUNT(*) FROM valuations')
total_valuations = c.fetchone()[0]
c.execute('SELECT COUNT(*) FROM scores')
total_scores = c.fetchone()[0]
conn.close()

print(f'Dados existentes: {total_listings} listings, {total_valuations} valuations, {total_scores} scores')

# Executar valuation engine
print('\n=== Executando Valuation Engine ===')
engine = ValuationEngine(repo=repo)

# Forçar retrain para usar os novos dados INE
print('Retreinando modelos...')
trained_count = engine.retrain()
print(f'Modelos retreinados com {trained_count} listings')

# Valuar sample de listings
print('\n=== Valuando sample de 10 listings ===')
listings = repo.get_clean_listings(limit=10)
sample_results = []
for listing in listings:
    listing_dict = {
        'preco_pedido': listing.preco_pedido,
        'area_util_m2': listing.area_util_m2,
        'quartos': listing.quartos,
        'casas_banho': listing.casas_banho,
        'ano_construcao': listing.ano_construcao,
        'freguesia': listing.freguesia,
        'concelho': listing.concelho,
        'distrito': listing.distrito,
        'lat': listing.lat,
        'lon': listing.lon,
        'dist_metro_m': listing.dist_metro_m,
        'dist_escola_m': listing.dist_escola_m,
        'dist_comercio_m': listing.dist_comercio_m,
        'estado': listing.estado,
        'cert_energetico': listing.cert_energetico,
        'tipologia': listing.tipologia,
        'preco_por_m2': listing.preco_por_m2,
        'ine_preco_medio_m2': listing.ine_preco_medio_m2,
        'ine_tendencia_mensal': listing.ine_tendencia_mensal,
        'num_fotos': listing.num_fotos,
        'scrape_timestamp': listing.scrape_timestamp,
        'source_id': listing.source_id,
        'source_portal': listing.source_portal,
        'tem_garagem': getattr(listing, 'tem_garagem', None),
        'tem_piscina': getattr(listing, 'tem_piscina', None),
        'tem_vista_mar': getattr(listing, 'tem_vista_mar', None),
        'tem_vista_rio': getattr(listing, 'tem_vista_rio', None),
        'andar': getattr(listing, 'andar', None),
    }
    
    result = engine.valuate_advanced(listing_dict)
    if result:
        discount_pct = round((listing.preco_pedido - result['valor_justo']) / listing.preco_pedido * 100, 1) if listing.preco_pedido > 0 else 0
        sample_results.append({
            'id': listing.id,
            'concelho': listing.concelho,
            'preco_pedido': listing.preco_pedido,
            'valor_justo': result['valor_justo'],
            'confianca': result['confianca'],
            'discount': discount_pct,
            'models_active': result['models_active'],
            'ci_lower': result['ci_lower'],
            'ci_upper': result['ci_upper'],
        })

print(f'\nSample de {len(sample_results)} valuations:')
for r in sample_results:
    print(f"  {r['concelho']}: Pedido={r['preco_pedido']:.0f}€ | Justo={r['valor_justo']:.0f}€ | Discount={r['discount']}% | Conf={r['confianca']:.2f} | Models={r['models_active']}")

print('\n=== Pipeline executado com sucesso ===')
