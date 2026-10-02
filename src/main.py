import os
import sys
import gi

gi.require_version('Gtk', '3.0')

try:
    gi.require_version('WebKit2', '4.0')
except ValueError:
    gi.require_version('WebKit2', '4.1')

from gi.repository import Gtk, WebKit2

class NarkBrowser(Gtk.Window):
    def __init__(self):
        super().__init__(title="Nark-Browser")
        self.set_default_size(1024, 768)
        self.connect("destroy", Gtk.main_quit)

        data_dir = os.path.expanduser("~/.local/share/Nark-Browser")
        os.makedirs(data_dir, exist_ok=True)

        context = WebKit2.WebContext.get_default()
        cookie_manager = context.get_cookie_manager()
        cookie_file = os.path.join(data_dir, "cookies.sqlite")
        cookie_manager.set_persistent_storage(
            cookie_file, WebKit2.CookiePersistentStorage.SQLITE
        )

        self.webview = WebKit2.WebView.new_with_context(context)
        
        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        
        btn_back = Gtk.Button(label="←")
        btn_back.connect("clicked", lambda x: self.webview.go_back())
        
        btn_forward = Gtk.Button(label="→")
        btn_forward.connect("clicked", lambda x: self.webview.go_forward())
        
        btn_reload = Gtk.Button(label="↻")
        btn_reload.connect("clicked", lambda x: self.webview.reload())

        self.url_entry = Gtk.Entry()
        self.url_entry.connect("activate", self.on_navigate)

        toolbar.pack_start(btn_back, False, False, 2)
        toolbar.pack_start(btn_forward, False, False, 2)
        toolbar.pack_start(btn_reload, False, False, 2)
        toolbar.pack_start(self.url_entry, True, True, 2)

        self.webview.connect("load-changed", self.on_load_changed)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        vbox.pack_start(toolbar, False, False, 2)
        vbox.pack_start(self.webview, True, True, 0)
        self.add(vbox)

        start_url = sys.argv[1] if len(sys.argv) > 1 else "https://google.com"
        self.navigate_to(start_url)

    def navigate_to(self, url):
        if not (url.startswith("http://") or url.startswith("https://")):
            url = "https://" + url
        self.url_entry.set_text(url)
        self.webview.load_uri(url)

    def on_navigate(self, entry):
        self.navigate_to(entry.get_text())

    def on_load_changed(self, webview, event):
        if event == WebKit2.LoadEvent.COMMITTED:
            self.url_entry.set_text(webview.get_uri())

if __name__ == "__main__":
    win = NarkBrowser()
    win.show_all()
    Gtk.main()
