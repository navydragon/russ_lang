import re

from django.core.exceptions import ValidationError

RUSSIAN_COURSE_WEBSOFT_ID = '7221015156608859696'


def validate_websoft_id(value):
    value = str(value)
    if not re.fullmatch(r'[1-9][0-9]{0,18}', value) or int(value) > 9223372036854775807:
        raise ValidationError('ID WebSoft должен быть положительным целым числом int64 без ведущих нулей.')
