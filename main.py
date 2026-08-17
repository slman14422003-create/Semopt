# -*- coding: utf-8 -*-
"""
AST-2012A Clinical Master — تطبيق أندرويد أصلي (Python/Kivy/KivyMD)
لا يعتمد على WebView أو TWA أو Chrome إطلاقًا؛ تطبيق مستقل حقيقي.
"""

import webbrowser
from urllib.parse import quote

from kivy.app import App
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.properties import StringProperty, BooleanProperty
from kivy.uix.screenmanager import Screen, ScreenManager, SlideTransition
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton, MDRaisedButton

import data_manager as dm
import notifications as notif


# ---------------------------------------------------------------------------
# مكوّنات مساعدة قابلة لإعادة الاستخدام
# ---------------------------------------------------------------------------

class ResultCard(MDCard):
    """بطاقة نتيجة بحث/حالة - تُبنى بالكامل من الكود لعرض عنوان الحالة."""

    def __init__(self, title, on_release=None, **kwargs):
        super().__init__(
            orientation="vertical",
            padding=(16, 12),
            size_hint_y=None,
            height=72,
            radius=[14],
            elevation=1,
            ripple_behavior=True,
            md_bg_color=(0.11, 0.13, 0.17, 1),
            **kwargs,
        )
        self.add_widget(
            MDLabel(
                text=title,
                halign="right",
                theme_text_color="Custom",
                text_color=(0.9, 0.93, 0.96, 1),
                font_style="Subtitle1",
            )
        )
        if on_release:
            self.bind(on_release=lambda *_: on_release())
        self.on_release_callback = on_release

    def on_touch_up(self, touch):
        if self.collide_point(*touch.pos) and self.on_release_callback:
            self.on_release_callback()
        return super().on_touch_up(touch)


def section_label(text):
    return MDLabel(
        text=text,
        halign="right",
        theme_text_color="Custom",
        text_color=(0.55, 0.6, 0.68, 1),
        font_style="Caption",
        size_hint_y=None,
        height=28,
    )


def field_row(label, value):
    box = MDBoxLayout(orientation="vertical", size_hint_y=None, padding=(0, 4))
    box.add_widget(
        MDLabel(text=f"[b]{label}[/b]", markup=True, halign="right",
                theme_text_color="Custom", text_color=(0.4, 0.85, 0.95, 1),
                size_hint_y=None, height=24)
    )
    lbl = MDLabel(text=value or "-", halign="right", theme_text_color="Custom",
                  text_color=(0.9, 0.93, 0.96, 1))
    lbl.bind(texture_size=lambda inst, val: setattr(inst, "height", val[1]))
    box.add_widget(lbl)
    box.bind(minimum_height=box.setter("height"))
    return box


# ---------------------------------------------------------------------------
# الشاشة الرئيسية: البحث
# ---------------------------------------------------------------------------

class HomeScreen(Screen):
    def do_search(self, query):
        results_box = self.ids.results_box
        results_box.clear_widgets()

        if not query.strip():
            results_box.add_widget(
                MDLabel(
                    text="المنظومة السريرية الضخمة جاهزة الآن.\n"
                         "ابحث عن أي حالة، نمط، أو مشكلة تقنية للحصول على التوصيف الدقيق.",
                    halign="center",
                    theme_text_color="Custom",
                    text_color=(0.55, 0.6, 0.68, 1),
                    size_hint_y=None,
                    height=120,
                )
            )
            return

        matched, is_fallback = dm.search(query)

        if not matched:
            results_box.add_widget(
                MDLabel(
                    text="لم يتم العثور على نتيجة مطابقة. جرّب صياغة أخرى.",
                    halign="center",
                    theme_text_color="Custom",
                    text_color=(0.9, 0.5, 0.5, 1),
                    size_hint_y=None,
                    height=80,
                )
            )
            return

        note = (
            "✅ تم العثور على البروتوكول الصحيح المطابق لبحثك."
            if len(matched) == 1
            else "⚠️ يوجد أكثر من بروتوكول بنفس درجة التطابق، حدد الحالة بدقة أكبر."
        )
        results_box.add_widget(
            MDLabel(text=note, halign="center", theme_text_color="Custom",
                    text_color=(0.5, 0.85, 0.55, 1), size_hint_y=None, height=36)
        )

        for item in matched:
            card = ResultCard(
                title=item["title"],
                on_release=lambda it=item: self.open_detail(it),
            )
            results_box.add_widget(card)

    def open_detail(self, item):
        app = MDApp.get_running_app()
        detail_screen = app.root.get_screen("detail")
        detail_screen.load_case(item)
        app.root.transition = SlideTransition(direction="left")
        app.root.current = "detail"

    def go_add_case(self):
        app = MDApp.get_running_app()
        add_screen = app.root.get_screen("add_edit")
        add_screen.load_for_add()
        app.root.transition = SlideTransition(direction="up")
        app.root.current = "add_edit"

    def go(self, screen_name):
        app = MDApp.get_running_app()
        app.root.transition = SlideTransition(direction="left")
        app.root.current = screen_name
        if screen_name == "my_cases":
            app.root.get_screen("my_cases").refresh()
        elif screen_name == "encyclopedia":
            app.root.get_screen("encyclopedia").populate()


