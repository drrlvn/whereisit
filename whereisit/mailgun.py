import urllib.parse
import aiohttp


class Mailgun:
    def __init__(self, *, session, domain, api_key):
        self._session = session
        self._domain = domain
        self._api_key = api_key

    async def send(self, *, from_addr, to_addrs, subject, body):
        request = self._session.post(
            "https://api.mailgun.net/v3/{}/messages".format(urllib.parse.quote(self._domain)),
            auth=aiohttp.BasicAuth("api", self._api_key),
            data={"from": from_addr,
                  "to": to_addrs,
                  "subject": subject,
                  "text": body,
                 })

        async with request as response:
            response.raise_for_status()
