import sys
import os
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, GLib

# Modern Libadwaita style manager for dark mode
style_manager = Adw.StyleManager.get_default()
style_manager.set_color_scheme(Adw.ColorScheme.PREFER_DARK)


class MainWindow(Adw.ApplicationWindow):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.set_title("Dashboard")
        self.set_default_size(1100, 650)

        # Setup persistence file path for quick notes
        config_dir = os.path.join(GLib.get_user_config_dir(), "com.joshua.dashboard")
        os.makedirs(config_dir, exist_ok=True)
        self.notes_file_path = os.path.join(config_dir, "quick_notes.txt")

        # 1. ROOT HORIZONTAL PANED: Draggable divider between Sidebar and Main Content
        self.root_paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        self.root_paned.set_wide_handle(True)
        self.set_content(self.root_paned)

        # Build pages first so sidebar navigation can reference them
        self.setup_pages()
        self.setup_sidebar()

    def setup_sidebar(self):
        """Creates the sidebar with a vertical paned splitter for navigation vs notes."""
        sidebar_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        sidebar_box.add_css_class("background")
        
        sidebar_header = Adw.HeaderBar()
        sidebar_header.set_show_title(True)
        sidebar_header.set_show_end_title_buttons(False)

        # Toggle button to slide notes open/closed
        notes_toggle_btn = Gtk.Button()
        notes_toggle_btn.set_icon_name("document-edit-symbolic")
        notes_toggle_btn.set_tooltip_text("Toggle Quick Notes")
        notes_toggle_btn.connect("clicked", self.toggle_sidebar_notes)
        sidebar_header.pack_end(notes_toggle_btn)

        sidebar_box.append(sidebar_header)

        # --- VERTICAL PANED CONTAINER FOR NOTES ---
        self.sidebar_paned = Gtk.Paned(orientation=Gtk.Orientation.VERTICAL)
        self.sidebar_paned.set_wide_handle(True)
        self.sidebar_paned.set_vexpand(True)

        # 1. Top Pane: Navigation List
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)

        self.list_box = Gtk.ListBox()
        self.list_box.add_css_class("navigation-sidebar")
        self.list_box.set_margin_top(12)
        self.list_box.set_margin_bottom(12)
        self.list_box.set_margin_start(12)
        self.list_box.set_margin_end(12)
        self.list_box.set_selection_mode(Gtk.SelectionMode.SINGLE)
        
        self.page_names = ["dashboard", "applications", "stats", "settings"]
        titles = ["Dashboard", "Applications", "System Stats", "Settings"]

        for title in titles:
            row = Adw.ActionRow(title=title)
            self.list_box.append(row)

        self.list_box.connect("row-selected", self.on_nav_row_selected)
        scrolled.set_child(self.list_box)
        
        self.sidebar_paned.set_start_child(scrolled)
        self.sidebar_paned.set_resize_start_child(True)
        self.sidebar_paned.set_shrink_start_child(False)

        # 2. Bottom Pane: Toggle-able & Resizable Notes Container
        self.notes_revealer = Gtk.Revealer()
        self.notes_revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_UP)
        self.notes_revealer.set_reveal_child(False)

        notes_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        notes_container.set_margin_top(8)
        notes_container.set_margin_bottom(12)
        notes_container.set_margin_start(12)
        notes_container.set_margin_end(12)
        notes_container.add_css_class("card")

        notes_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        notes_title = Gtk.Label(label="Quick Notes")
        notes_title.set_xalign(0)
        notes_title.add_css_class("heading")
        notes_header.append(notes_title)

        notes_spacer = Gtk.Box()
        notes_spacer.set_hexpand(True)
        notes_header.append(notes_spacer)

        close_notes_btn = Gtk.Button.new_from_icon_name("window-close-symbolic")
        close_notes_btn.add_css_class("flat")
        close_notes_btn.set_tooltip_text("Close Notes")
        close_notes_btn.connect("clicked", lambda b: self.notes_revealer.set_reveal_child(False))
        notes_header.append(close_notes_btn)
        
        #notes_container.append(notes_header)

        notes_scrolled = Gtk.ScrolledWindow()
        notes_scrolled.set_vexpand(True)

        self.notes_text_view = Gtk.TextView()
        self.notes_text_view.set_wrap_mode(Gtk.WrapMode.WORD)
        
        # --- LOAD & SAVE NOTES LOGIC ---
        self.notes_buffer = self.notes_text_view.get_buffer()
        self.load_notes()
        # Connect to the 'changed' signal so text saves automatically as you type
        self.notes_buffer.connect("changed", self.save_notes)

        notes_scrolled.set_child(self.notes_text_view)
        notes_container.append(notes_scrolled)
        self.notes_revealer.set_child(notes_container)

        self.sidebar_paned.set_end_child(self.notes_revealer)
        self.sidebar_paned.set_resize_end_child(True)
        self.sidebar_paned.set_shrink_end_child(False)
        self.sidebar_paned.set_position(380)

        sidebar_box.append(self.sidebar_paned)
        
        self.root_paned.set_start_child(sidebar_box)
        self.root_paned.set_resize_start_child(True)
        self.root_paned.set_shrink_start_child(False)
        self.root_paned.set_position(260)

        first_row = self.list_box.get_row_at_index(0)
        if first_row:
            self.list_box.select_row(first_row)

    def load_notes(self):
        """Loads saved notes from disk into the text buffer if the file exists."""
        if os.path.exists(self.notes_file_path):
            try:
                with open(self.notes_file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    self.notes_buffer.set_text(content)
            except Exception as e:
                print(f"Failed to load notes: {e}")

    def save_notes(self, buffer):
        """Saves current text buffer contents to disk."""
        start_iter = buffer.get_start_iter()
        end_iter = buffer.get_end_iter()
        text = buffer.get_text(start_iter, end_iter, True)
        try:
            with open(self.notes_file_path, "w", encoding="utf-8") as f:
                f.write(text)
        except Exception as e:
            print(f"Failed to save notes: {e}")

    def toggle_sidebar_notes(self, button):
        current_state = self.notes_revealer.get_reveal_child()
        self.notes_revealer.set_reveal_child(not current_state)

    def setup_pages(self):
        self.view_stack = Adw.ViewStack()
        self.root_paned.set_end_child(self.view_stack)
        self.root_paned.set_resize_end_child(True)
        self.root_paned.set_shrink_end_child(True)

        dashboard_view = self.create_dashboard_page()
        self.view_stack.add_named(dashboard_view, "dashboard")

        apps_view = self.create_simple_text_page("Applications Management", "Manage installed apps and shortcuts here.")
        self.view_stack.add_named(apps_view, "applications")

        stats_view = self.create_simple_text_page("System Statistics", "CPU, Memory, and Disk usage monitors will go here.")
        self.view_stack.add_named(stats_view, "stats")

        settings_view = self.create_simple_text_page("Preferences", "Customize app appearance and behavior.")
        self.view_stack.add_named(settings_view, "settings")

    def create_dashboard_page(self):
        toolbar_view = Adw.ToolbarView()
        header_bar = Adw.HeaderBar()
        toolbar_view.add_top_bar(header_bar)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_hexpand(True)
        toolbar_view.set_content(scrolled)

        wrapper = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        wrapper.set_margin_top(24)
        wrapper.set_margin_bottom(24)
        wrapper.set_margin_start(24)
        wrapper.set_margin_end(24)
        scrolled.set_child(wrapper)

        #title_label = Gtk.Label(label="Quick Launcher")
        #title_label.set_xalign(0)
        #title_label.add_css_class("title-1")
        #wrapper.append(title_label)

        flow_box = Gtk.FlowBox()
        flow_box.set_valign(Gtk.Align.FILL)
        flow_box.set_max_children_per_line(3)
        flow_box.set_min_children_per_line(1)
        flow_box.set_row_spacing(20)
        flow_box.set_column_spacing(20)
        flow_box.set_selection_mode(Gtk.SelectionMode.NONE)
        flow_box.set_homogeneous(False)
        flow_box.set_halign(Gtk.Align.FILL)
        wrapper.append(flow_box)

        apps = [
            {"name": "Terminal", "desc": "Ghostty shell", "cmd": "ghostty +new-window", "icon": "utilities-terminal"},
            {"name": "File Manager", "desc": "Dolphin file browser", "cmd": "dolphin", "icon": "system-file-manager"},
            {"name": "Web Browser", "desc": "Firefox web browser", "cmd": "firefox", "icon": "firefox"},
            {"name": "System Monitor", "desc": "Btop resource usage", "cmd": "kitty btop", "icon": "utilities-system-monitor"},
            {
                "name": "Note Taker",
                "desc": "Personal note taking app",
                "cmd": "/home/joshua/Documents/NoteTaker/.venv/bin/python3 /home/joshua/Documents/NoteTaker/main.py",
                "icon_path": "/home/joshua/Pictures/lebron.jpg"
            },
            {
                "name": "Stremio",
                "desc": "Streaming service",
                "cmd": "flatpak run com.stremio.Stremio",
                "icon_path": "/home/joshua/Pictures/lebron.jpg"
            },
             
        ]

        for app_info in apps:
            card_btn = self.create_app_card(
                app_info["name"], app_info["desc"], 
                app_info.get("icon"), app_info.get("icon_path")
            )
            card_btn.connect("clicked", lambda btn, cmd=app_info["cmd"]: self.launch_app(cmd))
            flow_box.append(card_btn)

        return toolbar_view

    def create_simple_text_page(self, title_text, description_text):
        toolbar_view = Adw.ToolbarView()
        header_bar = Adw.HeaderBar()
        toolbar_view.add_top_bar(header_bar)

        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        content_box.set_valign(Gtk.Align.CENTER)
        content_box.set_halign(Gtk.Align.CENTER)

        title = Gtk.Label(label=title_text)
        title.add_css_class("title-1")
        
        desc = Gtk.Label(label=description_text)
        desc.add_css_class("dim-label")

        content_box.append(title)
        content_box.append(desc)

        toolbar_view.set_content(content_box)
        return toolbar_view

    def on_nav_row_selected(self, list_box, row):
        if row is not None:
            index = row.get_index()
            if 0 <= index < len(self.page_names):
                target_page = self.page_names[index]
                self.view_stack.set_visible_child_name(target_page)

    def create_app_card(self, name, description, icon_name=None, icon_path=None):
        button = Gtk.Button()
        button.add_css_class("card")
        button.set_size_request(180, 180)
        button.set_halign(Gtk.Align.CENTER)
        button.set_valign(Gtk.Align.CENTER)
        button.set_tooltip_text(f"{name} — {description}")

        card_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        card_box.set_valign(Gtk.Align.CENTER)
        card_box.set_halign(Gtk.Align.CENTER)
        card_box.set_hexpand(True)
        card_box.set_vexpand(True)

        icon_widget = None
        if icon_path:
            try:
                icon_widget = Gtk.Image.new_from_file(icon_path)
                icon_widget.set_pixel_size(48)
            except Exception as e:
                print(f"Failed to load icon: {e}")

        if not icon_widget and icon_name:
            theme = Gtk.IconTheme.get_for_display(button.get_display())
            if theme.has_icon(icon_name):
                icon_widget = Gtk.Image.new_from_icon_name(icon_name)
                icon_widget.set_pixel_size(48)

        if icon_widget:
            card_box.append(icon_widget)
        else:
            fallback_label = Gtk.Label(label=name)
            fallback_label.add_css_class("title-3")
            card_box.append(fallback_label)

        spacer = Gtk.Box()
        spacer.set_vexpand(True)
        card_box.append(spacer)

        text_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        name_label = Gtk.Label(label=name)
        name_label.add_css_class("heading")
        name_label.set_ellipsize(3)

        desc_label = Gtk.Label(label=description)
        desc_label.add_css_class("dim-label")
        desc_label.set_ellipsize(3)

        text_box.append(name_label)
        #text_box.append(desc_label)
        card_box.append(text_box)

        button.set_child(card_box)
        return button

    def launch_app(self, cmd):
        import subprocess
        try:
            subprocess.Popen(cmd, shell=True)
            print(f"Launched: {cmd}")
        except Exception as e:
            print(f"Failed to launch {cmd}: {e}")


def on_activate(app):
    win = MainWindow(application=app)
    win.present()


app = Adw.Application(application_id="com.joshua.dashboard")
app.connect("activate", on_activate)

sys.exit(app.run(sys.argv))