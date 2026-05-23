from dash import html, dcc

_SECTION_ITEMS = {
    'exploratorio': [
        ('01  Tendencias',  '/slide_1'),
        ('02  Geografía',   '/slide_2'),
        ('03  Categorías',  '/slide_3'),
        ('04  Comparativo', '/slide_4'),
    ],
    'profundo': [
        ('05  Crimen × PIB',        '/slide_5'),
        ('06  Crimen × IDDE',       '/slide_6'),
        ('07  ENVIPE',              '/slide_7'),
        ('11  Infra Digital × Seg', '/slide_11'),
    ],
    'modelos': [
        ('08  ENOE · Modelo',     '/slide_8'),
        ('09  DENUE · Modelo',    '/slide_9'),
        ('10  Innovación Digital', '/slide_10'),
    ],
}

_SECTION_META = {
    'exploratorio': {'label': 'EXPLORATORIO', 'core': '#00b4cc', 'bright': '#33d4ee'},
    'profundo':     {'label': 'PROFUNDO',      'core': '#c9922a', 'bright': '#f0b84a'},
    'modelos':      {'label': 'MODELOS',       'core': '#00b87a', 'bright': '#00d98f'},
}

_PATH_TO_SECTION = {
    '/slide_1': 'exploratorio', '/slide_2': 'exploratorio',
    '/slide_3': 'exploratorio', '/slide_4': 'exploratorio',
    '/slide_5': 'profundo',     '/slide_6': 'profundo',
    '/slide_7': 'profundo',     '/slide_11': 'profundo',
    '/slide_8': 'modelos',      '/slide_9': 'modelos',
    '/slide_10': 'modelos',
}


def sidebar(active_path='/'):
    section_key = _PATH_TO_SECTION.get(active_path)
    if not section_key:
        return html.Div()

    meta = _SECTION_META[section_key]
    core   = meta['core']
    bright = meta['bright']

    brand = html.Div([
        html.Div(style={
            'width': '28px', 'height': '3px',
            'background': f'linear-gradient(90deg,{core},{bright})',
            'borderRadius': '2px', 'marginBottom': '8px',
        }),
        html.Span('ANÁLISIS', style={
            'fontSize': '9px', 'fontWeight': '700',
            'letterSpacing': '0.16em', 'color': core,
            'display': 'block', 'lineHeight': '1',
        }),
        html.Span(meta['label'], style={
            'fontSize': '9px', 'fontWeight': '400',
            'letterSpacing': '0.10em', 'color': '#5c5c74',
            'display': 'block', 'lineHeight': '1.6',
        }),
    ], className='sidebar-brand')

    home_link = dcc.Link(
        '← Inicio',
        href='/',
        className='sidebar-item',
        style={'textDecoration': 'none', 'fontSize': '11px', 'opacity': '0.6'},
    )

    items = [brand, home_link]
    for label, href in _SECTION_ITEMS[section_key]:
        cls = 'sidebar-item active' if href == active_path else 'sidebar-item'
        items.append(dcc.Link(label, href=href, className=cls, style={'textDecoration': 'none'}))

    return html.Div(items, className=f'sidebar section-{section_key}')
