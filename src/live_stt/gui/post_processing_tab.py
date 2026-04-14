"""Post-processing tab — manage the ordered list of post-processors."""

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk  # noqa: E402

from ..post_processors.base import PostProcessorConfig, make_config
from ..post_processors.registry import PostProcessorRegistry
from ..services.config import Config

_PROVIDERS = ["anthropic", "deepl"]
_PROVIDER_LABELS = {"anthropic": "Anthropic (Claude)", "deepl": "DeepL"}
_PROVIDER_DEFAULT_ICONS = {
    "anthropic": "accessories-text-editor-symbolic",
    "deepl": "preferences-desktop-locale-symbolic",
}


# ---------------------------------------------------------------------------
# Provider chooser dialog
# ---------------------------------------------------------------------------

class ProviderChooserDialog(Gtk.Dialog):
    """Small modal that lets the user pick a provider before editing."""

    def __init__(self, parent: Gtk.Window | None) -> None:
        super().__init__(
            title="Choose provider",
            transient_for=parent,
            flags=Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
        )
        self.add_button("Cancel", Gtk.ResponseType.CANCEL)
        ok_btn = self.add_button("Next", Gtk.ResponseType.OK)
        ok_btn.get_style_context().add_class("suggested-action")

        box = self.get_content_area()
        box.set_spacing(12)
        box.set_margin_top(16)
        box.set_margin_bottom(8)
        box.set_margin_start(16)
        box.set_margin_end(16)

        label = Gtk.Label(label="Select the post-processor type:")
        label.set_xalign(0)
        box.pack_start(label, False, False, 0)

        self._combo = Gtk.ComboBoxText()
        for p in _PROVIDERS:
            self._combo.append(p, _PROVIDER_LABELS[p])
        self._combo.set_active_id("anthropic")
        box.pack_start(self._combo, False, False, 0)

        self.show_all()

    def get_provider(self) -> str:
        return self._combo.get_active_id() or "anthropic"


# ---------------------------------------------------------------------------
# Editor dialog
# ---------------------------------------------------------------------------

