from django.template.loader import render_to_string
from django.test import SimpleTestCase

from courses.quiz_report import detect_format, parse_quiz_report
from courses.quiz_report.registry import QUESTION_PARSERS
from courses.services import parse_dr_summary
from courses.templatetags.quiz_report_tags import render_attempt_results
from courses.tests.fixtures import QUESTION_FIXTURES, SAMPLE_MULTIPLE_CHOICE_XML


class DetectFormatTests(SimpleTestCase):
    def test_detect_xml(self):
        self.assertEqual(detect_format(SAMPLE_MULTIPLE_CHOICE_XML), 'xml')

    def test_detect_html(self):
        self.assertEqual(detect_format('<table><tr><td>Score</td></tr></table>'), 'html')

    def test_detect_plain(self):
        self.assertEqual(detect_format('plain text result'), 'plain')

    def test_detect_empty(self):
        self.assertEqual(detect_format(''), 'plain')


class ParseQuizReportTests(SimpleTestCase):
    def test_parse_real_multiple_choice_xml(self):
        report = parse_quiz_report(SAMPLE_MULTIPLE_CHOICE_XML)
        self.assertIsNotNone(report)
        self.assertEqual(report.version, '2')
        self.assertEqual(report.summary.score, '10')
        self.assertEqual(report.summary.percent, '100')
        self.assertTrue(report.summary.passed)
        self.assertEqual(len(report.questions), 1)
        self.assertEqual(report.questions[0].type, 'multipleChoiceQuestion')
        self.assertEqual(report.questions[0].payload['user_answer_index'], 0)
        self.assertEqual(len(report.groups), 1)
        self.assertEqual(report.groups[0].name, 'Group 1')

    def test_all_registered_parsers_exist(self):
        expected = {
            'multipleChoiceQuestion',
            'trueFalseQuestion',
            'multipleResponseQuestion',
            'typeInQuestion',
            'fillInTheBlankQuestion',
            'multipleChoiceTextQuestion',
            'matchingQuestion',
            'sequenceQuestion',
            'wordBankQuestion',
            'essayQuestion',
            'numericQuestion',
            'hotspotQuestion',
            'likertScaleQuestion',
            'dndQuestion',
        }
        self.assertEqual(set(QUESTION_PARSERS.keys()), expected)

    def test_parse_each_question_type(self):
        for qtype, xml in QUESTION_FIXTURES.items():
            if qtype == 'unknownQuestion':
                continue
            report = parse_quiz_report(xml)
            self.assertIsNotNone(report, msg=f'Failed to parse {qtype}')
            self.assertEqual(len(report.questions), 1, msg=qtype)
            self.assertEqual(report.questions[0].type, qtype)

    def test_unknown_question_fallback(self):
        report = parse_quiz_report(QUESTION_FIXTURES['unknownQuestion'])
        self.assertIsNotNone(report)
        question = report.questions[0]
        self.assertEqual(question.type, 'unknown')
        self.assertEqual(question.payload['original_tag'], 'futureQuestion')
        self.assertIn('futureQuestion', question.raw_xml)

    def test_parse_dr_summary_compat(self):
        summary = parse_dr_summary(SAMPLE_MULTIPLE_CHOICE_XML)
        self.assertTrue(summary['passed'])
        self.assertEqual(summary['score'], '10')
        self.assertEqual(summary['percent'], '100')
        self.assertEqual(summary['finish_timestamp'], '8 июня 2026 г. 13:27')


class RenderQuizReportTests(SimpleTestCase):
    def test_render_multiple_choice(self):
        html = render_attempt_results(SAMPLE_MULTIPLE_CHOICE_XML)
        self.assertIn('Option 1', html)
        self.assertIn('Верно', html)
        self.assertIn('quiz-report', html)

    def test_render_html_fallback(self):
        html_content = '<table><tr><td>10 / 10 (100%)</td></tr></table>'
        html = render_attempt_results(html_content)
        self.assertIn('<table>', html)

    def test_render_plain_fallback(self):
        html = render_attempt_results('some plain text')
        self.assertIn('quiz-report-raw', html)
        self.assertIn('some plain text', html)

    def test_render_all_question_types(self):
        for qtype, xml in QUESTION_FIXTURES.items():
            html = render_attempt_results(xml)
            self.assertIn('quiz-report', html, msg=qtype)
            self.assertNotIn('<multipleChoiceQuestion', html, msg=qtype)

    def test_report_template_renders_groups(self):
        report = parse_quiz_report(SAMPLE_MULTIPLE_CHOICE_XML)
        html = render_to_string('quiz_report/report.html', {'report': report})
        self.assertIn('Group 1', html)
