import os, sys

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

import requests
import lxml.html

from extract_store import ExtractStore


class Services(object):
    """http://www.services.gov.za/
    This assumes all translated paths will have the language code in their
    urls, this is for identification purposes. The website itself reads the
    language code from the cookie and ignores the code in the url.
    """
    base_url = 'http://www.services.gov.za/'
    languages = {
        'nd_ZA': 'isiNdebele',
        'xh_ZA': 'isiXhosa',
        'af_ZA': 'Afrikaans',
        'en_ZA': 'English',
        'zu_ZA': 'isiZulu',
        'st_ZA': 'Sesotho',
        'nso_ZA': 'Sesotho sa Leboa',
        'tn_ZA': 'Setswana',
        'ss_ZA': 'siSwati',
        've_ZA': 'Tshivenda',
        'ts_ZA': 'Xitsonga',
    }
    _last_response = None
    _crawled_urls = list()
    _pending_urls = list()
        
    def get_page(self, page_url, lang_code):
        cookies = dict(locale=lang_code)

        print page_url
        self._last_response = requests.get(page_url, cookies=cookies)
        self._crawled_urls.append(page_url)

        return self._last_response
        
    def append_urls(self, html_page, lang_code):
        page_tree = lxml.html.fromstring(html_page)
        page_tree.make_links_absolute(self.base_url)

        for node in page_tree.xpath('//a'):
            if 'href' not in node.attrib:
                continue
            url = node.attrib['href']
            # crawls urls with language code
            if '/{0}'.format(lang_code) not in url or \
                    url in self._crawled_urls + self._pending_urls:
                continue
            self._pending_urls.append(url)

        return self._pending_urls

    def _crawl_pages(self, url, lang_code):
        response = services.get_page(url, lang_code)
        
        extract_store = ExtractStore(response.text, lang_code)
        
        urls = services.append_urls(response.text,  lang_code)
        
        print len(self._pending_urls)
        print len(self._crawled_urls)
        print len(set(self._pending_urls))
        print len(set(self._crawled_urls))

        if url in self._pending_urls:
            self._pending_urls.remove(url)

        for url in self._pending_urls:
            if url in self._crawled_urls:
                continue
            self._crawl_pages(url, lang_code)



if __name__ == "__main__":

    services = Services()

    for lang_code, label in services.languages.items():
        response = services._crawl_pages(
            'http://www.services.gov.za/services/content/Home/',
            lang_code
        )
