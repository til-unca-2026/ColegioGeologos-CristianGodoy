from html.parser import HTMLParser
import re


class HTMLSanitizer(HTMLParser):
    """
    Parser HTML estricto basado únicamente en la librería estándar de Python.
    Permite solo una lista blanca de etiquetas y atributos seguros para editores ricos (Quill),
    eliminando etiquetas peligrosas (<script>, <style>, <iframe>, <object>, etc.) y
    atributos maliciosos (event handlers on* como onclick, onerror, y esquemas javascript:).
    """

    ALLOWED_TAGS = {
        "p", "br", "strong", "b", "em", "i", "u", "s", "strike",
        "h1", "h2", "h3", "h4", "h5", "h6",
        "ul", "ol", "li", "blockquote", "pre", "code",
        "a", "span", "div", "sub", "sup", "hr",
    }

    ALLOWED_ATTRIBUTES = {
        "a": {"href", "title", "target", "rel"},
        "span": {"class"},
        "p": {"class"},
        "div": {"class"},
        "code": {"class"},
        "pre": {"class"},
        "blockquote": {"class"},
    }

    DISALLOWED_CONTENTS = {"script", "style", "iframe", "object", "embed", "applet"}

    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.result = []
        self.ignored_stack = []

    def handle_starttag(self, tag, attrs):
        tag_lower = tag.lower()
        if tag_lower in self.DISALLOWED_CONTENTS:
            self.ignored_stack.append(tag_lower)
            return

        if self.ignored_stack:
            return

        if tag_lower in self.ALLOWED_TAGS:
            cleaned_attrs = []
            allowed_for_tag = self.ALLOWED_ATTRIBUTES.get(tag_lower, set())

            for attr, val in attrs:
                attr_lower = attr.lower()
                # Bloquear cualquier manejador on* (onclick, onerror, onload, etc.)
                if attr_lower.startswith("on"):
                    continue

                if attr_lower in allowed_for_tag:
                    val_str = str(val or "")
                    # Prevenir ejecución de pseudo-protocolos peligrosos en enlaces
                    if attr_lower == "href":
                        stripped = re.sub(r"\s+", "", val_str).lower()
                        if stripped.startswith(("javascript:", "data:", "vbscript:")):
                            continue

                    cleaned_attrs.append(f'{attr_lower}="{self._escape_attr(val_str)}"')

            # Si es enlace externo o abre en nueva pestaña, forzar rel="noopener noreferrer"
            if tag_lower == "a":
                has_rel = any(a.startswith("rel=") for a in cleaned_attrs)
                if not has_rel:
                    cleaned_attrs.append('rel="noopener noreferrer"')

            attr_string = f" {' '.join(cleaned_attrs)}" if cleaned_attrs else ""
            self.result.append(f"<{tag_lower}{attr_string}>")

    def handle_endtag(self, tag):
        tag_lower = tag.lower()
        if self.ignored_stack:
            if self.ignored_stack[-1] == tag_lower:
                self.ignored_stack.pop()
            return

        if tag_lower in self.ALLOWED_TAGS:
            if tag_lower not in {"br", "hr"}:
                self.result.append(f"</{tag_lower}>")

    def handle_data(self, data):
        if not self.ignored_stack:
            self.result.append(data)

    def handle_entityref(self, name):
        if not self.ignored_stack:
            self.result.append(f"&{name};")

    def handle_charref(self, name):
        if not self.ignored_stack:
            self.result.append(f"&#{name};")

    def _escape_attr(self, val):
        return val.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;").replace(">", "&gt;")

    def get_clean_html(self):
        return "".join(self.result)


def sanitize_html(html_content):
    """
    Función de utilidad pública para limpiar el contenido HTML de forma segura.
    """
    if not html_content or not isinstance(html_content, str):
        return ""
    parser = HTMLSanitizer()
    parser.feed(html_content)
    return parser.get_clean_html()