# ---------------------------------------------------------------------------
# شاشة تفاصيل الحالة
# ---------------------------------------------------------------------------

class CaseDetailScreen(Screen):
    current_case = None

    def load_case(self, item):
        self.current_case = item
        box = self.ids.detail_box
        box.clear_widgets()

        box.add_widget(
            MDLabel(text=item["title"], halign="right", theme_text_color="Custom",
                    text_color=(1, 1, 1, 1), font_style="H6",
                    size_hint_y=None, height=64)
        )

        for label, key in [
            ("النمط", "mode"), ("التردد", "freq"), ("القناة", "channel"),
            ("المدة", "duration"),
        ]:
            if item.get(key):
                box.add_widget(field_row(label, item.get(key)))

        poles = item.get("poles") or []
        if poles:
            box.add_widget(field_row("الأقطاب", "\n".join(poles)))

        if item.get("explanation"):
            box.add_widget(field_row("الشرح الإكلينيكي", item["explanation"]))
        if item.get("symptoms"):
            box.add_widget(field_row("الأعراض", item["symptoms"]))
        if item.get("sessionsPlan"):
            box.add_widget(field_row("خطة الجلسات", item["sessionsPlan"]))
        if item.get("tip"):
            box.add_widget(field_row("نصيحة", item["tip"]))

        safety_notes = dm.get_general_safety_note(item.get("mode", ""))
        if safety_notes:
            box.add_widget(field_row("⚠️ ملاحظات سلامة عامة", "\n".join(f"• {n}" for n in safety_notes)))

        term = dm.extract_english_term(item["title"]) if item["title"].startswith("بروتوكول") else None
        if term:
            btn = MDRaisedButton(
                text="🔗 مصادر طبية موثوقة (Physiopedia / PubMed)",
                size_hint_y=None, height=48,
                on_release=lambda *_: self.open_sources(term),
            )
            box.add_widget(btn)

        is_custom = item.get("custom")
        actions = MDBoxLayout(size_hint_y=None, height=48, spacing=12, padding=(0, 12))
        if is_custom:
            actions.add_widget(MDRaisedButton(text="✏️ تعديل", on_release=lambda *_: self.edit_case()))
            actions.add_widget(MDFlatButton(text="🗑️ حذف", on_release=lambda *_: self.confirm_delete()))
        box.add_widget(actions)

    def open_sources(self, term):
        q = quote(term)
        try:
            webbrowser.open(f"https://www.physio-pedia.com/index.php?search={q}")
        except Exception as e:
            print(f"تعذر فتح الرابط: {e}")

    def edit_case(self):
        app = MDApp.get_running_app()
        add_screen = app.root.get_screen("add_edit")
        add_screen.load_for_edit(self.current_case)
        app.root.transition = SlideTransition(direction="up")
        app.root.current = "add_edit"

    def confirm_delete(self):
        self.dialog = MDDialog(
            title="تأكيد الحذف",
            text=f"هل تريد حذف \"{self.current_case['title']}\" نهائيًا؟",
            buttons=[
                MDFlatButton(text="إلغاء", on_release=lambda *_: self.dialog.dismiss()),
                MDRaisedButton(text="حذف", md_bg_color=(0.85, 0.3, 0.3, 1),
                               on_release=lambda *_: self.do_delete()),
            ],
        )
        self.dialog.open()

    def do_delete(self):
        dm.delete_custom_case(self.current_case["id"])
        self.dialog.dismiss()
        app = MDApp.get_running_app()
        app.root.current = "home"

    def go_back(self):
        app = MDApp.get_running_app()
        app.root.transition = SlideTransition(direction="right")
        app.root.current = "home"


# ---------------------------------------------------------------------------
# شاشة إضافة/تعديل حالة (تصلح "زر ال+" بواجهة كاملة مخصصة، وتدعم التعديل)
# ---------------------------------------------------------------------------

