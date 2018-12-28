import os.path
import pygments
import urllib.parse
from datetime import timedelta
from jinja2 import Markup
from pygments import highlight
from pygments.lexers import guess_lexer, guess_lexer_for_filename, TextLexer
from pygments.formatters import HtmlFormatter
from srht.markdown import markdown
from srht.rst import rst_to_html
from scmsrht.redis import redis

def get_clone_urls(origin_url, ssh_username, owner, repo):
    """ Gets a standard list of clone URLs to show on a repository's
        summary page (read-only https, read/write ssh).
    """
    # Remove the scheme and port from the origin URL.
    parsed_origin_url = urllib.parse.urlparse(origin_url)
    base = parsed_origin_url.hostname

    clone_urls = [
        {'desc': "read-only", 'url': "https://{}/{}/{}", 'link': True},
        {'desc': "read/write", 'url': "ssh://%s@{}/{}/{}" % ssh_username},
    ]
    for curl in clone_urls:
        curl['url'] = curl['url'].format(base, owner.canonical_name, repo.name)
    return clone_urls

def get_readme_names():
    """ Gets a list of supported `README` file names. The first one that's
        found can be passed to `format_readme` below.
    """
    return [
        'README.md',
        'README.rst']

def format_readme(cache_prefix, content_hash, name, content_getter):
    """ Formats a `README` file for display on a repository's summary page.
    """
    key = f"{cache_prefix}:readme:{content_hash}:v4"
    html = redis.get(key)
    if html:
        return Markup(html.decode())

    try:
        raw = content_getter()
    except:
        raw = "Error decoding readme - is it valid UTF-8?"

    basename, ext = os.path.splitext(name)
    if ext == '.md':
        html = markdown(raw, ["h1", "h2", "h3", "h4", "h5"])
    elif ext == '.rst':
        html = rst_to_html(raw)
    else:
        # Unsupported/unknown markup type.
        html = raw

    redis.setex(key, timedelta(days=7), html)
    return Markup(html)

def _get_shebang(data):
    if not data.startswith('#!'):
        return None

    endline = data.find('\n')
    if endline == -1:
        shebang = data
    else:
        shebang = data[:endline]

    return shebang

def _get_lexer(name, data):
    try:
        return guess_lexer_for_filename(name, data)
    except pygments.util.ClassNotFound:
        try:
            shebang = _get_shebang(data)
            if not shebang:
                return TextLexer()

            return guess_lexer(shebang)
        except pygments.util.ClassNotFound:
            return TextLexer()

def highlight_file(cache_prefix, name, content_hash, content):
    """ Highlights a file for display in a repository's browsing UI.
    """
    key = f"{cache_prefix}:highlight:{content_hash}"
    html = redis.get(key)
    if html:
        return Markup(html.decode())

    lexer = _get_lexer(name, content)
    formatter = HtmlFormatter()
    style = formatter.get_style_defs('.highlight')
    html = f"<style>{style}</style>" + highlight(content, lexer, formatter)
    redis.setex(key, timedelta(days=7), html)
    return Markup(html)
