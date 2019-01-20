import os.path
import pygments
from datetime import timedelta
from jinja2 import Markup
from pygments import highlight
from pygments.lexers import guess_lexer, guess_lexer_for_filename, TextLexer
from pygments.formatters import HtmlFormatter
from srht.markdown import markdown
from scmsrht.redis import redis

try:
    from srht.rst import rst_to_html
except ImportError:
    # No support for reStructuredText
    def rst_to_html(txt):
        return txt

def get_formatted_readme(cache_prefix, file_finder, content_getter):
    readme_names = ['README.md', 'README.rst']
    for name in readme_names:
        content_hash, user_obj = file_finder(name)
        if content_hash:
            return format_readme(cache_prefix, content_hash, name,
                        content_getter, user_obj)
    return None

def format_readme(cache_prefix, content_hash, name, content_getter, user_obj):
    """ Formats a `README` file for display on a repository's summary page.
    """
    key = f"{cache_prefix}:readme:{content_hash}:v4"
    html = redis.get(key)
    if html:
        return Markup(html.decode())

    try:
        raw = content_getter(user_obj)
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

def get_highlighted_file(cache_prefix, name, content_hash, content):
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
