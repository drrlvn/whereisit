FROM python

RUN mkdir /usr/src/whereisit
COPY setup.py /usr/src/whereisit
COPY whereisit /usr/src/whereisit/whereisit
RUN pip install --no-cache-dir -e /usr/src/whereisit
CMD whereisit /etc/whereisit.toml
