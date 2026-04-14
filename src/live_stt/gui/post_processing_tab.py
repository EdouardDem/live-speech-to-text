"""Post-processing tab — manage the ordered list of post-processors."""

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk  # noqa: E402

from ..post_processors.base import PostProcessorConfig
from ..post_processors import registry as provider_registry
from ..services.config import Config
from ..services import icons

# -- UI texts ----------------------------------------------------------------

_TXT_CHOOSER_TITLE = "Choose provider"
_TXT_CHOOSER_LABEL = "Select the post-processor type:"
_TXT_CHOOSER_CANCEL = "Cancel"
_TXT_CHOOSER_NEXT = "Next"

_TXT_EDITOR_TITLE_ADD = "Add processor"
_TXT_EDITOR_TITLE_EDIT = "Edit processor"
_TXT_EDITOR_CANCEL = "Cancel"
_TXT_EDITOR_SAVE = "Save"
_TXT_EDITOR_LBL_PROVIDER = "Provider"
_TXT_EDITOR_LBL_NAME = "Name"
_TXT_EDITOR_LBL_ICON = "Icon name"
_TXT_EDITOR_LBL_HOTKEY = "Hotkey (optional)"
_TXT_EDITOR_PLACEHOLDER_ICON = "e.g. accessories-text-editor-symbolic"
_TXT_EDITOR_PLACEHOLDER_HOTKEY = "e.g. <ctrl>+<shift>+t"
_TXT_EDITOR_FALLBACK_NAME = "Processor"
_TXT_EDITOR_API_KEY_WARNING = (
    '<span foreground="#e67e22">\u26a0  {label} API key not set \u2014 '
    "configure it in Settings \u2192 API Keys.</span>"
)

_TXT_ROW_TOOLTIP_EDIT = "Edit"
_TXT_ROW_TOOLTIP_DELETE = "Delete"

_TXT_TAB_TITLE = "Post-processors"
_TXT_TAB_ADD_BTN = "+ Add processor"
_TXT_TAB_EMPTY_HINT = 'No post-processors yet. Click "+ Add processor" to create one.'
_TXT_TAB_DELETE_CONFIRM = "Delete this post-processor?"


# ---------------------------------------------------------------------------
# Provider chooser dialog
# ---------------------------------------------------------------------------

