import re
import requests
import lxml.html

from lxml.html.clean import Cleaner

from zabalaza.apps.words.models import db, Word, Language


class ExtractStore(object):
    """Extracts and stores words in the specified html document. It also 
    handles possible duplicates in the database.
    """
    def __init__(self, html_page, lang_code):
        self.lang_code = lang_code.split('_')[0]
        self.html_page = html_page
        self._store_words()
        
    def _extract_words(self):
        cleaner = Cleaner(style=True)
        
        page_tree = lxml.html.fromstring(self.html_page)
        page_tree = cleaner.clean_html(page_tree)
        
        page_text = page_tree.text_content()
        words = re.findall('[\'a-zA-Z\-]{2,}', page_text)
        
        return set(words)
    
    def _store_words(self):
        """Stores words"""
        words = self._extract_words()
        language = Language.query.filter(Language.code==self.lang_code).first()
        if language is None:
            return False
        
        for word_data in words:
            word_data = word_data.strip()
            current_word = Word.get_word(word_data, self.lang_code)

            if current_word is not None:
                continue
            word = Word(
                word = word_data,
                language_id = language.id
            )
            db.session.add(word)
        db.session.commit()
        print words
