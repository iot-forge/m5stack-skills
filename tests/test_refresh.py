"""scripts/refresh.py: the M5 docs page check (B37).

The pages are served from the strings below through a stand-in for refresh.get, and the sources come from a
temporary data/. No test touches the network.
Run: python -m unittest discover tests
"""
import contextlib, importlib.util, io, json, shutil, tempfile, unittest, urllib.error
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("refresh", REPO / "scripts/refresh.py")
refresh = importlib.util.module_from_spec(spec)
spec.loader.exec_module(refresh)

URL = "https://docs.m5stack.com/en/core/core2"
PAYLOAD_PATH = "/_nuxt/static/{build}/en/core/Core2/payload.js"
SHELL = '<html><head><link rel="preload" href="/_nuxt/static/{build}/en/core/Core2/state.js" as="script">' \
        '<link rel="preload" href="' + PAYLOAD_PATH + '" as="script"></head><body>Core2</body></html>'
PAYLOAD = '__NUXT_JSONP__("/en/core/Core2", {{data:[{{htmlbody:"\\u003Ch1\\u003ECore2\\u003C\\u002Fh1\\u003E",' \
          'contributorSkus:[{skus}],markdownSourcePath:"core\\u002FCore2.md",markdownRaw:{raw}}}],fetch:{{}},mutations:[]}});'
# sha256 of the page's Markdown as UTF-8, from `printf '<text>' | sha256sum`
CORE2 = "# Core2\n"
CORE2_SHA = "1260848266871be5b7e0c0f9d1ddb7d17fa4b57b32bc87c84b6236c8e4884ab3"
CORE2_EDITED = "# Core2\n\nFlash: 16MB\n"
CORE2_EDITED_SHA = "e5b06eb8d3f0f8bf92b499edd4cebbbbc8af2afc3e2e14f3fbbea8755cc06b77"


def site(markdown, build="111", skus='"A176"'):
    """{url: text} for one docs page whose Markdown is MARKDOWN, as M5's build BUILD serves it."""
    return {URL: SHELL.format(build=build),
            "https://docs.m5stack.com" + PAYLOAD_PATH.format(build=build): PAYLOAD.format(skus=skus, raw=json.dumps(markdown))}


class DocsPages(unittest.TestCase):
    def setUp(self):
        self.data = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.data, ignore_errors=True)
        self.addCleanup(setattr, refresh, "DATA", refresh.DATA)
        self.addCleanup(setattr, refresh, "get", refresh.get)
        refresh.DATA = self.data
        self.sources([{"id": "m5-core2", "kind": "m5-docs", "title": "Core2", "url": URL, "ref": "retrieved 2026-09-26",
                       "content_sha256": CORE2_SHA}])

    def sources(self, sources):
        (self.data / "sources.json").write_text(json.dumps({"schema_version": 1, "sources": sources}), encoding="utf-8")

    def serve(self, pages):
        def get(url):
            if url not in pages:
                raise urllib.error.URLError(f"no fixture for {url}")
            return pages[url]
        refresh.get = get

    def section(self):
        """The docs-page section of the drift report, as lines."""
        rep = []
        refresh.check_m5_docs(rep)
        return rep

    def test_changed_page_is_listed(self):
        self.serve(site(CORE2_EDITED))
        rep = self.section()
        self.assertEqual(rep[0], "## M5 docs pages")
        changed = [l for l in rep if l.startswith("- CHANGED page m5-core2")]
        self.assertEqual(len(changed), 1, rep)
        self.assertIn(URL, changed[0])
        self.assertIn(CORE2_EDITED_SHA, changed[0])  # the hash a person records after re-reading the page

    def test_same_content_is_unchanged(self):
        self.serve(site(CORE2))
        self.assertEqual(self.section(), ["## M5 docs pages", "- 1 of 1 pages unchanged since their recorded hash"])

    def test_a_new_m5_deploy_is_not_a_change(self):  # the build id and the site-wide product list move on every deploy
        self.serve(site(CORE2, build="222", skus='"A176","K999"'))
        self.assertEqual(self.section()[1:], ["- 1 of 1 pages unchanged since their recorded hash"])

    def test_line_endings_are_not_a_change(self):  # M5's pages mix CRLF and LF Markdown
        self.serve(site(CORE2.replace("\n", "\r\n")))
        self.assertEqual(self.section()[1:], ["- 1 of 1 pages unchanged since their recorded hash"])

    def test_unreachable_page_is_reported_and_never_unchanged(self):
        self.sources([{"id": "m5-gone", "kind": "m5-docs", "title": "Gone", "url": "https://docs.m5stack.com/en/core/gone",
                       "ref": "retrieved 2026-09-26", "content_sha256": CORE2_SHA},
                      {"id": "m5-core2", "kind": "m5-docs", "title": "Core2", "url": URL, "ref": "retrieved 2026-09-26",
                       "content_sha256": CORE2_SHA}])
        self.serve(site(CORE2))
        rep = self.section()
        self.assertTrue(any(l.startswith("- COULD NOT CHECK page m5-gone") for l in rep), rep)
        self.assertEqual(rep[-1], "- 1 of 2 pages unchanged since their recorded hash")  # the page after it is still checked

    def test_page_without_its_content_is_reported(self):  # M5 changed the site's shape: say so, never guess
        pages = site(CORE2)
        pages[URL] = "<html><body>Core2</body></html>"
        self.serve(pages)
        rep = self.section()
        self.assertTrue(any(l.startswith("- COULD NOT CHECK page m5-core2") for l in rep), rep)
        self.assertEqual(rep[-1], "- 0 of 1 pages unchanged since their recorded hash")

    def test_only_docs_sources_are_fetched(self):
        self.sources([{"id": "esp32-datasheet", "kind": "datasheet", "title": "ESP32", "url": "https://example.com/esp32.pdf", "ref": "v4.9"}])
        self.serve({})
        self.assertEqual(self.section()[1:], ["- 0 of 0 pages unchanged since their recorded hash"])

    def run_main(self, *argv):
        """(exit code, report) of one refresh run; every upstream but the docs pages is unreachable."""
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = refresh.main(list(argv))
        return code, out.getvalue()

    def test_strict_exits_1_on_a_changed_page(self):
        self.serve(site(CORE2_EDITED))
        code, out = self.run_main("--strict")
        self.assertIn("- CHANGED page m5-core2", out)
        self.assertEqual(code, 1)

    def test_strict_exits_0_when_no_page_changed(self):
        self.serve(site(CORE2))
        code, out = self.run_main("--strict")
        self.assertIn("## M5 docs pages\n- 1 of 1 pages unchanged", out)
        self.assertEqual(code, 0)

    def test_refresh_never_writes_data(self):  # ADR 0003: a person records the new hash
        before = (self.data / "sources.json").read_bytes()
        self.serve(site(CORE2_EDITED))
        self.run_main()
        self.assertEqual((self.data / "sources.json").read_bytes(), before)
        self.assertEqual([p.name for p in self.data.iterdir()], ["sources.json"])


if __name__ == "__main__":
    unittest.main()