class ProviderChooserDialog(Gtk.Dialog):
    """Small modal that lets the user pick a provider before editing."""

    def __init__(self, parent: Gtk.Window | None) -> None:
        super().__init__(
            title=_TXT_CHOOSER_TITLE,
            transient_for=parent,
            flags=Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
        )
        self.add_button(_TXT_CHOOSER_CANCEL, Gtk.ResponseType.CANCEL)
        ok_btn = self.add_button(_TXT_CHOOSER_NEXT, Gtk.ResponseType.OK)
        ok_btn.get_style_context().add_class("suggested-action")

        box = self.get_content_area()
        box.set_spacing(12)
        box.set_margin_top(16)
        box.set_margin_bottom(8)
        box.set_margin_start(16)
        box.set_margin_end(16)

        label = Gtk.Label(label=_TXT_CHOOSER_LABEL)
        label.set_xalign(0)
        box.pack_start(label, False, False, 0)

        provider_ids = provider_registry.get_provider_ids()
        self._combo = Gtk.ComboBoxText()
        for pid in provider_ids:
            self._combo.append(pid, provider_registry.get_provider_label(pid))
        self._combo.set_active(0)
        box.pack_start(self._combo, False, False, 0)

        self.show_all()

    def get_provider(self) -> str:
        return self._combo.get_active_id() or provider_registry.get_provider_ids()[0]


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
            title=_TXT_EDITOR_TITLE_ADD if is_new else _TXT_EDITOR_TITLE_EDIT,
            transient_for=parent,
            flags=Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
        )
        self._app_config = app_config
        self._provider = cfg.provider
        self._editing_id = cfg.id

        self.add_button(_TXT_EDITOR_CANCEL, Gtk.ResponseType.CANCEL)
        ok_btn = self.add_button(_TXT_EDITOR_SAVE, Gtk.ResponseType.OK)
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
        grid.attach(Gtk.Label(label=_TXT_EDITOR_LBL_PROVIDER, xalign=0), 0, 0, 1, 1)
        provider_label = Gtk.Label(
            label=provider_registry.get_provider_label(self._provider),
            xalign=0,
        )
        provider_label.set_hexpand(True)
        grid.attach(provider_label, 1, 0, 1, 1)

        # Name
        grid.attach(Gtk.Label(label=_TXT_EDITOR_LBL_NAME, xalign=0), 0, 1, 1, 1)
        self._name = Gtk.Entry()
        self._name.set_hexpand(True)
        self._name.set_text(cfg.name)
        grid.attach(self._name, 1, 1, 1, 1)

        # Icon
        grid.attach(Gtk.Label(label=_TXT_EDITOR_LBL_ICON, xalign=0), 0, 2, 1, 1)
        self._icon = Gtk.Entry()
        self._icon.set_hexpand(True)
        self._icon.set_placeholder_text(_TXT_EDITOR_PLACEHOLDER_ICON)
        self._icon.set_text(cfg.icon)
        grid.attach(self._icon, 1, 2, 1, 1)

        # Hotkey
        grid.attach(Gtk.Label(label=_TXT_EDITOR_LBL_HOTKEY, xalign=0), 0, 3, 1, 1)
        self._hotkey = Gtk.Entry()
        self._hotkey.set_hexpand(True)
        self._hotkey.set_placeholder_text(_TXT_EDITOR_PLACEHOLDER_HOTKEY)
        self._hotkey.set_text(cfg.hotkey)
        grid.attach(self._hotkey, 1, 3, 1, 1)

        # Provider-specific form (created by the registry)
        self._form = provider_registry.create_provider_form(self._provider)
        self._form.set_margin_top(8)
        self._form.set_margin_bottom(8)
        self._form.set_margin_start(16)
        self._form.set_margin_end(16)
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
        key_field = provider_registry.get_provider_api_key_field(self._provider)
        if not getattr(self._app_config, key_field, ""):
            label = provider_registry.get_provider_label(self._provider)
            self._warning.set_markup(
                _TXT_EDITOR_API_KEY_WARNING.format(label=label)
            )
            self._warning.show()
        else:
            self._warning.hide()

    def get_result(self) -> PostProcessorConfig:
        """Build and return the PostProcessorConfig from current form state."""
        icon = self._icon.get_text().strip()
        provider_fields = self._form.collect()

        return PostProcessorConfig(
            id=self._editing_id,
            name=self._name.get_text().strip() or _TXT_EDITOR_FALLBACK_NAME,
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

        provider_text = provider_registry.get_provider_label(cfg.provider)
        name_label = Gtk.Label(xalign=0)
        name_label.set_markup(
            f"{cfg.name}  "
            f'<span style="italic" foreground="#888888">{provider_text}</span>'
        )
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

        edit_btn = Gtk.Button.new_from_icon_name(icons.get("edit"), Gtk.IconSize.SMALL_TOOLBAR)
        edit_btn.set_tooltip_text(_TXT_ROW_TOOLTIP_EDIT)
        edit_btn.set_relief(Gtk.ReliefStyle.NONE)
        edit_btn.connect("clicked", lambda _: on_edit(cfg))
        hbox.pack_start(edit_btn, False, False, 0)

        del_btn = Gtk.Button.new_from_icon_name(icons.get("delete"), Gtk.IconSize.SMALL_TOOLBAR)
        del_btn.set_tooltip_text(_TXT_ROW_TOOLTIP_DELETE)
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

    def __init__(self, registry: provider_registry.PostProcessorRegistry, app_config: Config) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self._registry = registry
        self._app_config = app_config

        # Toolbar
        toolbar_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        toolbar_box.set_margin_top(12)
        toolbar_box.set_margin_bottom(8)
        toolbar_box.set_margin_start(16)
        toolbar_box.set_margin_end(16)

        title = Gtk.Label(label=_TXT_TAB_TITLE)
        title.set_xalign(0)
        title.set_hexpand(True)
        toolbar_box.pack_start(title, True, True, 0)

        add_btn = Gtk.Button(label=_TXT_TAB_ADD_BTN)
        add_btn.connect("clicked", self._on_add_clicked)
        toolbar_box.pack_start(add_btn, False, False, 0)

        self.pack_start(toolbar_box, False, False, 0)
        self.pack_start(Gtk.Separator(), False, False, 0)

        # Empty-state hint
        self._empty_label = Gtk.Label(label=_TXT_TAB_EMPTY_HINT)
        self._empty_label.set_margin_top(16)
        self._empty_label.get_style_context().add_class("dim-label")
        self._empty_label.set_no_show_all(True)
        self.pack_start(self._empty_label, False, False, 0)

        # Processor list
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_vexpand(True)

        self._list_box = Gtk.ListBox()
        self._list_box.set_selection_mode(Gtk.SelectionMode.NONE)
        scroll.add(self._list_box)
        self.pack_start(scroll, True, True, 0)

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

        cfg = provider_registry.make_config(provider)
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
            text=_TXT_TAB_DELETE_CONFIRM,
        )
        if confirm.run() == Gtk.ResponseType.YES:
            self._registry.remove(proc_id)
        confirm.destroy()

    def _on_toggle(self, proc_id: str, enabled: bool) -> None:
        self._registry.set_enabled(proc_id, enabled)
