import os
import json
import hashlib
import urllib.request
import urllib.parse

GOOGLE_API_KEY = os.environ.get('GOOGLE_TRANSLATE_KEY', '')

CACHE = {}

LANGUAGES = {
    'pt': {'name': 'Português', 'flag': '🇵🇹', 'rtl': False},
    'en': {'name': 'English',   'flag': '🇬🇧', 'rtl': False},
    'es': {'name': 'Español',   'flag': '🇪🇸', 'rtl': False},
    'fr': {'name': 'Français',  'flag': '🇫🇷', 'rtl': False},
    'de': {'name': 'Deutsch',   'flag': '🇩🇪', 'rtl': False},
    'it': {'name': 'Italiano',  'flag': '🇮🇹', 'rtl': False},
    'ar': {'name': 'العربية',   'flag': '🇦🇪', 'rtl': True},
}

GOOGLE_LANG = {
    'pt': 'pt', 'en': 'en', 'es': 'es',
    'fr': 'fr', 'de': 'de', 'it': 'it', 'ar': 'ar',
}

UI_STRINGS_PT = {
    'portal_title': 'Oportunidades de Investimento em Portugal',
    'portal_sub': 'Acesso privilegiado a oportunidades selecionadas nas áreas de imobiliário, infraestrutura, energia, blue economy, agricultura e private equity.',
    'all_phases': 'Todas as fases',
    'all_sectors': 'Todos os sectores',
    'search_placeholder': 'Pesquisar oportunidades...',
    'search_btn': 'Pesquisar',
    'see_details': 'Ver detalhes →',
    'min_invest': 'mín.',
    'opportunities_found': 'oportunidade(s) encontrada(s)',
    'download_pdf': 'Download PDF Brochura',
    'contact_team': 'Contactar equipa ADPI',
    'description': 'Descrição da oportunidade',
    'project_data': 'Dados do projeto',
    'min_investment': 'Investimento mínimo',
    'location': 'Localização',
    'area': 'Área',
    'jobs': 'Postos de trabalho',
    'expected_return': 'Retorno esperado',
    'horizon': 'Horizonte temporal',
    'documents': 'Documentos disponíveis',
    'back': '← Voltar às oportunidades',
    'available': 'Disponível',
    'in_analysis': 'Em análise',
    'reserved': 'Reservado',
    'admin_access': 'Área Admin',
    'investor_portal': 'Portal de Investimento',
    'direct_workers': 'diretos',
    'hectares': 'hectares',
    'phase_10': 'Phase 1.0 — Real Estate',
    'phase_20': 'Phase 2.0 — Representação',
}

def google_translate(text, target_lang):
    if not text or not GOOGLE_API_KEY:
        return text
    cache_key = hashlib.md5(f'{target_lang}:{text}'.encode()).hexdigest()
    if cache_key in CACHE:
        return CACHE[cache_key]
    try:
        url = 'https://translation.googleapis.com/language/translate/v2'
        data = urllib.parse.urlencode({
            'q': text,
            'source': 'pt',
            'target': GOOGLE_LANG.get(target_lang, target_lang),
            'key': GOOGLE_API_KEY,
            'format': 'text'
        }).encode('utf-8')
        req = urllib.request.Request(url, data=data, method='POST')
        req.add_header('Content-Type', 'application/x-www-form-urlencoded')
        with urllib.request.urlopen(req, timeout=5) as r:
            result = json.loads(r.read().decode('utf-8'))
            translated = result['data']['translations'][0]['translatedText']
            CACHE[cache_key] = translated
            return translated
    except Exception as e:
        print(f"Google Translate error: {e}")
        return text

def translate_ui(lang):
    if lang == 'pt' or lang not in LANGUAGES:
        return UI_STRINGS_PT
    cache_key = f'ui_{lang}'
    if cache_key in CACHE:
        return CACHE[cache_key]
    translated = {}
    for key, val in UI_STRINGS_PT.items():
        translated[key] = google_translate(val, lang)
    CACHE[cache_key] = translated
    return translated

def translate_text(text, lang):
    if not text or lang == 'pt':
        return text
    return google_translate(text, lang)

def translate_opp(opp, lang):
    if lang == 'pt':
        return opp
    o = dict(opp)
    o['titulo'] = translate_text(opp.get('titulo', ''), lang)
    o['descricao'] = translate_text(opp.get('descricao', ''), lang)
    return o
