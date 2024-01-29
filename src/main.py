import logging
import re
from urllib.parse import urljoin

import requests_cache
from bs4 import BeautifulSoup
from tqdm import tqdm
from typing import Tuple, Optional, List, Any

from constants import (
    BASE_DIR,
    MAIN_DOC_URL,
    PEP_DOC_URL,
    EXPECTED_STATUS,
    DOWNLOAD_DIR_PATH,
    HTMLTag,
    RegexPatterns,
    CSV_ENCODING,
)
from configs import configure_argument_parser, configure_logging
from outputs import control_output
from utils import get_response, find_tag


def get_response_and_soup(
    session: Any, url: str, features: str = 'lxml'
) -> Tuple[Any, Any]:
    response = get_response(session, url)
    if response is None:
        return None, None
    soup = BeautifulSoup(response.text, features)
    return response, soup


def whats_new(session: Any) -> Optional[List[Tuple[str, str, str]]]:
    whats_new_url = urljoin(MAIN_DOC_URL, 'whatsnew/')
    response, soup = get_response_and_soup(session, whats_new_url)
    if response is None:
        return
    div_with_ul = find_tag(
        soup, HTMLTag.DIV, attrs={'class': 'toctree-wrapper'}
    )
    sections_by_python = div_with_ul.find_all(
        HTMLTag.LI, attrs={'class': 'toctree-l1'}
    )
    results = [('Ссылка на статью', 'Заголовок', 'Редактор, Автор')]
    for section in tqdm(sections_by_python):
        version_a_tag = find_tag(section, HTMLTag.A)
        href = version_a_tag['href']
        version_link = urljoin(whats_new_url, href)
        response, soup = get_response_and_soup(session, version_link)
        if response is None:
            continue
        h1 = find_tag(soup, HTMLTag.H1)
        dl = find_tag(soup, HTMLTag.DL)
        dl_text = dl.text.replace('\n', ' ')
        results.append((version_link, h1.text, dl_text))
    return results


def latest_versions(session: Any) -> List[Tuple[str, str, str]]:

    response, soup = get_response_and_soup(session, MAIN_DOC_URL)
    if response is None:
        return
    sidebar = find_tag(
        soup, HTMLTag.DIV, attrs={'class': 'sphinxsidebarwrapper'}
    )

    ul_tags = sidebar.find_all(HTMLTag.UL)
    for ul in ul_tags:
        if 'All versions' in ul.text:
            a_tags = ul.find_all(HTMLTag.A)
            break
    else:
        raise Exception('Не найден список c версиями Python')

    results = [('Ссылка на статью', 'Заголовок', 'Редактор, автор')]
    pattern = RegexPatterns.PYTHON_VERSION_STATUS

    for a_tag in a_tags:

        link = a_tag['href']

        text_match = re.search(pattern, a_tag.text)
        if text_match is not None:

            version, status = text_match.groups()
        else:

            version, status = a_tag.text, ''

        results.append((link, version, status))

    return results


def download(session: Any) -> None:
    downloads_url = urljoin(MAIN_DOC_URL, 'download.html')
    response, soup = get_response_and_soup(session, downloads_url)
    if response is None:
        return
    pdf_a4_tag = find_tag(
        soup, HTMLTag.A, attrs={'href': RegexPatterns.PDF_A4_LINK}
    )
    pdf_a4_link = pdf_a4_tag['href']
    archive_url = urljoin(downloads_url, pdf_a4_link)
    filename = archive_url.split('/')[-1]
    downloads_dir = BASE_DIR / DOWNLOAD_DIR_PATH
    downloads_dir.mkdir(exist_ok=True)
    archive_path = downloads_dir / filename
    response = session.get(archive_url)
    with open(archive_path, 'wb') as file:
        file.write(response.content)
    logging.info(f'Архив был загружен и сохранён: {archive_path}')


def pep(session: Any) -> List[Tuple[str, int]]:

    response = get_response(session, PEP_DOC_URL)
    if response is None:
        return

    soup = BeautifulSoup(response.text, features='lxml')
    section = find_tag(
        soup, HTMLTag.SECTION, attrs={'id': 'index-by-category'}
    )

    table = section.find_all(HTMLTag.TABLE)

    pep_div = section.find_all(
        HTMLTag.A, attrs={'class': 'pep reference internal'}
    )
    links_with_numbers = [
        link for link in pep_div if link.text.strip().isdigit()
    ]

    expected_status = []
    for abbr in table:
        pop = abbr.find_all(HTMLTag.ABBR)
        for tag in pop:
            preview_status = tag.text[1:]
            if preview_status in EXPECTED_STATUS:
                expected_status.append(EXPECTED_STATUS[preview_status])
            else:
                expected_status.append(EXPECTED_STATUS[''])

    list_status_table = []
    results = [('Статус', 'Количество')]
    list_status = []
    i = 0
    for pep in tqdm(links_with_numbers):

        version_link = urljoin(PEP_DOC_URL, pep['href'])

        response = session.get(version_link)
        response.encoding = CSV_ENCODING
        soup = BeautifulSoup(response.text, 'lxml')

        abbr = soup.find(HTMLTag.ABBR)
        text = abbr.text
        list_status.append(text)

        if text not in list_status_table:
            list_status_table.append(text)

        if text not in expected_status[i]:
            logging.info(
                f'\nНесовпадающие статусы:\n {version_link}\n '
                f'Статус в карточке: {text}\n '
                f'Ожидаемые статусы: {expected_status[i]}'
            )

        i += 1

    total = len(list_status)
    for tag in list_status_table:
        num = list_status.count(tag)
        results.append((tag, num))
    results.append(('Total', total))

    return results


MODE_TO_FUNCTION = {
    'whats-new': whats_new,
    'latest-versions': latest_versions,
    'download': download,
    'pep': pep,
}


def main() -> None:

    configure_logging()

    logging.info('Парсер запущен!')

    arg_parser = configure_argument_parser(MODE_TO_FUNCTION.keys())
    args = arg_parser.parse_args()

    logging.info(f'Аргументы командной строки: {args}')

    session = requests_cache.CachedSession()
    if args.clear_cache:
        session.cache.clear()

    parser_mode = args.mode
    results = MODE_TO_FUNCTION[parser_mode](session)

    if results is not None:
        control_output(results, args)

    logging.info('Парсер завершил работу.')


if __name__ == '__main__':
    main()
