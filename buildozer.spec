[app]

title = AST-2012A Clinical Master
package.name = clinicalmaster
package.domain = com.ast2012a

source.dir = .
source.include_exts = py,png,jpg,kv,json,ttf
source.include_patterns = data/*.json

version = 1.0.0

# نُثبّت إصدار بايثون المستهدف صراحة على 3.11 (نسخة مستقرة ومُختبرة جيدًا
# مع Kivy/KivyMD)، بدل ترك python-for-android يختار أحدث نسخة بايثون
# (اللي وصلت الآن 3.14 وهي حديثة جدًا وتفشل غالبًا أثناء البناء من
# المصدر على أدوات/رؤوس تطوير النظام المتاحة على GitHub Actions).
# ملاحظة مهمة: لازم نُثبّت hostpython3 (أداة البناء) بنفس رقم إصدار
# python3 (المكتبة المُضمَّنة داخل التطبيق) بالظبط، وإلا يرفض p4a
# البناء برسالة "python3 should have same version as hostpython3".
requirements = python3==3.11.8,hostpython3==3.11.8,kivy==2.3.0,kivymd==1.2.0,plyer,pillow

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
# log_level=1 (معلومات عادية) بدل 2 (تفصيلي/Debug) - يقلل كثيرًا الأسطر
# المتكررة زي نسخ كل ملف من مكتبة بايثون القياسية سطر سطر أثناء بناء
# hostpython3، واللي كانت بتبان وكأنها "تعليق لا نهائي". أي خطأ فعلي
# ([ERROR]) بيظهر دايمًا بغض النظر عن هذا الإعداد.
log_level = 1
warn_on_root = 1
