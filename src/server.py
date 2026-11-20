"""HTTP interface for the in-memory URL shortener."""

import argparse
import html
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, quote, unquote, urlsplit

from src.shortener import URLShortener


class URLShortenerHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlsplit(self.path).path
        if path == "/":
            self._send_html(200, self._home_page())
        elif path == "/table":
            self._send_html(200, self._table_page())
        else:
            self._redirect_code(path)

    def do_POST(self):
        if urlsplit(self.path).path != "/":
            self._send_not_found()
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            if content_length < 0:
                raise ValueError("Content-Length cannot be negative")
            body = self.rfile.read(content_length).decode("utf-8")
        except (ValueError, UnicodeDecodeError):
            self._send_html(400, self._error_page("요청을 읽을 수 없습니다."))
            return

        fields = parse_qs(body, keep_blank_values=True)
        urls = fields.get("url", [])
        url = urls[0] if urls else ""
        try:
            code = self.server.shortener.shorten(url)
        except ValueError as error:
            self._send_html(400, self._error_page(str(error)))
            return

        host = self.headers.get("Host", "localhost")
        short_url = f"http://{host}/{code}"
        content = (
            '<main><h1>짧은 링크가 준비됐어요</h1>'
            f'<p>짧은 링크: <a href="{html.escape(short_url, quote=True)}">'
            f"{html.escape(short_url)}</a></p>"
            f"<p>원본 주소: {html.escape(url)}</p>"
            '<p><a href="/">다른 주소 줄이기</a> · '
            '<a href="/table">해시 테이블 보기</a></p></main>'
        )
        self._send_html(200, self._page("단축 결과", content))

    def _redirect_code(self, path):
        if not path.startswith("/") or "/" in path[1:]:
            self._send_not_found()
            return
        code = unquote(path[1:])
        if not code:
            self._send_not_found()
            return
        try:
            url = self.server.shortener.expand(code)
        except KeyError:
            self._send_not_found()
            return

        self.send_response(302)
        self.send_header(
            "Location", quote(url, safe=":/?#[]@!$&'()*+,;=%")
        )
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _home_page(self):
        content = (
            "<main><h1>URL 단축 서비스</h1>"
            '<form method="post" action="/">'
            '<label for="url">줄일 URL</label>'
            '<input id="url" name="url" type="url" required '
            'placeholder="https://example.com/long/path">'
            '<button type="submit">줄이기</button>'
            "</form>"
            '<p><a href="/table">현재 해시 테이블 보기</a></p></main>'
        )
        return self._page("URL 단축 서비스", content)

    def _table_page(self):
        table = self.server.shortener._url_to_code
        content = (
            "<main><h1>현재 URL 해시 테이블</h1>"
            f"<p>칸 수: {table.capacity} · 항목 수: {len(table)} · "
            f"적재율: {table.load_factor:.3f}</p>"
            '<p>각 칸의 연결 리스트는 왼쪽에서 오른쪽으로 이어집니다. '
            "노드를 펼치면 URL 키의 호너 해시 계산을 볼 수 있습니다.</p>"
        )

        for bucket_index, entries in enumerate(table.bucket_items()):
            content += (
                f'<section class="bucket"><h2>칸 {bucket_index}</h2>'
                '<div class="chain">'
            )
            if not entries:
                content += '<p class="empty">비어 있음</p>'
            for position, (url, code) in enumerate(entries):
                if position:
                    content += '<span class="arrow" aria-label="다음 노드">&rarr;</span>'
                short_url = self._short_url(code)
                content += (
                    '<article class="node">'
                    f"<p><strong>URL 키</strong><br>{html.escape(url)}</p>"
                    f"<p><strong>짧은 코드</strong><br>{html.escape(code)}</p>"
                    f'<p><strong>짧은 링크</strong><br><a href="'
                    f'{html.escape(short_url, quote=True)}">'
                    f"{html.escape(short_url)}</a></p>"
                    f"{self._hash_details(table, url)}"
                    "</article>"
                )
            content += "</div></section>"

        content += '<p><a href="/">돌아가기</a></p></main>'
        return self._page("해시 테이블", content)

    def _hash_details(self, table, key):
        bucket_index, steps = table.hash_trace(key)
        content = (
            '<details><summary>호너 해시 계산 펼치기</summary>'
            "<p>시작값: h₀ = 0</p>"
            "<ol>"
        )
        for position, character, code_point, previous, value in steps:
            safe_character = html.escape(repr(character))
            content += (
                f"<li>문자 {position + 1} ({safe_character}, "
                f"ord={code_point}): h{position + 1} = "
                f"({previous} × 31 + {code_point}) % {table.capacity} "
                f"= {value}</li>"
            )
        content += (
            "</ol>"
            f"<p>최종 칸: {bucket_index}</p>"
            "</details>"
        )
        return content

    def _short_url(self, code):
        host = self.headers.get(
            "Host", f"localhost:{self.server.server_port}"
        )
        return f"http://{host}/{code}"

    def _error_page(self, message):
        content = (
            "<main><h1>주소를 줄이지 못했어요</h1>"
            f"<p>{html.escape(message)}</p>"
            '<p><a href="/">다시 시도하기</a></p></main>'
        )
        return self._page("입력 오류", content)

    def _send_not_found(self):
        content = (
            "<main><h1>링크를 찾을 수 없습니다</h1>"
            '<p><a href="/">처음으로</a></p></main>'
        )
        self._send_html(404, self._page("찾을 수 없음", content))

    def _page(self, title, content):
        return (
            "<!doctype html><html lang=\"ko\"><head>"
            '<meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            f"<title>{html.escape(title)}</title>"
            "<style>"
            "body{font-family:system-ui,sans-serif;line-height:1.5;margin:2rem auto;"
            "padding:0 1rem;max-width:70rem;color:#172033}"
            "input{box-sizing:border-box;display:block;margin:.5rem 0 1rem;"
            "padding:.7rem;width:100%;max-width:40rem}"
            "button{padding:.7rem 1.2rem;cursor:pointer}"
            ".bucket{border:1px solid #cbd5e1;border-radius:.5rem;margin:1rem 0;"
            "padding:1rem}.chain{display:flex;align-items:stretch;gap:.75rem;"
            "flex-wrap:wrap}.node{border:1px solid #94a3b8;border-radius:.4rem;"
            "padding:.8rem;min-width:16rem;max-width:36rem;overflow-wrap:anywhere}"
            ".arrow{align-self:center;font-size:1.8rem;color:#475569}"
            ".empty{color:#64748b}details{margin-top:.8rem}summary{cursor:pointer}"
            "ol{padding-left:2rem;overflow-wrap:anywhere}"
            "</style></head><body>"
            f"{content}</body></html>"
        )

    def _send_html(self, status, document):
        body = document.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def create_server(port=8000, shortener=None):
    server = HTTPServer(("", port), URLShortenerHandler)
    server.shortener = shortener if shortener is not None else URLShortener()
    return server


def main():
    parser = argparse.ArgumentParser(description="Run the URL shortener service.")
    parser.add_argument("--port", type=int, default=8000)
    arguments = parser.parse_args()

    server = create_server(arguments.port)
    print(f"Serving URL shortener on port {server.server_port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping URL shortener.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
