import os, json, hashlib, urllib.request, urllib.parse

GOOGLE_API_KEY = os.environ.get('GOOGLE_TRANSLATE_KEY', '')
CACHE = {}

# Ordem: PT, EN, AR, depois resto
LANGUAGES = {
    'pt': {'flag': '🇵🇹', 'rtl': False, 'full': 'Português', 'google': 'pt'},
    'ar': {'flag': '🇦🇪', 'rtl': True,  'full': 'العربية',   'google': 'ar'},
    'en': {'flag': '🇬🇧', 'rtl': False, 'full': 'English',   'google': 'en'},
    'es': {'flag': '🇪🇸', 'rtl': False, 'full': 'Español',   'google': 'es'},
    'fr': {'flag': '🇫🇷', 'rtl': False, 'full': 'Français',  'google': 'fr'},
    'de': {'flag': '🇩🇪', 'rtl': False, 'full': 'Deutsch',   'google': 'de'},
    'it': {'flag': '🇮🇹', 'rtl': False, 'full': 'Italiano',  'google': 'it'},
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
    'estado_disponivel': 'Disponível',
    'estado_analise': 'Em análise',
    'estado_reservado': 'Reservado',
    'back': 'Voltar',
    'description': 'Descrição da oportunidade',
    'project_data': 'Dados do projeto',
    'min_investment': 'Investimento mínimo',
    'location': 'Localização',
    'area': 'Área',
    'hectares': 'ha',
    'jobs': 'Postos de trabalho',
    'expected_return': 'Retorno esperado',
    'horizon': 'Horizonte temporal',
    'documents': 'Documentos disponíveis',
    'download': 'Download',
    'download_pdf': 'Download PDF Brochura',
    'contact_team': 'Contactar equipa ADPI',
    'direct': 'diretos',
    'footer_contact': 'investimento@adpi.pt · +351 266 000 000 · Cascais / Lisboa',
    'no_results': 'Nenhuma oportunidade encontrada.',
    'clear_filters': 'Limpar filtros',
    'contact_more': 'Para mais informações',
    'contact_sub': 'Contacte a equipa ADPI para obter informação detalhada.',
    'pdf_confidential': 'Confidencial',
    'pdf_generated': 'Documento gerado em',
    'pdf_page': 'Pág',
    'fase_label_pdf': 'Fase',
    'sector_label_pdf': 'Sector',
    # Admin
    'password_label': 'Password de administrador',
    'login_btn': 'Entrar',
    'login_title': 'Acesso Restrito',
    'login_sub': 'Área reservada à equipa ADPI.',
    'back_portal': 'Voltar ao portal',
    'dashboard_title': 'Dashboard ADPI Admin',
    'dashboard_sub': 'Gestão das oportunidades publicadas no portal',
    'new_opp': 'Nova Oportunidade',
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
    'form_sub_new': 'Preencha os dados para publicar no portal do investidor',
    'form_sub_edit': 'Atualizar dados publicados no portal do investidor',
    'cancel': 'Cancelar',
    'save': 'Guardar alterações',
    'publish': 'Publicar oportunidade',
    'main_info': 'Informação principal',
    'title_label': 'Título / Designação',
    'title_ph': 'Ex: Solar Park North Alentejo',
    'sector_label': 'Sector',
    'municipio_label': 'Município / Cidade',
    'fase_label': 'Fase ADPI',
    'estado_label': 'Estado',
    'desc_label': 'Descrição',
    'desc_ph': 'Descreva a oportunidade de investimento...',
    'lang_content': 'Idioma do conteúdo inserido',
    'lang_content_sub': 'O conteúdo pode ser inserido em qualquer idioma. O sistema traduzirá automaticamente para os outros.',
    'financial_data': 'Dados financeiros e dimensão',
    'invest_label': 'Investimento mínimo (€)',
    'area_label': 'Área (hectares)',
    'jobs_label': 'Postos de trabalho diretos',
    'return_label': 'Retorno esperado',
    'return_ph': 'Ex: 10-15% ao ano',
    'horizon_label': 'Horizonte temporal',
    'horizon_ph': 'Ex: 5-7 anos',
    'media_title': 'Imagens e documentos',
    'photos_label': 'Fotografias do projeto',
    'docs_label': 'Documentos (brochuras, estudos)',
    'add_photos': 'Adicionar fotos',
    'add_docs': 'Adicionar documentos',
    'select_sector': 'Selecionar sector...',
    'select_mun': 'Selecionar...',
    'select_fase': 'Selecionar fase...',
    'opp_label': 'Oportunidade',
    'phase_label': 'Fase',
    'municipio_col': 'Município',
    'sector_col': 'Sector',
    'actions_label': 'Ações',
    'contact_title': 'Contactar a equipa ADPI',
    'contact_email': 'Email',
    'contact_phone': 'Telefone',
    'contact_close': 'Fechar',
}

