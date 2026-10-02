import os
import sys

# GPU描画のバグ・低速化を回避（描画トラブル防止）
os.environ["WEBKIT_DISABLE_DMABUF_RENDERER"] = "1"

import gi

gi.require_version('Gtk', '3.0')
try:
    gi.require_version('WebKit2', '4.0')
except ValueError:
    gi.require_version('WebKit2', '4.1')

from gi.repository import Gtk, WebKit2, Gdk

# --- カスタムCSS（モダンなデザイン定義） ---
STYLE_CSS = b"""
window {
    background-color: #2b2b2b;
}

/* ツールバー（ナビゲーションバー） */
.nav-bar {
    background-color: #2b2b2b;
    padding: 4px 6px;
    border-bottom: 1px solid #1e1e1e;
}

/* 小さめで丸みのあるナビボタン */
.nav-btn {
    min-width: 28px;
    min-height: 28px;
    padding: 0px 6px;
    border-radius: 6px;
    background-image: none;
    background-color: transparent;
    color: #dfdfdf;
    border: none;
    font-weight: bold;
}
.nav-btn:hover {
    background-color: #3c3f41;
}

/* URL入力欄 */
.url-entry {
    border-radius: 14px;
    background-color: #1e1e1e;
    color: #ffffff;
    border: 1px solid #3c3f41;
    padding: 2px 12px;
    font-size: 13px;
}
.url-entry:focus {
    border-color: #4a90e2;
}

/* タブバーのデザイン (上部に配置) */
notebook header {
    background-color: #212121;
    border-bottom: 1px solid #1e1e1e;
    padding: 2px 2px 0px 2px;
}

notebook tab {
    background-color: #2d2d2d;
    color: #aaaaaa;
    border-radius: 8px 8px 0px 0px;
    padding: 4px 10px;
    margin-right: 2px;
    border: none;
}

notebook tab:checked {
    background-color: #2b2b2b;
    color: #ffffff;
}

/* タブ閉じるボタン */
.tab-close-btn {
    min-width: 16px;
    min-height: 16px;
    padding: 0;
    margin-left: 6px;
    border-radius: 50%;
    background-color: transparent;
    color: #888888;
    border: none;
    font-size: 10px;
}
.tab-close-btn:hover {
    background-color: #e81123;
    color: #ffffff;
}
"""

