# -*- coding: utf-8 -*-
"""
طبقة الإشعارات: تُظهر إشعار حقيقي منسوب للتطبيق نفسه على أندرويد (وليس
لمتصفح Chrome، لأن هذا تطبيق أندرويد أصلي مبني بـ Python/Kivy وليس TWA/
WebView إطلاقًا). تتعامل بأمان مع الأذونات المرفوضة أو غياب الدعم.
"""

import json
import os

_PREF_FILE_NAME = "notif_pref.json"


def _pref_path():
    from kivy.app import App
    app = App.get_running_app()
    base = app.user_data_dir if app else "."
    return os.path.join(base, _PREF_FILE_NAME)


def is_enabled():
    try:
        with open(_pref_path(), encoding="utf-8") as f:
            return json.load(f).get("enabled", False)
    except (OSError, json.JSONDecodeError):
        return False


def set_enabled(value):
    try:
        with open(_pref_path(), "w", encoding="utf-8") as f:
            json.dump({"enabled": bool(value)}, f)
    except OSError:
        pass


def request_permission():
    """يطلب صلاحية الإشعارات على أندرويد 13+ (POST_NOTIFICATIONS)."""
    try:
        from android.permissions import Permission, request_permissions  # noqa
        request_permissions([Permission.POST_NOTIFICATIONS])
        return True
    except Exception:
        # مش على أندرويد (تجربة على سطح المكتب مثلاً) - نعتبرها متاحة
        return True


def send(title, message):
    """يرسل إشعار فوري. يرجع True عند النجاح، False عند الفشل."""
    try:
        from plyer import notification
        notification.notify(title=title, message=message, timeout=6)
        return True
    except Exception as e:
        print(f"[notifications] فشل إرسال الإشعار: {e}")
        return False
