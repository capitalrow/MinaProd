from playwright.sync_api import sync_playwright

def test_search_and_highlight_ui(live_server):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(live_server.url + "/meeting/1")
        page.fill("#searchInput", "project")
        assert page.locator("mark.highlight").count() > 0
        browser.close()