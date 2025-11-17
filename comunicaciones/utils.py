import re
import logging
from urllib.parse import urlparse, parse_qs
from bs4 import BeautifulSoup, MarkupResemblesLocatorWarning
import warnings

# Configurar logging
logger = logging.getLogger(__name__)

# Suprimir warnings de BeautifulSoup sobre URLs
warnings.filterwarnings("ignore", category=MarkupResemblesLocatorWarning)


# ============================================
# CONVERSIÓN DE URLs A EMBEDS
# ============================================

def convertir_url_a_embed(contenido):
    """
    Detecta si el contenido es una URL simple y la convierte a código embed.
    Si ya es código HTML, lo devuelve sin cambios.
    """
    if not contenido or not contenido.strip():
        return contenido
    
    contenido = contenido.strip()
    
    # Si ya contiene tags HTML (iframe, script, etc), no hacer nada
    if '<iframe' in contenido or '<script' in contenido or '<blockquote' in contenido:
        return contenido
    
    # Si empieza con http/https, probablemente es una URL
    if contenido.startswith('http://') or contenido.startswith('https://'):
        # Intentar convertir según el dominio
        if 'canva.com' in contenido:
            return convertir_canva_url(contenido)
        elif 'youtube.com' in contenido or 'youtu.be' in contenido:
            return convertir_youtube_url(contenido)
        elif 'vimeo.com' in contenido:
            return convertir_vimeo_url(contenido)
        elif 'docs.google.com/presentation' in contenido:
            return convertir_google_slides_url(contenido)
        elif 'drive.google.com' in contenido:
            return convertir_google_drive_url(contenido)
        elif 'instagram.com' in contenido:
            return convertir_instagram_url(contenido)
        elif 'twitter.com' in contenido or 'x.com' in contenido:
            return convertir_twitter_url(contenido)
        else:
            # URL no soportada - crear iframe genérico CON ADVERTENCIA
            logger.warning(f"⚠️ URL no soportada para conversión automática: {contenido}")
            
            # Intentar crear iframe genérico pero avisar que puede fallar
            embed_code = f'''<!-- ADVERTENCIA: Esta URL podría no permitir embeds -->
<div style="padding: 1rem; background: #fff3cd; border: 1px solid #ffc107; border-radius: 8px; margin: 1rem 0;">
    <p style="margin: 0; color: #856404;">
        <strong>⚠️ Plataforma no soportada:</strong> Esta URL podría no permitir embeds.
    </p>
    <p style="margin: 0.5rem 0 0 0; font-size: 0.9rem; color: #856404;">
        URL: <a href="{contenido}" target="_blank">{contenido}</a>
    </p>
</div>
<iframe src="{contenido}" width="100%" height="500" frameborder="0" allowfullscreen></iframe>'''
            
            return embed_code
    
    # Si no es ni HTML ni URL reconocida, devolver sin cambios
    return contenido


def convertir_canva_url(url):
    """Convierte una URL de Canva en código embed."""
    try:
        # Extraer el ID del diseño
        match = re.search(r'/design/([^/]+)', url)
        if not match:
            logger.warning(f"No se pudo extraer ID de Canva de: {url}")
            return f'<!-- Error: URL de Canva inválida -->\n{url}'
        
        design_id = match.group(1)
        embed_url = f"https://www.canva.com/design/{design_id}/view?embed"
        
        logger.info(f"✅ Convertida URL de Canva: {design_id}")
        
        embed_code = f'''<div style="position: relative; width: 100%; height: 0; padding-top: 56.2500%; padding-bottom: 0; box-shadow: 0 2px 8px 0 rgba(63,69,81,0.16); overflow: hidden; border-radius: 8px; will-change: transform;">
  <iframe loading="lazy" style="position: absolute; width: 100%; height: 100%; top: 0; left: 0; border: none; padding: 0; margin: 0;"
    src="{embed_url}" allowfullscreen="allowfullscreen" allow="fullscreen">
  </iframe>
</div>'''
        
        return embed_code
        
    except Exception as e:
        logger.error(f"Error al convertir URL de Canva: {str(e)}")
        return f'<!-- Error al convertir URL de Canva: {str(e)} -->\n{url}'