class ProcessorEditorDialog(Gtk.Dialog):
    """Dialog for creating or editing a single PostProcessorConfig.

    The *provider* is fixed at construction time — for new processors it is
    chosen via :class:`ProviderChooserDialog` beforehand.
    """

    def __init__(
        self,
        parent: Gtk.Window,
        app_config: Config,
        cfg: PostProcessorConfig,
    ) -> None:
        is_new = cfg.name == "New Processor"
        super().__init__(
            title="Edit processor" if not is_new else "Add processor",
            transient_for=parent,
            flags=Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
        )
        self._app_config = app_config
        self._provider = cfg.provider
        self._editing_id = cfg.id

        self.add_button("Cancel", Gtk.ResponseType.CANCEL)
        ok_btn = self.add_button("Save", Gtk.ResponseType.OK)
        ok_btn.get_style_context().add_class("suggested-action")

        box = self.get_content_area()
        box.set_spacing(0)

        grid = Gtk.Grid()
        grid.set_column_spacing(12)
        grid.set_row_spacing(8)
        grid.set_margin_top(16)
        grid.set_margin_bottom(8)
        grid.set_margin_start(16)
        grid.set_margin_end(16)
        box.pack_start(grid, True, True, 0)

        # Provider (read-only)
        grid.attach(Gtk.Label(label="Provider", xalign=0), 0, 0, 1, 1)
        provider_label = Gtk.Label(
            label=_PROVIDER_LABELS.get(self._provider, self._provider),
            xalign=0,
        )
        provider_label.set_hexpand(True)
        grid.attach(provider_label, 1, 0, 1, 1)

        # Name
        grid.attach(Gtk.Label(label="Name", xalign=0), 0, 1, 1, 1)
        self._name = Gtk.Entry()
        self._name.set_hexpand(True)
        self._name.set_text(cfg.name)
        grid.attach(self._name, 1, 1, 1, 1)

        # Icon
        grid.attach(Gtk.Label(label="Icon name", xalign=0), 0, 2, 1, 1)
        self._icon = Gtk.Entry()
        self._icon.set_hexpand(True)
        self._icon.set_placeholder_text("e.g. accessories-text-editor-symbolic")
        self._icon.set_text(cfg.icon)
        grid.attach(self._icon, 1, 2, 1, 1)

        # Hotkey
        grid.attach(Gtk.Label(label="Hotkey (optional)", xalign=0), 0, 3, 1, 1)
        self._hotkey = Gtk.Entry()
        self._hotkey.set_hexpand(True)
        self._hotkey.set_placeholder_text("e.g. <ctrl>+<shift>+t")
        self._hotkey.set_text(cfg.hotkey)
        grid.attach(self._hotkey, 1, 3, 1, 1)

        # Provider-specific form
        from ..post_processors.anthropic.gui import AnthropicForm
        from ..post_processors.deepl.gui import DeepLForm

        if self._provider == "anthropic":
            self._form = AnthropicForm()
        else:
            self._form = DeepLForm()

        self._form.set_margin_top(8)
        self._form.set_margin_bottom(8)
        self._form.populate(cfg)
        box.pack_start(self._form, True, True, 0)

        # API key warning
        self._warning = Gtk.Label()
        self._warning.set_xalign(0)
        self._warning.set_margin_start(16)
        self._warning.set_margin_end(16)
        self._warning.set_margin_bottom(12)
        self._warning.set_no_show_all(True)
        box.pack_start(self._warning, False, False, 0)

        self._update_warning()
        self.show_all()

    def _update_warning(self) -> None:
        if self._provider == "anthropic" and not self._app_config.anthropic_api_key:
            self._warning.set_markup(
                '<span foreground="#e67e22">⚠  Anthropic API key not set — '
                "configure it in Settings → API Keys.</span>"
            )
            self._warning.show()
        elif self._provider == "deepl" and not self._app_config.deepl_api_key:
            self._warning.set_markup(
                '<span foreground="#e67e22">⚠  DeepL API key not set — '
                "configure it in Settings → API Keys.</span>"
            )
            self._warning.show()
        else:
            self._warning.hide()

    def get_result(self) -> PostProcessorConfig:
        """Build and return the PostProcessorConfig from current form state."""
        icon = (
            self._icon.get_text().strip()
            or _PROVIDER_DEFAULT_ICONS.get(self._provider, "system-run-symbolic")
        )
        provider_fields = self._form.collect()

        return PostProcessorConfig(
            id=self._editing_id,
            name=self._name.get_text().strip() or "Processor",
            icon=icon,
            provider=self._provider,
            hotkey=self._hotkey.get_text().strip(),
            **provider_fields,
        )


# ---------------------------------------------------------------------------
# Processor row
# ---------------------------------------------------------------------------

class ProcessorRow(Gtk.ListBoxRow):
    """A row in the post-processor list showing icon, name, and action buttons."""

    def __init__(
        self,
        cfg: PostProcessorConfig,
        on_edit: callable,
        on_delete: callable,
        on_toggle: callable,
    ) -> None:
        super().__init__()
        self.set_selectable(False)
        self.set_activatable(False)

        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        hbox.set_margin_top(6)
        hbox.set_margin_bottom(6)
        hbox.set_margin_start(10)
        hbox.set_margin_end(10)

        icon = Gtk.Image.new_from_icon_name(cfg.icon, Gtk.IconSize.LARGE_TOOLBAR)
        hbox.pack_start(icon, False, False, 0)

        name_label = Gtk.Label(label=cfg.name, xalign=0)
        name_label.set_hexpand(True)
        hbox.pack_start(name_label, True, True, 0)

        if cfg.hotkey:
            hotkey_label = Gtk.Label(label=cfg.hotkey)
            hotkey_label.get_style_context().add_class("dim-label")
            hbox.pack_start(hotkey_label, False, False, 0)

        enabled_switch = Gtk.Switch()
        enabled_switch.set_active(cfg.enabled)
        enabled_switch.set_valign(Gtk.Align.CENTER)
        enabled_switch.connect("notify::active", lambda sw, _: on_toggle(cfg.id, sw.get_active()))
        hbox.pack_start(enabled_switch, False, False, 0)

        edit_btn = Gtk.Button.new_from_icon_name("document-edit-symbolic", Gtk.IconSize.SMALL_TOOLBAR)
        edit_btn.set_tooltip_text("Edit")
        edit_btn.set_relief(Gtk.ReliefStyle.NONE)
        edit_btn.connect("clicked", lambda _: on_edit(cfg))
        hbox.pack_start(edit_btn, False, False, 0)

        del_btn = Gtk.Button.new_from_icon_name("edit-delete-symbolic", Gtk.IconSize.SMALL_TOOLBAR)
        del_btn.set_tooltip_text("Delete")
        del_btn.set_relief(Gtk.ReliefStyle.NONE)
        del_btn.connect("clicked", lambda _: on_delete(cfg.id))
        hbox.pack_start(del_btn, False, False, 0)

        self.add(hbox)
        self.show_all()


