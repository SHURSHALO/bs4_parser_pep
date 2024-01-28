import logging
import re
from urllib.parse import urljoin

import requests_cache
from bs4 import BeautifulSoup
from tqdm import tqdm

from constants import BASE_DIR, MAIN_DOC_URL, PEP_DOC_URL, EXPECTED_STATUS
from configs import configure_argument_parser, configure_logging
from outputs import control_output
from utils import get_response, find_tag


def whats_new(session):

    whats_new_url = urljoin(MAIN_DOC_URL, 'whatsnew/')

    if __name__ == '__main__':

        response = get_response(session, whats_new_url)
        if response is None:

            return

        soup = BeautifulSoup(response.text, features='lxml')

        main_div = find_tag(
            soup, 'section', attrs={'id': 'what-s-new-in-python'}
        )

        div_with_ul = find_tag(
            main_div, 'div', attrs={'class': 'toctree-wrapper'}
        )

        sections_by_python = div_with_ul.find_all(
            'li', attrs={'class': 'toctree-l1'}
        )

        results = [('Ссылка на статью', 'Заголовок', 'Редактор, автор')]
        for section in tqdm(sections_by_python):
            version_a_tag = section.find('a')
            version_link = urljoin(whats_new_url, version_a_tag['href'])
            response = get_response(session, version_link)
            if response is None:

                continue
            soup = BeautifulSoup(response.text, 'lxml')
            h1 = find_tag(soup, 'h1')
            dl = find_tag(soup, 'dl')
            dl_text = dl.text.replace('\n', ' ')
            results.append((version_link, h1.text, dl_text))

        return results


def latest_versions(session):
    MAIN_DOC_URL = 'https://docs.python.org/3/'

    if __name__ == '__main__':

        response = get_response(session, MAIN_DOC_URL)
        if response is None:
            return
        soup = BeautifulSoup(response.text, 'lxml')
        sidebar = find_tag(
            soup, 'div', attrs={'class': 'sphinxsidebarwrapper'}
        )

        ul_tags = sidebar.find_all('ul')
        for ul in ul_tags:
            if 'All versions' in ul.text:
                a_tags = ul.find_all('a')
                break
        else:
            raise Exception('Не найден список c версиями Python')

        results = [('Ссылка на статью', 'Заголовок', 'Редактор, автор')]
        pattern = r'Python (?P<version>\d\.\d+) \((?P<status>.*)\)'

        for a_tag in a_tags:

            link = a_tag['href']

            text_match = re.search(pattern, a_tag.text)
            if text_match is not None:

                version, status = text_match.groups()
            else:

                version, status = a_tag.text, ''

            results.append((link, version, status))

        return results


def download(session):

    downloads_url = urljoin(MAIN_DOC_URL, 'download.html')

    if __name__ == '__main__':

        response = get_response(session, downloads_url)
        if response is None:
            return

        soup = BeautifulSoup(response.text, features='lxml')

        table_tag = find_tag(soup, 'table', attrs={'class': 'docutils'})

        pdf_a4_tag = find_tag(
            table_tag, 'a', attrs={'href': re.compile(r'.+pdf-a4\.zip$')}
        )

        pdf_a4_link = pdf_a4_tag['href']

        archive_url = urljoin(downloads_url, pdf_a4_link)
        filename = archive_url.split('/')[-1]

        downloads_dir = BASE_DIR / 'downloads'

        downloads_dir.mkdir(exist_ok=True)

        archive_path = downloads_dir / filename

        response = session.get(archive_url)

        with open(archive_path, 'wb') as file:

            file.write(response.content)

        logging.info(f'Архив был загружен и сохранён: {archive_path}')


def pep(session):

    response = get_response(session, PEP_DOC_URL)
    if response is None:
        return

    soup = BeautifulSoup(response.text, features='lxml')
    section = soup.find('section', attrs={'id': 'index-by-category'})

    table = section.find_all('table')

    pep_div = section.find_all('a', attrs={'class': 'pep reference internal'})
    links_with_numbers = [
        link for link in pep_div if link.text.strip().isdigit()
    ]

    expected_status = []
    for abbr in table:
        pop = abbr.find_all('abbr')
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
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'lxml')

        abbr = soup.find('abbr')
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


def main():

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
