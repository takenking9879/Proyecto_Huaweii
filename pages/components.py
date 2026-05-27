from dash import html, dcc

_SECTION_ITEMS = {
    'diagnostico': [
        ('01  Tendencias',  '/slide_1'),
        ('02  Geografía',   '/slide_2'),
        ('03  Categorías',  '/slide_3'),
    ],
    'evidencia': [
        ('04  Percepción',       '/slide_7'),
        ('05  Economía Digital', '/slide_economia'),
        ('06  Ciberseguridad',   '/slide_ciberseguridad'),
    ],
    'estrategia': [
        ('07  Oportunidad',      '/slide_inversion'),
        ('08  Tu Estado',        '/slide_perfil_estado'),
    ],
}

_SECTION_META = {
    'diagnostico': {'label': 'DIAGNÓSTICO', 'core': '#00b4cc', 'bright': '#33d4ee'},
    'evidencia':   {'label': 'EVIDENCIA',   'core': '#c9922a', 'bright': '#f0b84a'},
    'estrategia':  {'label': 'ESTRATEGIA',  'core': '#00b87a', 'bright': '#00d98f'},
}

_PATH_TO_SECTION = {
    '/slide_1': 'diagnostico', '/slide_2': 'diagnostico',
    '/slide_3': 'diagnostico',
    '/slide_7': 'evidencia',      '/slide_economia': 'evidencia',
    '/slide_ciberseguridad': 'evidencia',
    '/slide_inversion': 'estrategia', '/slide_perfil_estado': 'estrategia',
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
