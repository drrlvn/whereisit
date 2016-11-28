from html.parser import HTMLParser


class HTMLStripper(HTMLParser):
     def __init__(self):
         super().__init__()
         self._ignore = False
         self._data = []

     def handle_starttag(self, tag, attrs):
         if tag == 'script':
             self._ignore = True
         elif tag == 'br':
             self._data.append('\n')

     def handle_endtag(self, tag):
         if tag == 'script':
             self._ignore = False

     def handle_data(self, data):
         if self._ignore:
             return
         self._data.append(data)

     def get_data(self):
         return ''.join(self._data).strip()