def convertir_youtube_url(url):
    """Convierte una URL de YouTube en código embed."""
    try:
        video_id = None
        
        # Caso 1: youtube.com/watch?v=VIDEO_ID
        if 'youtube.com/watch' in url:
            parsed = urlparse(url)
            query_params = parse_qs(parsed.query)
            video_id = query_params.get('v', [None])[0]
        
        # Caso 2: youtu.be/VIDEO_ID
        elif 'youtu.be/' in url:
            video_id = url.split('youtu.be/')[-1].split('?')[0].split('/')[0]
        
        # Caso 3: youtube.com/embed/VIDEO_ID (ya es embed, extraer ID)
        elif 'youtube.com/embed/' in url:
            video_id = url.split('embed/')[-1].split('?')[0].split('/')[0]
        
        # Caso 4: youtube.com/v/VIDEO_ID
        elif 'youtube.com/v/' in url:
            video_id = url.split('v/')[-1].split('?')[0].split('/')[0]
        
        if not video_id:
            logger.warning(f"No se pudo extraer ID de YouTube de: {url}")
            return f'<!-- Error: No se pudo extraer ID de YouTube -->\n{url}'
        
        # URL correcta para embed (con nocookie para mejor privacidad)
        embed_url = f"https://www.youtube-nocookie.com/embed/{video_id}"
        logger.info(f"✅ Convertida URL de YouTube: {video_id}")
        
        # Código embed optimizado con aspect ratio responsive
        embed_code = f'''<div style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden;">
  <iframe style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;" 
    src="{embed_url}" 
    title="YouTube video player" 
    frameborder="0" 
    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" 
    allowfullscreen>
  </iframe>
</div>'''
        
        return embed_code
        
    except Exception as e:
        logger.error(f"Error al convertir URL de YouTube: {str(e)}")
        return f'<!-- Error al convertir URL de YouTube: {str(e)} -->\n{url}'


def convertir_vimeo_url(url):
    """Convierte una URL de Vimeo en código embed."""
    try:
        match = re.search(r'vimeo\.com/(\d+)', url)
        if not match:
            return f'<!-- Error: URL de Vimeo inválida -->\n{url}'
        
        video_id = match.group(1)
        embed_url = f"https://player.vimeo.com/video/{video_id}"
        
        logger.info(f"✅ Convertida URL de Vimeo: {video_id}")
        
        embed_code = f'''<iframe src="{embed_url}" width="640" height="360" 
    frameborder="0" allow="autoplay; fullscreen; picture-in-picture" allowfullscreen>
</iframe>'''
        
        return embed_code
        
    except Exception as e:
        logger.error(f"Error al convertir URL de Vimeo: {str(e)}")
        return f'<!-- Error al convertir URL de Vimeo: {str(e)} -->\n{url}'


def convertir_google_slides_url(url):
    """Convierte una URL de Google Slides en código embed."""
    try:
        match = re.search(r'/presentation/d/([a-zA-Z0-9_-]+)', url)
        if not match:
            return f'<!-- Error: URL de Google Slides inválida -->\n{url}'
        
        presentation_id = match.group(1)
        embed_url = f"https://docs.google.com/presentation/d/{presentation_id}/embed?start=false&loop=false&delayms=3000"
        
        logger.info(f"✅ Convertida URL de Google Slides: {presentation_id}")
        
        # Usar aspect ratio 16:9 responsivo
        embed_code = f'''<div style="position: relative; width: 100%; padding-bottom: 56.25%; height: 0; overflow: hidden;">
  <iframe src="{embed_url}" 
    style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; border: none;"
    frameborder="0" 
    allowfullscreen="true" 
    mozallowfullscreen="true" 
    webkitallowfullscreen="true">
  </iframe>
</div>'''
        
        return embed_code
        
    except Exception as e:
        logger.error(f"Error al convertir URL de Google Slides: {str(e)}")
        return f'<!-- Error al convertir URL de Google Slides: {str(e)} -->\n{url}'


def convertir_google_drive_url(url):
    """Convierte una URL de Google Drive en código embed."""
    try:
        match = re.search(r'/file/d/([a-zA-Z0-9_-]+)', url) or re.search(r'id=([a-zA-Z0-9_-]+)', url)
        if not match:
            return f'<!-- Error: URL de Google Drive inválida -->\n{url}'
        
        file_id = match.group(1)
        embed_url = f"https://drive.google.com/file/d/{file_id}/preview"
        
        logger.info(f"✅ Convertida URL de Google Drive: {file_id}")
        
        embed_code = f'''<iframe src="{embed_url}" 
    width="640" height="480" allow="autoplay" allowfullscreen>
</iframe>'''
        
        return embed_code
        
    except Exception as e:
        logger.error(f"Error al convertir URL de Google Drive: {str(e)}")
        return f'<!-- Error al convertir URL de Google Drive: {str(e)} -->\n{url}'


