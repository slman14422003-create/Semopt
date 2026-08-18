[app]

title = AST-2012A Clinical Master
package.name = clinicalmaster
package.domain = com.ast2012a

source.dir = .
source.include_exts = py,png,jpg,kv,json,ttf
source.include_patterns = data/*.json

version = 1.0.0

# لا نُثبّت رقم إصدار بايثون يدويًا هنا - نعتمد على الإصدار الافتراضي
# المتوافق تلقائيًا بين python3 و hostpython3 داخل نسخة python-for-android
# المُثبّتة (2024.1.21 - آخر إصدار مستقر ومتّسق على PyPI، راجع ملاحظة
# مهمة في .github/workflows/build-apk.yml حول سبب تثبيت هذا الإصدار
# تحديدًا بدل الاعتماد على أحدث نسخة تطوير غير مستقرة).
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
# معمارية واحدة فقط (arm64-v8a) - تغطي كل أجهزة الأندرويد الحديثة تقريبًا
# (من 2019 تقريبًا وما بعدها). بناء معماريتين معًا (arm64-v8a +
# armeabi-v7a) يضاعف وقت البناء لأن python-for-android يبني hostpython3
# كاملة من الصفر لكل معمارية على حدة - وهذا ما كان يبدو وكأنه "تعليق"
# لا نهائي أثناء نسخ ملفات مكتبة بايثون القياسية واحدًا تلو الآخر.
android.archs = arm64-v8a

android.allow_backup = True

[buildozer]
# log_level=2 مطلوب هنا فعليًا: من غيره Buildozer بيخفي رسالة الخطأ
# الحقيقية عند الفشل (زي ما حصل بالظبط - ظهرت رسالة عامة "raise log_level
# to 2" بدل السبب الفعلي). الأسطر الكتيرة اللي بتتكرر أثناء البناء (نسخ
# ملفات مكتبة بايثون مثلاً) عادية تمامًا وليست خطأ - الخطأ الحقيقي دايمًا
# بيبان بوضوح في سطر يبدأ بـ [ERROR] أو مكتوب فيه "failed"/"Traceback".
log_level = 2
warn_on_root = 1
