[app]

title = AST-2012A Clinical Master
package.name = clinicalmaster
package.domain = com.ast2012a

source.dir = .
source.include_exts = py,png,jpg,kv,json,ttf
source.include_patterns = data/*.json

version = 1.0.0

requirements = python3,kivy==2.3.0,kivymd==1.2.0,plyer,pillow

icon.filename = %(source.dir)s/assets/icon.png
presplash.filename = %(source.dir)s/assets/presplash.png

orientation = portrait
fullscreen = 0

# أذونات أندرويد: الإشعارات الحقيقية + الاهتزاز عند الإشعار + فتح روابط
# المصادر الطبية الموثوقة في المتصفح (Intent خارجي عادي، مش WebView داخل التطبيق)
android.permissions = POST_NOTIFICATIONS,VIBRATE,INTERNET

android.api = 33
android.minapi = 24
android.ndk_api = 24
android.archs = arm64-v8a,armeabi-v7a

android.allow_backup = True

[buildozer]
log_level = 2
warn_on_root = 1