class AddEditCaseScreen(Screen):
    editing_case_id = StringProperty("", allownone=True)

    def load_for_add(self):
        self.editing_case_id = None
        self.ids.screen_title.text = "➕ إضافة حالة جديدة"
        self.ids.submit_btn.text = "💾 حفظ الحالة"
        for field_id in self._field_ids():
            self.ids[field_id].text = ""

    def load_for_edit(self, item):
        self.editing_case_id = item["id"]
        self.ids.screen_title.text = "✏️ تعديل الحالة"
        self.ids.submit_btn.text = "💾 حفظ التعديلات"

        self.ids.f_keywords.text = ", ".join(item.get("keywords", []))
        self.ids.f_title.text = item.get("title", "")
        self.ids.f_mode.text = item.get("mode", "")
        self.ids.f_freq.text = item.get("freq", "")
        self.ids.f_channel.text = item.get("channel", "")
        self.ids.f_duration.text = item.get("duration", "")
        poles = item.get("poles") or []
        self.ids.f_pole_pos.text = poles[0] if len(poles) > 0 else ""
        self.ids.f_pole_neg.text = poles[1] if len(poles) > 1 else ""
        self.ids.f_explanation.text = item.get("explanation", "")
        self.ids.f_symptoms.text = item.get("symptoms", "")
        self.ids.f_sessions_plan.text = item.get("sessionsPlan", "")
        self.ids.f_tip.text = item.get("tip", "")

    def _field_ids(self):
        return [
            "f_keywords", "f_title", "f_mode", "f_freq", "f_channel", "f_duration",
            "f_pole_pos", "f_pole_neg", "f_explanation", "f_symptoms",
            "f_sessions_plan", "f_tip",
        ]

    def submit(self):
        title = self.ids.f_title.text.strip()
        mode = self.ids.f_mode.text.strip()
        explanation = self.ids.f_explanation.text.strip()
        keywords_raw = self.ids.f_keywords.text.strip()

        if not title or not mode or not explanation or not keywords_raw:
            self._toast_error("العنوان، النمط، الشرح، والكلمات المفتاحية حقول إلزامية.")
            return

        keywords = [k.strip() for k in keywords_raw.split(",") if k.strip()]
        pole_pos = self.ids.f_pole_pos.text.strip()
        pole_neg = self.ids.f_pole_neg.text.strip()
        poles = [pole_pos] if pole_pos and not pole_neg else ([pole_pos, pole_neg] if pole_pos else [])

        fields = {
            "keywords": keywords,
            "title": title,
            "mode": mode,
            "freq": self.ids.f_freq.text.strip(),
            "channel": self.ids.f_channel.text.strip() or "القناتين 1 و 2",
            "duration": self.ids.f_duration.text.strip() or "20-30 دقيقة",
            "poles": poles,
            "explanation": explanation,
        }
        if self.ids.f_symptoms.text.strip():
            fields["symptoms"] = self.ids.f_symptoms.text.strip()
        if self.ids.f_sessions_plan.text.strip():
            fields["sessionsPlan"] = self.ids.f_sessions_plan.text.strip()
        if self.ids.f_tip.text.strip():
            fields["tip"] = self.ids.f_tip.text.strip()

        if self.editing_case_id:
            dm.update_custom_case(self.editing_case_id, fields)
        else:
            dm.add_custom_case(fields)

        app = MDApp.get_running_app()
        app.root.transition = SlideTransition(direction="down")
        app.root.current = "home"
        app.root.get_screen("home").ids.search_field.text = ""

    def _toast_error(self, msg):
        try:
            from kivymd.toast import toast
            toast(msg)
        except Exception:
            print(msg)

    def cancel(self):
        app = MDApp.get_running_app()
        app.root.transition = SlideTransition(direction="down")
        app.root.current = "home"


# ---------------------------------------------------------------------------
# شاشة "حالاتي" - إدارة الحالات المخصصة
# ---------------------------------------------------------------------------

class MyCasesScreen(Screen):
    def refresh(self):
        box = self.ids.cases_box
        box.clear_widgets()
        cases = dm.load_custom_cases()

        if not cases:
            box.add_widget(
                MDLabel(text="لا توجد حالات مخصصة بعد. اضغط + من الشاشة الرئيسية لإضافة أول حالة.",
                        halign="center", theme_text_color="Custom",
                        text_color=(0.55, 0.6, 0.68, 1), size_hint_y=None, height=80)
            )
            return

        for c in cases:
            row = MDBoxLayout(size_hint_y=None, height=64, spacing=8, padding=(8, 8))
            row.add_widget(MDLabel(text=c["title"], halign="right",
                                    theme_text_color="Custom", text_color=(0.9, 0.93, 0.96, 1)))
            row.add_widget(MDFlatButton(text="تعديل", on_release=lambda *_, c=c: self.edit(c)))
            row.add_widget(MDFlatButton(text="حذف", theme_text_color="Custom",
                                         text_color=(0.9, 0.4, 0.4, 1),
                                         on_release=lambda *_, c=c: self.delete(c)))
            box.add_widget(row)

    def edit(self, case):
        app = MDApp.get_running_app()
        add_screen = app.root.get_screen("add_edit")
        add_screen.load_for_edit(case)
        app.root.transition = SlideTransition(direction="up")
        app.root.current = "add_edit"

    def delete(self, case):
        dm.delete_custom_case(case["id"])
        self.refresh()

    def go_back(self):
        app = MDApp.get_running_app()
        app.root.transition = SlideTransition(direction="right")
        app.root.current = "home"


