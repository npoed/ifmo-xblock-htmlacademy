from django.test import TestCase
import hashlib
from xblock_htmlacademy.xblock_academy_core import HTMLAcademyXBlock
import mock
from xblock.field_data import DictFieldData
from datetime import datetime
import pytz


def fake_block(**kw):
    runtime = mock.Mock()
    scope_ids = mock.Mock()
    data = DictFieldData(kw)
    return HTMLAcademyXBlock(runtime, data, scope_ids)


class Md5TestCase(TestCase):
    def test_md5(self):
        input_value = "so much wow"
        md5 = hashlib.md5()
        md5.update(input_value)
        self.assertEqual(HTMLAcademyXBlock._md5(input_value), md5.hexdigest())


class NowTestCase(TestCase):
    @mock.patch('xblock_htmlacademy.xblock_academy_core.datetime.datetime', autospec=True)
    def test_now(self, date_mock):
        block = fake_block()
        now = datetime.utcnow()
        date_mock.utcnow = lambda: now
        self.assertEqual(now.replace(tzinfo=pytz.utc), block._now())


class GetPointsTestCase(TestCase):
    def test_with_empty_history(self):
        block = fake_block(history='[]')
        self.assertEqual(block._get_points(), 0)

    def test_with_existing_history(self):
        block = fake_block(history='[{"date": 2}, {"date": 3}]')
        self.assertEqual(block._get_points(), 3)

    def test_with_input_history(self):
        block = fake_block()
        self.assertEqual(block._get_points('[{"date": 2}, {"date": 3}]'), 3)


class GetScoreTestCase(TestCase):
    def test_get_score(self):
        block = fake_block(history='[{"date": 0.1}, {"date": 0.5}]', weight=3)
        score = block.get_score()
        self.assertEqual(score['score'], 1.5)
        self.assertEqual(score['total'], 3)


class MaxScoreTestCase(TestCase):
    def test_max_score(self):
        block = fake_block(weight=10)
        self.assertEqual(block.max_score(), 10)



