from django.conf import settings
from django.template import Library, Node, NodeList, TemplateSyntaxError
from django.template.defaultfilters import stringfilter
from django.utils.safestring import SafeString, mark_safe

from pygments import highlight
from pygments.formatters.html import HtmlFormatter
from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.util import ClassNotFound


STYLE = getattr(settings, "PYGMENTO_STYLE", "default")
CSS_CLASS = getattr(settings, "PYGMENTO_CSS_CLASS", "highlight")

html_formatter = HtmlFormatter(style=STYLE, cssclass=CSS_CLASS)

register = Library()


def highlighter(code: str, lexer: str) -> SafeString:
    """
    Highlights given code using the lexer name passed
    """
    try:
        lexer_class = get_lexer_by_name(lexer)
    except ClassNotFound:
        # if lexer isn't found try to guess it based on the code
        lexer_class = guess_lexer(code)
    formatted_output = highlight(code, lexer_class, html_formatter)
    return mark_safe(formatted_output)


class PygmentoCSSNode(Node):
    """
    Renders the CSS based on the style
    """
    def render(self, context) -> SafeString:
        style = html_formatter.get_style_defs()
        return mark_safe(f"<style>{style}</style>")


class PygmentoBlockNode(Node):
    """
    Custom block node for handling multi-line code block
    """
    def __init__(self, nodelist: NodeList, lexer: str):
        self.lexer = lexer
        self.nodelist = nodelist

    def render(self, context) -> SafeString:
        code = self.nodelist.render(context)
        return highlighter(code, self.lexer)


@register.tag
def pygmento_css(*args) -> PygmentoCSSNode:
    """
    Template tag to add CSS
    """
    return PygmentoCSSNode()


@register.filter
@stringfilter
def pygmento(code: str, lexer: str) -> SafeString:
    """
    For single line code
    """
    return highlighter(code, lexer)


@register.tag
def pygmentoblock(parser, token) -> PygmentoBlockNode:
    """
    For multi-line code
    """
    try:
        lexer = token.split_contents()[1]
    except IndexError:
        raise TemplateSyntaxError("pygmentoblock takes lexer name as an argument")
    nodelist: NodeList = parser.parse(('endpygmentoblock',))
    parser.delete_first_token()
    return PygmentoBlockNode(nodelist, lexer)