# ---------------------------------------------------------------------------
# شاشة موسوعة الأنماط
# ---------------------------------------------------------------------------

class EncyclopediaScreen(Screen):
    def populate(self):
        box = self.ids.modes_box
        box.clear_widgets()
        for m in dm.load_modes_encyclopedia():
            card = MDCard(orientation="vertical", padding=14, size_hint_y=None,
                           height=100, radius=[12], md_bg_color=(0.11, 0.13, 0.17, 1))
            card.add_widget(MDLabel(text=m.get("name", m.get("title", "")), halign="right",
                                     theme_text_color="Custom", text_color=(1, 1, 1, 1),
                                     font_style="Subtitle1", size_hint_y=None, height=28))
            desc = m.get("description", m.get("explanation", ""))
            card.add_widget(MDLabel(text=desc, halign="right", theme_text_color="Custom",
                                     text_color=(0.8, 0.83, 0.87, 1)))
            box.add_widget(card)

    def go_back(self):
        app = MDApp.get_running_app()
        app.root.transition = SlideTransition(direction="right")
        app.root.current = "home"


# ---------------------------------------------------------------------------
# شاشة الإعدادات (إشعارات حقيقية، تصدير/استيراد، حول)
# ---------------------------------------------------------------------------

class SettingsScreen(Screen):
    notif_status_text = StringProperty("")

    def on_pre_enter(self, *args):
        self.refresh_notif_label()

    def refresh_notif_label(self):
        enabled = notif.is_enabled()
        self.ids.notif_status.text = "🔔 الإشعارات مُفعّلة - اضغط لإرسال إشعار تجريبي" if enabled \
            else "🔕 الإشعارات غير مفعّلة - اضغط للتفعيل"

    def toggle_notifications(self):
        notif.request_permission()
        was_enabled = notif.is_enabled()
        if not was_enabled:
            notif.set_enabled(True)
        ok = notif.send(
            "AST-2012A Clinical Master",
            "✅ الإشعارات تعمل بنجاح - هذا إشعار حقيقي من التطبيق نفسه.",
        )
        if not ok:
            notif.set_enabled(False)
        self.refresh_notif_label()

    def export_backup(self):
        import json
        cases = dm.load_custom_cases()
        path = f"{dm.APP_DATA_DIR}/backup_export.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(cases, f, ensure_ascii=False, indent=2)
        self._toast(f"تم الحفظ في: {path}")

    def clear_all(self):
        self.dialog = MDDialog(
            title="تأكيد",
            text="سيتم حذف كل الحالات المخصصة نهائيًا. متأكد؟",
            buttons=[
                MDFlatButton(text="إلغاء", on_release=lambda *_: self.dialog.dismiss()),
                MDRaisedButton(text="مسح الكل", md_bg_color=(0.85, 0.3, 0.3, 1),
                               on_release=lambda *_: self._do_clear()),
            ],
        )
        self.dialog.open()

    def _do_clear(self):
        dm.clear_all_custom_cases()
        self.dialog.dismiss()
        self._toast("تم مسح كل الحالات المخصصة.")

    def _toast(self, msg):
        try:
            from kivymd.toast import toast
            toast(msg)
        except Exception:
            print(msg)

    def go_back(self):
        app = MDApp.get_running_app()
        app.root.transition = SlideTransition(direction="right")
        app.root.current = "home"


# ---------------------------------------------------------------------------
# التطبيق
# ---------------------------------------------------------------------------

class RootManager(ScreenManager):
    pass


class ClinicalMasterApp(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Cyan"
        self.title = "AST-2012A Clinical Master"
        Window.softinput_mode = "below_target"

        dm.init_paths()

        return Builder.load_file("main.kv")

    def on_start(self):
        self.root.get_screen("home").do_search("")


if __name__ == "__main__":
    ClinicalMasterApp().run()
