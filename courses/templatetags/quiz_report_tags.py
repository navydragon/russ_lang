from django import template
from django.template.loader import get_template, render_to_string
from django.template import TemplateDoesNotExist
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from courses.quiz_report import detect_format, parse_quiz_report

register = template.Library()

QUESTION_TEMPLATE_PREFIX = 'quiz_report/questions/'


@register.simple_tag
def render_attempt_results(results_text: str) -> str:
    if not results_text:
        return ''

    fmt = detect_format(results_text)
    if fmt == 'html':
        return mark_safe(results_text)
    if fmt == 'plain':
        return format_html(
            '<pre class="quiz-report-raw">{}</pre>', results_text,
        )

    report = parse_quiz_report(results_text)
    if report is None:
        return format_html(
            '<pre class="quiz-report-raw">{}</pre>', results_text,
        )

    return render_to_string('quiz_report/report.html', {'report': report})


@register.inclusion_tag('quiz_report/_question_body.html', takes_context=False)
def render_question(question):
    template_name = f'{QUESTION_TEMPLATE_PREFIX}{question.type}.html'
    try:
        get_template(template_name)
    except TemplateDoesNotExist:
        template_name = f'{QUESTION_TEMPLATE_PREFIX}unknown.html'
    return {'question': question, 'template_name': template_name}