class NarkBrowser(Gtk.Window):
    def __init__(self):
        super().__init__(title="Nark-Browser")
        self.set_default_size(1024, 768)
        self.connect("destroy", Gtk.main_quit)

        # CSSの読み込み
        self.apply_styles()

        # 永続化データ（Cookie/キャッシュ）の設定
        self.data_dir = os.path.expanduser("~/.local/share/Nark-Browser")
        os.makedirs(self.data_dir, exist_ok=True)

        self.context = WebKit2.WebContext.get_default()
        cookie_manager = self.context.get_cookie_manager()
        cookie_file = os.path.join(self.data_dir, "cookies.sqlite")
        cookie_manager.set_persistent_storage(
            cookie_file, WebKit2.CookiePersistentStorage.SQLITE
        )

        # 1. ツールバー（UI要素）の作成
        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        toolbar.get_style_context().add_class("nav-bar")
        
        btn_back = Gtk.Button(label="‹")
        btn_back.get_style_context().add_class("nav-btn")
        btn_back.connect("clicked", lambda x: self.get_current_webview() and self.get_current_webview().go_back())
        
        btn_forward = Gtk.Button(label="›")
        btn_forward.get_style_context().add_class("nav-btn")
        btn_forward.connect("clicked", lambda x: self.get_current_webview() and self.get_current_webview().go_forward())
        
        btn_reload = Gtk.Button(label="↻")
        btn_reload.get_style_context().add_class("nav-btn")
        btn_reload.connect("clicked", lambda x: self.get_current_webview() and self.get_current_webview().reload())

        btn_new_tab = Gtk.Button(label="＋")
        btn_new_tab.get_style_context().add_class("nav-btn")
        btn_new_tab.connect("clicked", lambda x: self.add_new_tab("https://google.com"))

        self.url_entry = Gtk.Entry()
        self.url_entry.get_style_context().add_class("url-entry")
        self.url_entry.connect("activate", self.on_navigate)

        toolbar.pack_start(btn_back, False, False, 0)
        toolbar.pack_start(btn_forward, False, False, 0)
        toolbar.pack_start(btn_reload, False, False, 0)
        toolbar.pack_start(self.url_entry, True, True, 4)
        toolbar.pack_start(btn_new_tab, False, False, 0)

        # 2. タブ管理 (Gtk.Notebook) の準備（タブの位置はデフォルトで最上部）
        self.notebook = Gtk.Notebook()
        self.notebook.set_scrollable(True)
        self.notebook.connect("switch-page", self.on_tab_changed)

        # 構造変更：上から「タブバー (Notebook header) -> ツールバー -> ページ画面」の順番に配置
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        vbox.pack_start(toolbar, False, False, 0)
        vbox.pack_start(self.notebook, True, True, 0)
        self.add(vbox)

        # 初期タブ追加
        start_url = sys.argv[1] if len(sys.argv) > 1 else "https://google.com"
        self.add_new_tab(start_url)

    def apply_styles(self):
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(STYLE_CSS)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def add_new_tab(self, url):
        webview = WebKit2.WebView.new_with_context(self.context)

        # --- YouTube再生・メディア設定 & User-Agent 偽装 ---
        settings = webview.get_settings()
        if hasattr(settings, 'set_enable_media_stream'):
            settings.set_enable_media_stream(True)
        if hasattr(settings, 'set_enable_mediacapabilities'):
            settings.set_enable_mediacapabilities(True)
        if hasattr(settings, 'set_enable_webrtc'):
            settings.set_enable_webrtc(True)
        
        user_agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        settings.set_user_agent(user_agent)

        # タブヘッダーのデザイン構築
        tab_label_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
        title_label = Gtk.Label(label="新しいタブ")
        
        btn_close = Gtk.Button(label="✕")
        btn_close.get_style_context().add_class("tab-close-btn")
        btn_close.set_relief(Gtk.ReliefStyle.NONE)
        
        tab_label_box.pack_start(title_label, True, True, 0)
        tab_label_box.pack_start(btn_close, False, False, 0)
        tab_label_box.show_all()

        scrolled = Gtk.ScrolledWindow()
        scrolled.add(webview)
        scrolled.show_all()

        page_num = self.notebook.append_page(scrolled, tab_label_box)

        # イベント割り当て
        btn_close.connect("clicked", lambda x: self.close_tab(scrolled))
        webview.connect("load-changed", lambda wv, evt: self.on_load_changed(wv, evt, title_label))

        self.notebook.set_current_page(page_num)
        if not (url.startswith("http://") or url.startswith("https://")):
            url = "https://" + url
        webview.load_uri(url)

    def close_tab(self, page_widget):
        page_num = self.notebook.page_num(page_widget)
        if page_num != -1:
            self.notebook.remove_page(page_num)
        
        if self.notebook.get_n_pages() == 0:
            Gtk.main_quit()

    def get_current_webview(self):
        page_num = self.notebook.get_current_page()
        if page_num == -1:
            return None
        scrolled = self.notebook.get_nth_page(page_num)
        return scrolled.get_child()

    def navigate_to(self, url):
        webview = self.get_current_webview()
        if webview:
            if not (url.startswith("http://") or url.startswith("https://")):
                url = "https://" + url
            webview.load_uri(url)

    def on_navigate(self, entry):
        self.navigate_to(entry.get_text())

    def on_tab_changed(self, notebook, page, page_num):
        scrolled = notebook.get_nth_page(page_num)
        if scrolled:
            webview = scrolled.get_child()
            uri = webview.get_uri()
            if uri:
                self.url_entry.set_text(uri)

    def on_load_changed(self, webview, event, title_label):
        if event == WebKit2.LoadEvent.COMMITTED:
            uri = webview.get_uri()
            if webview == self.get_current_webview():
                self.url_entry.set_text(uri)
        elif event == WebKit2.LoadEvent.FINISHED:
            title = webview.get_title()
            if title:
                title_label.set_text(title[:10] + "..." if len(title) > 10 else title)

if __name__ == "__main__":
    win = NarkBrowser()
    win.show_all()
    Gtk.main()
