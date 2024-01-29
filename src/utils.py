import logging
from requests import Session, Response
from requests import RequestException
from typing import Optional

from exceptions import ParserFindTagException
from constants import CSV_ENCODING


def get_response(session: Session, url: str) -> Optional[Response]:
    try:
        response = session.get(url)
        response.encoding = CSV_ENCODING
        return response
    except RequestException:
        logging.exception(
            f'Возникла ошибка при загрузке страницы {url}', stack_info=True
        )


def find_tag(soup, tag, attrs=None):
    searched_tag = soup.find(tag, attrs=(attrs or {}))
    if searched_tag is None:
        error_msg = f'Не найден тег {tag} {attrs}'
        logging.error(error_msg, stack_info=True)
        raise ParserFindTagException(error_msg)
    return searched_tag
