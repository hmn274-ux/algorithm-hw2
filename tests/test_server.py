import http.client
import threading
import unittest
from urllib.parse import urlencode

from src.hash_table import HashTable
from src.server import create_server
from src.shortener import URLShortener


class ServerTests(unittest.TestCase):
    def setUp(self):
        self.shortener = URLShortener()
        self.server = create_server(port=0, shortener=self.shortener)
        self.thread = threading.Thread(target=self.server.serve_forever)
        self.thread.start()
        self.host, self.port = self.server.server_address

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()

    def _request(self, method, path, body=None, headers=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.port)
        connection.request(method, path, body=body, headers=headers or {})
        response = connection.getresponse()
        response_body = response.read().decode("utf-8")
        response_headers = response.headers
        status = response.status
        connection.close()
        return status, response_headers, response_body

    def test_home_page_has_url_form(self):
        status, headers, body = self._request("GET", "/")

        self.assertEqual(status, 200)
        self.assertIn("text/html", headers["Content-Type"])
        self.assertIn('<form method="post" action="/">', body)
        self.assertIn('name="url"', body)

    def test_post_displays_short_link_and_code_redirects(self):
        original_url = "https://example.com/path?q=1"
        body = urlencode({"url": original_url})
        status, _, result_page = self._request(
            "POST",
            "/",
            body,
            {"Content-Type": "application/x-www-form-urlencoded"},
        )
        expected_link = f"http://127.0.0.1:{self.port}/0"

        self.assertEqual(status, 200)
        self.assertIn(expected_link, result_page)
        self.assertIn(original_url, result_page)

        status, headers, _ = self._request("GET", "/0")
        self.assertEqual(status, 302)
        self.assertEqual(headers["Location"], original_url)

    def test_invalid_submission_and_unknown_code_return_errors(self):
        body = urlencode({"url": "not a URL"})
        status, _, error_page = self._request(
            "POST",
            "/",
            body,
            {"Content-Type": "application/x-www-form-urlencoded"},
        )
        self.assertEqual(status, 400)
        self.assertIn("주소를 줄이지 못했어요", error_page)

        status, _, missing_page = self._request("GET", "/missing")
        self.assertEqual(status, 404)
        self.assertIn("링크를 찾을 수 없습니다", missing_page)

    def test_table_shows_chained_nodes_and_horner_calculations(self):
        urls = ("https://a.example", "https://i.example")
        table = self.shortener._url_to_code
        self.assertIsInstance(table, HashTable)
        self.assertEqual(table.hash_index(urls[0]), table.hash_index(urls[1]))
        for url in urls:
            self.shortener.shorten(url)

        status, _, body = self._request("GET", "/table")

        self.assertEqual(status, 200)
        self.assertIn("URL 키", body)
        self.assertIn("짧은 코드", body)
        self.assertIn("짧은 링크", body)
        self.assertIn("&rarr;", body)
        self.assertEqual(body.count("<details>"), 2)
        self.assertIn("호너 해시 계산 펼치기", body)
        self.assertIn("× 31", body)
        self.assertIn("최종 칸", body)


if __name__ == "__main__":
    unittest.main()
