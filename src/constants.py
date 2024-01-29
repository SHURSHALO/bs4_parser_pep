from pathlib import Path
import re


class HTMLTag:
    DIV = 'div'
    LI = 'li'
    H1 = 'h1'
    DL = 'dl'
    UL = 'ul'
    A = 'a'
    ABBR = 'abbr'
    SECTION = 'section'
    TABLE = 'table'


class RegexPatterns:
    # Регулярное выражение для поиска ссылки на PDF файл с размером A4.
    PDF_A4_LINK = re.compile(r'.+pdf-a4\.zip$')

    # Регулярное выражение для извлечения версии и статуса Python.
    PYTHON_VERSION_STATUS = r'Python (?P<version>\d\.\d+) \((?P<status>.*)\)'


BASE_DIR = Path(__file__).parent
MAIN_DOC_URL = 'https://docs.python.org/3/'
PEP_DOC_URL = 'https://peps.python.org/'

EXPECTED_STATUS = {
    'A': ('Active', 'Accepted'),
    'D': ('Deferred',),
    'F': ('Final',),
    'P': ('Provisional',),
    'R': ('Rejected',),
    'S': ('Superseded',),
    'W': ('Withdrawn',),
    '': ('Draft', 'Active'),
}

LOG_FORMAT = '"%(asctime)s - [%(levelname)s] - %(message)s"'

DT_FORMAT = '%d.%m.%Y %H:%M:%S'
DATETIME_FORMAT = '%Y-%m-%d_%H-%M-%S'

PRETTY_OUTPUT = 'pretty'
FILE_OUTPUT = 'file'

DOWNLOAD_DIR_PATH = 'downloads'

CSV_ENCODING = 'utf-8'