def convertir_instagram_url(url):
    """Convierte una URL de Instagram en código embed."""
    try:
        if '/p/' not in url and '/reel/' not in url:
            return f'<!-- Error: URL de Instagram debe contener /p/ o /reel/ -->\n{url}'
        
        clean_url = url.rstrip('/')
        if not clean_url.endswith('/embed'):
            clean_url += '/embed'
        
        logger.info(f"✅ Convertida URL de Instagram")
        
        embed_code = f'''<blockquote class="instagram-media" data-instgrm-permalink="{url}" 
    data-instgrm-version="14" style="max-width:540px; min-width:326px; width:100%;">
</blockquote>
<script async src="//www.instagram.com/embed.js"></script>'''
        
        return embed_code
        
    except Exception as e:
        logger.error(f"Error al convertir URL de Instagram: {str(e)}")
        return f'<!-- Error al convertir URL de Instagram: {str(e)} -->\n{url}'


def convertir_twitter_url(url):
    """
    Convierte una URL de Twitter/X en código embed.
    Nota: Twitter requiere que el script se cargue para renderizar el tweet.
    """
    try:
        # Asegurar que la URL sea válida
        if '/status/' not in url:
            logger.warning(f"URL de Twitter sin /status/: {url}")
            return f'<!-- Error: URL de Twitter debe contener /status/ -->\n{url}'
        
        logger.info(f"✅ Convertida URL de Twitter/X")
        
        # Para Twitter, simplemente devolvemos la URL en un blockquote
        # El script de Twitter lo procesará automáticamente
        embed_code = f'''<blockquote class="twitter-tweet" data-dnt="true" data-theme="light">
    <a href="{url}"></a>
</blockquote>
<script async src="https://platform.twitter.com/widgets.js" charset="utf-8"></script>'''
        
        return embed_code
        
    except Exception as e:
        logger.error(f"Error al convertir URL de Twitter: {str(e)}")
        return f'<!-- Error al convertir URL de Twitter: {str(e)} -->\n{url}'


# ============================================
# LIMPIEZA DE CÓDIGO EMBED
# ============================================

def limpiar_embed_canva(html_code):
    """Limpia el código HTML de Canva para optimizar su visualización."""
    if not html_code:
        return html_code
    
    try:
        soup = BeautifulSoup(html_code, 'html.parser')
        
        # Encontrar el div contenedor con estilos inline
        container_div = soup.find('div', style=re.compile(r'position:\s*relative'))
        
        if container_div:
            style = container_div.get('style', '')
            # Eliminar márgenes excesivos
            style = re.sub(r'margin-top:\s*[\d.]+em;?', '', style)
            style = re.sub(r'margin-bottom:\s*[\d.]+em;?', '', style)
            container_div['style'] = style.strip()
        
        # Encontrar y eliminar enlaces de atribución
        attribution_links = soup.find_all('a', href=re.compile(r'canva\.com'))
        for link in attribution_links:
            if link.find_parent('iframe') is None:
                next_sibling = link.next_sibling
                link.decompose()
                if next_sibling and isinstance(next_sibling, str):
                    next_sibling.replace_with('')
        
        return str(soup)
        
    except Exception as e:
        logger.error(f"Error al limpiar embed de Canva: {e}")
        return html_code


def limpiar_embed_google_slides(html_code):
    """Limpia el código HTML de Google Slides."""
    if not html_code:
        return html_code
    
    try:
        soup = BeautifulSoup(html_code, 'html.parser')
        
        # Google Slides a veces incluye scripts innecesarios
        for script in soup.find_all('script'):
            script.decompose()
        
        return str(soup)
        
    except Exception as e:
        logger.error(f"Error al limpiar Google Slides: {e}")
        return html_code


def detectar_y_limpiar_embed(html_code):
    """
    Detecta el tipo de embed y aplica la limpieza correspondiente.
    También convierte URLs simples a código embed.
    """
    if not html_code:
        return html_code
    
    # PASO 1: Intentar convertir URL a embed si es necesario
    html_code = convertir_url_a_embed(html_code)
    
    # PASO 2: Limpiar el código embed según el tipo
    if 'canva.com' in html_code:
        return limpiar_embed_canva(html_code)
    elif 'docs.google.com/presentation' in html_code:
        return limpiar_embed_google_slides(html_code)
    else:
        return html_code


# ============================================
# VALIDACIÓN Y ANÁLISIS
# ============================================

