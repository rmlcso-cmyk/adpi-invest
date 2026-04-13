import os, json, hashlib, urllib.request, urllib.parse

GOOGLE_API_KEY = os.environ.get('GOOGLE_TRANSLATE_KEY', '')
CACHE = {}

LANGUAGES = {
    'pt': {'name': 'PT', 'flag': '🇵🇹', 'rtl': False, 'full': 'Português'},
    'en': {'name': 'EN', 'flag': '🇬🇧', 'rtl': False, 'full': 'English'},
    'es': {'name': 'ES', 'flag': '🇪🇸', 'rtl': False, 'full': 'Español'},
    'fr': {'name': 'FR', 'flag': '🇫🇷', 'rtl': False, 'full': 'Français'},
    'de': {'name': 'DE', 'flag': '🇩🇪', 'rtl': False, 'full': 'Deutsch'},
    'it': {'name': 'IT', 'flag': '🇮🇹', 'rtl': False, 'full': 'Italiano'},
    'ar': {'name': 'AR', 'flag': '🇦🇪', 'rtl': True,  'full': 'العربية'},
}

UI_PT = {
    'investor_portal': 'Portal',
    'admin_access': 'Admin',
    'all_phases': 'Todas as fases',
    'phase_10': 'Phase 1.0 — Real Estate',
    'phase_20': 'Phase 2.0 — Representação',
    'all_sectors': 'Todos os sectores',
    'search_placeholder': 'Pesquisar...',
    'search_btn': 'Pesquisar',
    'hero_eyebrow': 'Abu Dhabi · Portugal Investment Platform',
    'hero_title': 'Oportunidades de Investimento em Portugal',
    'hero_sub': 'Acesso privilegiado a oportunidades selecionadas nas áreas de imobiliário, infraestrutura, energia, blue economy, agricultura e private equity.',
    'found': 'encontrada(s)',
    'opportunity': 'oportunidade(s)',
    'see_details': 'Ver detalhes',
    'min': 'mín.',
    'available': 'Disponível',
    'in_analysis': 'Em análise',
    'reserved': 'Reservado',
    'back': '← Voltar',
    'description': 'Descrição da oportunidade',
    'project_data': 'Dados do projeto',
    'min_investment': 'Investimento mínimo',
    'location': 'Localização',
    'area': 'Área',
    'jobs': 'Postos de trabalho',
    'expected_return': 'Retorno esperado',
    'horizon': 'Horizonte temporal',
    'documents': 'Documentos disponíveis',
    'download': 'Download',
    'download_pdf': 'Download PDF Brochura',
    'contact_team': 'Contactar equipa ADPI',
    'direct': 'diretos',
    'hectares': 'ha',
    'footer_contact': 'investimento@adpi.pt · +351 266 000 000 · Cascais / Lisboa',
    'no_results': 'Nenhuma oportunidade encontrada.',
    'clear_filters': 'Limpar filtros',
    'contact_more': 'Para mais informações',
    'contact_sub': 'Contacte a equipa ADPI para obter informação detalhada.',
    'password_label': 'Password de administrador',
    'login_btn': 'Entrar',
    'login_title': 'Acesso Restrito',
    'login_sub': 'Área reservada à equipa ADPI.',
    'back_portal': '← Voltar ao portal',
    'dashboard_title': 'Dashboard ADPI Admin',
    'dashboard_sub': 'Gestão das oportunidades publicadas no portal',
    'new_opp': '+ Nova Oportunidade',
    'logout': 'Sair',
    'total_opps': 'Total de Oportunidades',
    'total_invest': 'Investimento Total',
    'total_jobs': 'Postos de Trabalho',
    'sectors': 'Sectores',
    'published': 'publicadas no portal',
    'sum_projects': 'soma dos projetos',
    'direct_creation': 'criação direta prevista',
    'areas': 'áreas representadas',
    'edit': 'Editar',
    'delete_confirm': 'Eliminar esta oportunidade?',
    'form_title_new': 'Nova Oportunidade',
    'form_title_edit': 'Editar Oportunidade',
    'form_sub_new': 'Preencha os dados para publicar no portal',
    'form_sub_edit': 'Atualizar dados publicados no portal',
    'cancel': 'Cancelar',
    'save': 'Guardar alterações',
    'publish': 'Publicar oportunidade',
    'main_info': 'Informação principal',
    'title_label': 'Título / Designação *',
    'sector_label': 'Sector *',
    'municipio_label': 'Município *',
    'fase_label': 'Fase ADPI',
    'estado_label': 'Estado',
    'desc_label': 'Descrição *',
    'financial_data': 'Dados financeiros e dimensão',
    'invest_label': 'Investimento mínimo (€)',
    'area_label': 'Área (hectares)',
    'jobs_label': 'Postos de trabalho diretos',
    'return_label': 'Retorno esperado',
    'horizon_label': 'Horizonte temporal',
    'media_title': 'Imagens e documentos',
    'photos_label': 'Fotografias do projeto',
    'docs_label': 'Documentos (brochuras, estudos)',
    'add_photos': 'Clique para adicionar fotos',
    'add_docs': 'Clique para adicionar documentos',
    'select_sector': 'Selecionar sector...',
    'select_mun': 'Selecionar...',
}

def _google(text, lang):
    if not text or not GOOGLE_API_KEY: return text
    ck = hashlib.md5(f'{lang}:{text}'.encode()).hexdigest()
    if ck in CACHE: return CACHE[ck]
    try:
        data = urllib.parse.urlencode({
            'q': text, 'source': 'pt', 'target': lang,
            'key': GOOGLE_API_KEY, 'format': 'text'
        }).encode()
        req = urllib.request.Request(
            'https://translation.googleapis.com/language/translate/v2',
            data=data, method='POST')
        req.add_header('Content-Type', 'application/x-www-form-urlencoded')
        with urllib.request.urlopen(req, timeout=6) as r:
            res = json.loads(r.read().decode())
            t = res['data']['translations'][0]['translatedText']
            CACHE[ck] = t
            return t
    except Exception as e:
        print(f"Translate error: {e}")
        return text

def translate_ui(lang):
    if lang == 'pt': return UI_PT
    ck = f'ui_{lang}'
    if ck in CACHE: return CACHE[ck]
    result = {k: _google(v, lang) for k, v in UI_PT.items()}
    CACHE[ck] = result
    return result

def translate_opp(opp, lang):
    if lang == 'pt': return opp
    o = dict(opp)
    o['titulo']    = _google(opp.get('titulo', ''), lang)
    o['descricao'] = _google(opp.get('descricao', ''), lang)
    return o