# ---------------------------------------------------------------------------
# Tab
# ---------------------------------------------------------------------------

class PostProcessingTab(Gtk.Box):
    """Notebook tab for managing the post-processor pipeline."""

    def __init__(self, registry: PostProcessorRegistry, app_config: Config) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self._registry = registry
        self._app_config = app_config

        # Toolbar
        toolbar_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        toolbar_box.set_margin_top(12)
        toolbar_box.set_margin_bottom(8)
        toolbar_box.set_margin_start(16)
        toolbar_box.set_margin_end(16)

        title = Gtk.Label(label="Post-processors")
        title.set_xalign(0)
        title.set_hexpand(True)
        toolbar_box.pack_start(title, True, True, 0)

        add_btn = Gtk.Button(label="+ Add processor")
        add_btn.connect("clicked", self._on_add_clicked)
        toolbar_box.pack_start(add_btn, False, False, 0)

        self.pack_start(toolbar_box, False, False, 0)
        self.pack_start(Gtk.Separator(), False, False, 0)

        # Processor list
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_vexpand(True)

        self._list_box = Gtk.ListBox()
        self._list_box.set_selection_mode(Gtk.SelectionMode.NONE)
        scroll.add(self._list_box)
        self.pack_start(scroll, True, True, 0)

        # Empty-state hint
        self._empty_label = Gtk.Label(label="No post-processors yet. Click \"+ Add processor\" to create one.")
        self._empty_label.set_margin_top(32)
        self._empty_label.get_style_context().add_class("dim-label")
        self._empty_label.set_no_show_all(True)
        self.pack_start(self._empty_label, False, False, 0)

        registry.on_change(self._rebuild)
        self._rebuild(registry.get_all())

    # -- Internal -------------------------------------------------------------

    def _rebuild(self, processors: list[PostProcessorConfig]) -> None:
        self._list_box.foreach(self._list_box.remove)
        for cfg in processors:
            row = ProcessorRow(
                cfg,
                on_edit=self._on_edit,
                on_delete=self._on_delete,
                on_toggle=self._on_toggle,
            )
            self._list_box.add(row)
        if processors:
            self._empty_label.hide()
        else:
            self._empty_label.show()
        self._list_box.show_all()

    def _get_parent_window(self) -> Gtk.Window | None:
        widget = self.get_toplevel()
        return widget if isinstance(widget, Gtk.Window) else None

    def _on_add_clicked(self, _btn: Gtk.Button) -> None:
        parent = self._get_parent_window()

        chooser = ProviderChooserDialog(parent)
        if chooser.run() != Gtk.ResponseType.OK:
            chooser.destroy()
            return
        provider = chooser.get_provider()
        chooser.destroy()

        cfg = make_config(
            provider,
            icon=_PROVIDER_DEFAULT_ICONS.get(provider, "system-run-symbolic"),
        )
        dialog = ProcessorEditorDialog(parent, self._app_config, cfg)
        if dialog.run() == Gtk.ResponseType.OK:
            self._registry.add(dialog.get_result())
        dialog.destroy()

    def _on_edit(self, cfg: PostProcessorConfig) -> None:
        dialog = ProcessorEditorDialog(self._get_parent_window(), self._app_config, cfg)
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self._registry.update(dialog.get_result())
        dialog.destroy()

    def _on_delete(self, proc_id: str) -> None:
        confirm = Gtk.MessageDialog(
            transient_for=self._get_parent_window(),
            flags=Gtk.DialogFlags.MODAL,
            type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text="Delete this post-processor?",
        )
        if confirm.run() == Gtk.ResponseType.YES:
            self._registry.remove(proc_id)
        confirm.destroy()

    def _on_toggle(self, proc_id: str, enabled: bool) -> None:
        self._registry.set_enabled(proc_id, enabled)