def validar_embed_code(html_code):
    """
    Valida que el código embed sea seguro y válido.
    También convierte URLs simples a código embed.
    
    Returns:
        Tuple (is_valid: bool, cleaned_code: str, error_message: str)
    """
    if not html_code or not html_code.strip():
        return False, '', 'El código embed está vacío'
    
    html_code_original = html_code.strip()
    
    # PASO 1: Convertir URL a embed si es necesario
    html_code_convertido = convertir_url_a_embed(html_code_original)
    
    # Si cambió, es porque se convirtió de URL a embed
    if html_code_convertido != html_code_original:
        info = obtener_info_embed(html_code_original)
        logger.info(f"🔄 URL de {info.get('plataforma', 'desconocida')} convertida a código embed")
    
    # PASO 2: Ahora validar el código embed resultante
    html_code = html_code_convertido
    
    # Lista de dominios permitidos (ampliada)
    dominios_permitidos = [
        'youtube.com',
        'youtube-nocookie.com',  # Para embeds de YouTube
        'youtu.be',
        'vimeo.com',
        'player.vimeo.com',  # Para embeds de Vimeo
        'canva.com',
        'docs.google.com',
        'drive.google.com',
        'slides.com',
        'prezi.com',
        'slideshare.net',
        'instagram.com',
        'twitter.com',
        'x.com',
        'platform.twitter.com',  # Para script de Twitter
        'facebook.com',
        'tiktok.com',
    ]
    
    try:
        soup = BeautifulSoup(html_code, 'html.parser')
        
        # Buscar todos los iframes
        iframes = soup.find_all('iframe')
        
        if not iframes:
            # Puede ser embed de redes sociales (script)
            scripts = soup.find_all('script')
            if scripts:
                # Validar que los scripts sean de dominios permitidos
                for script in scripts:
                    src = script.get('src', '')
                    if src and not any(dominio in src for dominio in dominios_permitidos):
                        logger.warning(f"Dominio no permitido en script: {src}")
                        return False, '', f'Dominio no permitido en script: {src}'
                
                # Scripts válidos, limpiar y devolver
                cleaned_code = detectar_y_limpiar_embed(html_code)
                return True, cleaned_code, ''
            else:
                logger.warning("No se encontró iframe ni script en el código embed")
                return False, '', 'No se encontró ningún iframe o script válido'
        
        # Validar cada iframe
        for iframe in iframes:
            src = iframe.get('src', '')
            
            if not src:
                logger.warning("Iframe sin atributo src")
                return False, '', 'El iframe no tiene atributo src'
            
            # Verificar que el src sea de un dominio permitido
            if not any(dominio in src for dominio in dominios_permitidos):
                logger.warning(f"Dominio no permitido: {src}")
                return False, '', f'Dominio no permitido: {src}'
        
        # Si todo está bien, limpiar y devolver
        cleaned_code = detectar_y_limpiar_embed(html_code)
        return True, cleaned_code, ''
        
    except Exception as e:
        logger.error(f"Error al validar embed: {str(e)}")
        return False, '', f'Error al validar el código: {str(e)}'


def obtener_info_embed(contenido):
    """
    Analiza el contenido y devuelve información sobre el tipo de embed.
    
    Returns:
        dict con información
    """
    if not contenido or not contenido.strip():
        return {
            'tipo': None,
            'plataforma': None,
            'convertible': False,
            'mensaje': 'Contenido vacío'
        }
    
    contenido = contenido.strip()
    
    # Detectar si es código HTML
    if '<iframe' in contenido or '<script' in contenido or '<blockquote' in contenido:
        return {
            'tipo': 'embed',
            'plataforma': 'desconocida',
            'convertible': False,
            'mensaje': 'Ya es código embed'
        }
    
    # Detectar si es URL
    if contenido.startswith('http://') or contenido.startswith('https://'):
        plataformas = {
            'canva.com': 'Canva',
            'youtube.com': 'YouTube',
            'youtu.be': 'YouTube',
            'vimeo.com': 'Vimeo',
            'docs.google.com/presentation': 'Google Slides',
            'drive.google.com': 'Google Drive',
            'instagram.com': 'Instagram',
            'twitter.com': 'Twitter',
            'x.com': 'X (Twitter)',
        }
        
        for dominio, nombre in plataformas.items():
            if dominio in contenido:
                return {
                    'tipo': 'url',
                    'plataforma': nombre,
                    'convertible': True,
                    'mensaje': f'URL de {nombre} detectada - se convertirá automáticamente a embed'
                }
        
        return {
            'tipo': 'url',
            'plataforma': 'desconocida',
            'convertible': False,
            'mensaje': 'URL no soportada para conversión automática'
        }
    
    return {
        'tipo': 'texto',
        'plataforma': None,
        'convertible': False,
        'mensaje': 'No es una URL ni código embed válido'
    }