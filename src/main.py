import os
import sys
import gi

gi.require_version('Gtk', '3.0')
try:
    gi.require_version('WebKit2', '4.0')
except ValueError:
    gi.require_version('WebKit2', '4.1')

from gi.repository import Gtk, WebKit2, Gdk

class NarkBrowser(Gtk.Window):
    def __init__(self):
        super().__init__(title="Nark-Browser")
        self.set_default_size(1024, 768)
        self.connect("destroy", Gtk.main_quit)

        # 永続化データ（Cookie/キャッシュ）の設定
        self.data_dir = os.path.expanduser("~/.local/share/Nark-Browser")
        os.makedirs(self.data_dir, exist_ok=True)

        self.context = WebKit2.WebContext.get_default()
        cookie_manager = self.context.get_cookie_manager()
        cookie_file = os.path.join(self.data_dir, "cookies.sqlite")
        cookie_manager.set_persistent_storage(
            cookie_file, WebKit2.CookiePersistentStorage.SQLITE
        )

        # 1. ツールバー（操作UI）
        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        
        btn_back = Gtk.Button(label="←")
        btn_back.connect("clicked", lambda x: self.get_current_webview().go_back())
        
        btn_forward = Gtk.Button(label="→")
        btn_forward.connect("clicked", lambda x: self.get_current_webview().go_forward())
        
        btn_reload = Gtk.Button(label="↻")
        btn_reload.connect("clicked", lambda x: self.get_current_webview().reload())

        btn_new_tab = Gtk.Button(label="＋")
        btn_new_tab.connect("clicked", lambda x: self.add_new_tab("https://google.com"))

        self.url_entry = Gtk.Entry()
        self.url_entry.connect("activate", self.on_navigate)

        toolbar.pack_start(btn_back, False, False, 2)
        toolbar.pack_start(btn_forward, False, False, 2)
        toolbar.pack_start(btn_reload, False, False, 2)
        toolbar.pack_start(btn_new_tab, False, False, 2)
        toolbar.pack_start(self.url_entry, True, True, 2)

        # 2. タブ管理（Gtk.Notebook）
        self.notebook = Gtk.Notebook()
        self.notebook.set_scrollable(True)
        self.notebook.connect("switch-page", self.on_tab_changed)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        vbox.pack_start(toolbar, False, False, 2)
        vbox.pack_start(self.notebook, True, True, 0)
        self.add(vbox)

        # 初期タブの追加
        start_url = sys.argv[1] if len(sys.argv) > 1 else "https://google.com"
        self.add_new_tab(start_url)

    def add_new_tab(self, url):
        webview = WebKit2.WebView.new_with_context(self.context)
        
        # タブのヘッダー部分（ラベル ＋ ×ボタン）
        tab_label_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        title_label = Gtk.Label(label="新しいタブ")
        btn_close = Gtk.Button(label="✕")
        btn_close.set_relief(Gtk.ReliefStyle.NONE)
        
        tab_label_box.pack_start(title_label, True, True, 0)
        tab_label_box.pack_start(btn_close, False, False, 0)
        tab_label_box.show_all()

        # スクロールエリアに WebView を配置
        scrolled = Gtk.ScrolledWindow()
        scrolled.add(webview)
        scrolled.show_all()

        page_num = self.notebook.append_page(scrolled, tab_label_box)

        # イベント接続
        btn_close.connect("clicked", lambda x: self.close_tab(scrolled))
        webview.connect("load-changed", lambda wv, evt: self.on_load_changed(wv, evt, title_label))

        # 表示設定
        self.notebook.set_current_page(page_num)
        if not (url.startswith("http://") or url.startswith("https://")):
            url = "https://" + url
        webview.load_uri(url)

    def close_tab(self, page_widget):
        page_num = self.notebook.page_num(page_widget)
        if page_num != -1:
            self.notebook.remove_page(page_num)
        
        # タブが全滅したらアプリ終了
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
                # タブ文字数を長すぎないよう制限
                title_label.set_text(title[:12] + "..." if len(title) > 12 else title)

if __name__ == "__main__":
    win = NarkBrowser()
    win.show_all()
    Gtk.main()