def _sanitize(text):
    """Fix common Google Translate errors."""
    # "15-20 years old" should be "15-20 years"
    import re
    text = re.sub(r'(\d+[-\u2013]\d+)\s+years?\s+old', r'\1 years', text)
    text = re.sub(r'(\d+)\s+years?\s+old', r'\1 years', text)
    # "8-12% per year old" fix
    text = re.sub(r'per\s+year\s+old', 'per year', text)
    return text

def _google(text, target_lang, source_lang='pt'):
    if not text or not GOOGLE_API_KEY or target_lang == source_lang:
        return text
    ck = hashlib.md5(f'{source_lang}>{target_lang}:{text}'.encode()).hexdigest()
    if ck in CACHE: return CACHE[ck]
    try:
        data = urllib.parse.urlencode({
            'q': text, 'source': source_lang, 'target': target_lang,
            'key': GOOGLE_API_KEY, 'format': 'text'
        }).encode()
        req = urllib.request.Request(
            'https://translation.googleapis.com/language/translate/v2',
            data=data, method='POST')
        req.add_header('Content-Type', 'application/x-www-form-urlencoded')
        with urllib.request.urlopen(req, timeout=6) as r:
            res = json.loads(r.read().decode())
            t = res['data']['translations'][0]['translatedText']
            t = _sanitize(t)
            CACHE[ck] = t
            return t
    except Exception as e:
        print(f"Translate error: {e}")
        return text

def translate_ui(lang):
    if lang == 'pt': return UI_PT
    ck = f'ui_{lang}'
    if ck in CACHE: return CACHE[ck]
    result = {k: _google(v, lang, 'pt') for k, v in UI_PT.items()}
    CACHE[ck] = result
    return result

def _fix_years(text, lang):
    """Remove 'old' from year translations."""
    if not text: return text
    bad = [' years old', ' year old', ' anos de idade', ' Jahre alt',
           ' ans de vieux', ' anni di vita', ' años de edad']
    for b in bad:
        text = text.replace(b, text.split(b)[0].split()[-1] + ' years' if lang=='en' else text.replace(b,''))
    # simpler fix
    for b in [' years old',' year old',' anos de idade',' Jahre alt',' ans de vieux',' anni di vita',' años de edad']:
        if b in text:
            text = text.replace(b, ' years' if lang=='en' else
                                   ' anos' if lang=='pt' else
                                   ' Jahre' if lang=='de' else
                                   ' ans' if lang=='fr' else
                                   ' anni' if lang=='it' else
                                   ' años' if lang=='es' else '')
    return text

def translate_opp(opp, target_lang):
    """Traduz todos os campos da oportunidade para target_lang."""
    if not opp: return opp
    source_lang = opp.get('content_lang', 'pt')
    o = dict(opp)

    # Guardar originais PT (estado e sector estão SEMPRE em PT na BD)
    o['sector_pt'] = opp.get('sector', '')
    o['estado_pt'] = opp.get('estado', 'Disponivel')

    if target_lang == source_lang and target_lang == 'pt':
        o['direct_label'] = 'diretos'
        o['fase_t'] = opp.get('fase', '')
        return o

    # Traduzir todos os campos de texto
    o['titulo']    = _google(opp.get('titulo',''), target_lang, source_lang)
    o['descricao'] = _google(opp.get('descricao',''), target_lang, source_lang)

    # Sector e estado SEMPRE de PT
    o['sector']    = _google(opp.get('sector',''), target_lang, 'pt')
    o['estado']    = _google(opp.get('estado','Disponível'), target_lang, 'pt')

    # Fase — traduzir de PT (está sempre em PT)
    o['fase_t']    = _google(opp.get('fase',''), target_lang, 'pt')

    # Retorno e horizonte — do idioma original
    raw_ret = opp.get('retorno','')
    raw_hor = opp.get('horizonte','')
    o['retorno']   = _fix_years(_google(raw_ret, target_lang, source_lang), target_lang) if raw_ret else ''
    o['horizonte'] = _fix_years(_google(raw_hor, target_lang, source_lang), target_lang) if raw_hor else ''

    # Labels auxiliares
    o['direct_label'] = _google('diretos', target_lang, 'pt')

    return o
