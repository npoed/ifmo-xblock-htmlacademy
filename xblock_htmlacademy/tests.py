from django.test import TestCase
import hashlib
from xblock_htmlacademy.xblock_academy_core import HTMLAcademyXBlock


class Md5TestCase(TestCase):
    def test_md5(self):
        input_value = "so much wow"
        md5 = hashlib.md5()
        md5.update(input_value)
        self.assertEqual(HTMLAcademyXBlock._md5(input_value), md5.hexdigest())


#class CurrentTimeTestCase(TestCase):
