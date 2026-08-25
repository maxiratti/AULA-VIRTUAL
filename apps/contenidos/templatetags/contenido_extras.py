import re

from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe


register = template.Library()


def _inline_markdown(text):
    text = escape(text)

    text = re.sub(
        r"`([^`\n]+)`",
        r"<code>\1</code>",
        text,
    )
    text = re.sub(
        r"\*\*([^*\n]+)\*\*",
        r"<strong>\1</strong>",
        text,
    )
    text = re.sub(
        r"(?<!\*)\*([^*\n]+)\*(?!\*)",
        r"<em>\1</em>",
        text,
    )
    text = re.sub(
        r"\[([^\]\n]+)\]\((https?://[^\s)]+)\)",
        r'<a href="\2" target="_blank" rel="noopener noreferrer">\1</a>',
        text,
    )

    return text


@register.filter(name="markdown_seguro")
def markdown_seguro(value):
    """
    Markdown básico y seguro para contenidos educativos.
    El texto original se escapa antes de generar las etiquetas permitidas.
    """
    if not value:
        return ""

    lines = str(value).replace("\r\n", "\n").split("\n")
    html = []
    paragraph = []
    list_type = None
    in_code = False
    code_lines = []

    def flush_paragraph():
        nonlocal paragraph
        if paragraph:
            joined = "<br>".join(
                _inline_markdown(line)
                for line in paragraph
            )
            html.append(f"<p>{joined}</p>")
            paragraph = []

    def close_list():
        nonlocal list_type
        if list_type:
            html.append(f"</{list_type}>")
            list_type = None

    for raw_line in lines:
        line = raw_line.rstrip()

        if line.strip().startswith("```"):
            flush_paragraph()
            close_list()

            if in_code:
                html.append(
                    "<pre><code>"
                    + escape("\n".join(code_lines))
                    + "</code></pre>"
                )
                code_lines = []
                in_code = False
            else:
                in_code = True
            continue

        if in_code:
            code_lines.append(raw_line)
            continue

        stripped = line.strip()

        if not stripped:
            flush_paragraph()
            close_list()
            continue

        if re.fullmatch(r"(-{3,}|\*{3,}|_{3,})", stripped):
            flush_paragraph()
            close_list()
            html.append("<hr>")
            continue

        heading = re.match(r"^(#{1,4})\s+(.+)$", stripped)
        if heading:
            flush_paragraph()
            close_list()
            level = len(heading.group(1))
            html.append(
                f"<h{level}>"
                + _inline_markdown(heading.group(2))
                + f"</h{level}>"
            )
            continue

        unordered = re.match(r"^[-*+]\s+(.+)$", stripped)
        if unordered:
            flush_paragraph()
            if list_type != "ul":
                close_list()
                html.append("<ul>")
                list_type = "ul"
            html.append(
                "<li>"
                + _inline_markdown(unordered.group(1))
                + "</li>"
            )
            continue

        ordered = re.match(r"^\d+\.\s+(.+)$", stripped)
        if ordered:
            flush_paragraph()
            if list_type != "ol":
                close_list()
                html.append("<ol>")
                list_type = "ol"
            html.append(
                "<li>"
                + _inline_markdown(ordered.group(1))
                + "</li>"
            )
            continue

        close_list()
        paragraph.append(stripped)

    if in_code:
        html.append(
            "<pre><code>"
            + escape("\n".join(code_lines))
            + "</code></pre>"
        )

    flush_paragraph()
    close_list()

    return mark_safe("\n".join(html))
