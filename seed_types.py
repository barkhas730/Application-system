"""
Өргөдлийн төрлүүдийг шинэчлэх скрипт.
Одоо байгаа бүх өргөдөл болон төрлүүдийг устгаж, шинэ 15 төрөл үүсгэнэ.

required_fields формат:
  [
    {
      "key":      "purpose",         # POST-д ирэх field нэр
      "label":    "Зориулалт",       # UI дээр харуулах
      "type":     "select",          # text | textarea | number | date | select | select_dynamic
      "required": true,              # илгээхэд заавал эсэх
      "options":  ["Бусад", ...]     # зөвхөн type=select үед ашиглана
    },
    ...
  ]

target_department:
  ""              → Бүх захирлууд
  "__own_dept__"  → Тухайн ажилтны хэлтэс
  "Хүний нөөцийн хэлтэс" | "Санхүүгийн хэлтэс" | ...

Ажиллуулах: python -X utf8 seed_types.py
"""
import os
import sys
import django

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from applications.models import ApplicationType, Application

# 1. Бүх өргөдлүүд устгана
deleted_apps, _ = Application.objects.all().delete()
print(f'[x] {deleted_apps} өргөдөл устгагдлаа.')

# 2. Бүх өргөдлийн төрлүүд устгана
deleted_types, _ = ApplicationType.objects.all().delete()
print(f'[x] {deleted_types} өргөдлийн төрөл устгагдлаа.\n')

# 3. Шинэ 16 өргөдлийн төрөл — монгол цагаан толгойн дарааллаар (PK 1-16)
TYPES = [
    # ── pk=1  А ─ Нийтлэг ────────────────────────────────────────────────────
    {
        'id': 1,
        'name': 'Ажилласан хугацааны тодорхойлолт авах хүсэлт',
        'target_department': 'Хүний нөөцийн хэлтэс',
        'requires_attachment': False,
        'instructions': 'Хүсэлт илгээснээс хойш 3 ажлын өдрийн дотор тодорхойлолтыг хүний нөөцийн хэлтэст ирж авна уу. Яаралтай шаардлага гарвал утсаар урьдчилан мэдэгдэнэ үү.',
        'required_fields': [
            {
                'key': 'purpose', 'label': 'Зориулалт', 'type': 'select',
                'required': True,
                'options': ['Банкны зээлд', 'Нийгмийн даатгалд', 'Байгууллагад', 'Тэтгэвэрт', 'Бусад'],
            },
            {
                'key': 'work_period', 'label': 'Ажилласан хугацаа (зааж өгөх бол)',
                'type': 'text', 'required': False, 'options': [],
            },
        ],
    },
    # ── pk=2  А ─ Хүний нөөц ─────────────────────────────────────────────────
    {
        'id': 2,
        'name': 'Ажилтны албан тушаал өөрчлөх хүсэлт',
        'target_department': 'Хүний нөөцийн хэлтэс',
        'requires_attachment': False,
        'instructions': 'Хүний нөөцийн хэлтэс хүсэлтийг хүлээн авч 5 ажлын өдрийн дотор шийдвэрлэнэ. Өөрчлөлт хүчин төгөлдөр болохоос өмнө холбогдох хэлтсийн дарга болон HR-д урьдчилан мэдэгдсэн байх шаардлагатай.',
        'required_fields': [
            {'key': 'employee_name', 'label': 'Ажилтны нэр', 'type': 'text', 'required': True, 'options': []},
            {'key': 'current_position', 'label': 'Одоогийн албан тушаал', 'type': 'text', 'required': True, 'options': []},
            {'key': 'new_position', 'label': 'Шинэ албан тушаал', 'type': 'text', 'required': True, 'options': []},
            {
                'key': 'change_type', 'label': 'Өөрчлөлтийн төрөл', 'type': 'select',
                'required': True,
                'options': ['Дэвшүүлэх', 'Шилжүүлэх', 'Бууруулах'],
            },
            {'key': 'reason', 'label': 'Шалтгаан, үндэслэл', 'type': 'textarea', 'required': True, 'options': []},
            {'key': 'effective_date', 'label': 'Хүчин төгөлдөр болох огноо', 'type': 'date', 'required': False, 'options': []},
        ],
    },
    # ── pk=3  Га ─ Удирдлага ──────────────────────────────────────────────────
    {
        'id': 3,
        'name': 'Гадаад томилолтын зөвшөөрлийн хүсэлт',
        'target_department': '',
        'requires_attachment': False,
        'instructions': 'Аялахаас дор хаяж 10 ажлын өдрийн өмнө хүсэлт илгээнэ үү. Визний хугацаа болон аялалын хуваарийг харгалзан эхлэх-дуусах огноог үнэн зөвөөр оруулна уу.',
        'required_fields': [
            {'key': 'destination_country', 'label': 'Очих улс / хот', 'type': 'text', 'required': True, 'options': []},
            {'key': 'travel_purpose', 'label': 'Зорилго', 'type': 'textarea', 'required': True, 'options': []},
            {'key': 'travel_start', 'label': 'Эхлэх огноо', 'type': 'date', 'required': True, 'options': []},
            {'key': 'travel_end', 'label': 'Дуусах огноо', 'type': 'date', 'required': True, 'options': []},
            {'key': 'organization', 'label': 'Урьсан байгууллага', 'type': 'text', 'required': False, 'options': []},
            {'key': 'estimated_cost', 'label': 'Тооцоолсон зардал (₮)', 'type': 'number', 'required': False, 'options': []},
        ],
    },
    # ── pk=4  Гэ ─ Удирдлага — гэрээний файл хавсаргана ─────────────────────
    {
        'id': 4,
        'name': 'Гэрээ батлуулах хүсэлт',
        'target_department': '',
        'requires_attachment': True,
        'instructions': 'Гэрээний эх хувийг заавал хавсаргана уу (PDF эсвэл Word). Нийлүүлэгчтэй урьдчилан тохирсон гэрээний төслийг дор хаяж 7 ажлын өдрийн өмнө ирүүлнэ үү.',
        'required_fields': [
            {
                'key': 'contract_type', 'label': 'Гэрээний төрөл', 'type': 'select',
                'required': True,
                'options': ['Ажлын гэрээ', 'Нийлүүлэлтийн гэрээ', 'Үйлчилгээний гэрээ',
                            'Түрээсийн гэрээ', 'Хамтын ажиллагааны гэрээ', 'Бусад'],
            },
            {'key': 'counterparty', 'label': 'Гэрээний нөгөө тал (байгууллага / хүн)', 'type': 'text', 'required': True, 'options': []},
            {'key': 'summary', 'label': 'Гэрээний товч агуулга', 'type': 'textarea', 'required': True, 'options': []},
            {'key': 'contract_value', 'label': 'Гэрээний дүн (₮)', 'type': 'number', 'required': False, 'options': []},
            {'key': 'contract_period', 'label': 'Гэрээний дуусах огноо', 'type': 'date', 'required': False, 'options': []},
        ],
    },
    # ── pk=5  Зар ─ Санхүү — баримт хавсаргана ──────────────────────────────
    {
        'id': 5,
        'name': 'Зардал буцаан авах хүсэлт',
        'target_department': 'Санхүүгийн хэлтэс',
        'requires_attachment': True,
        'instructions': 'Зардлын бүх баримтыг (касын баримт, нэхэмжлэл) хавсаргана уу. Зардал гарснаас хойш 14 хоногийн дотор хүсэлт илгээнэ үү — хоцорсон хүсэлтийг санхүүгийн хэлтэс хүлээн авахгүй.',
        'required_fields': [
            {
                'key': 'expense_type', 'label': 'Зардлын төрөл', 'type': 'select',
                'required': True,
                'options': ['Тээврийн зардал', 'Хоол хүнсний зардал', 'Байрны зардал',
                            'Сургалтын зардал', 'Харилцаа холбооны зардал', 'Бусад'],
            },
            {'key': 'expense_amount', 'label': 'Нийт дүн (₮)', 'type': 'number', 'required': True, 'options': []},
            {'key': 'expense_date', 'label': 'Зардлын огноо', 'type': 'date', 'required': True, 'options': []},
            {'key': 'description', 'label': 'Дэлгэрэнгүй тайлбар', 'type': 'textarea', 'required': False, 'options': []},
        ],
    },
    # ── pk=6  Зас ─ Аж ахуй ──────────────────────────────────────────────────
    {
        'id': 6,
        'name': 'Засвар үйлчилгээний хүсэлт',
        'target_department': 'Аж ахуйн хэлтэс',
        'requires_attachment': False,
        'instructions': 'Яаралтай тохиолдолд аж ахуйн хэлтэст утсаар шууд холбогдоно уу. Ердийн хүсэлтийг 3 ажлын өдрийн дотор хүлээн авч, ажлыг 7 хоногийн дотор гүйцэтгэнэ.',
        'required_fields': [
            {'key': 'location', 'label': 'Байршил / өрөөний дугаар', 'type': 'text', 'required': True, 'options': []},
            {
                'key': 'issue_type', 'label': 'Асуудлын төрөл', 'type': 'select',
                'required': True,
                'options': ['Цахилгаан', 'Дулаан', 'Ус', 'Агааржуулалт',
                            'Компьютер / Техник', 'Тавилга / Тоног', 'Бусад'],
            },
            {'key': 'description', 'label': 'Дэлгэрэнгүй тайлбар', 'type': 'textarea', 'required': True, 'options': []},
            {
                'key': 'urgency', 'label': 'Яаралтай байдал', 'type': 'select',
                'required': False,
                'options': ['Яаралтай (өнөөдөр)', 'Энэ долоо хоногт', 'Энэ сард', 'Хойшлуулж болно'],
            },
        ],
    },
    # ── pk=7  И ─ Санхүү ─────────────────────────────────────────────────────
    {
        'id': 7,
        'name': 'Илүү цаг ажилласан цалингийн хүсэлт',
        'target_department': 'Санхүүгийн хэлтэс',
        'requires_attachment': False,
        'instructions': 'Илүү цаг ажилласан сарын 25-ны дотор хүсэлт илгээнэ үү. Хоцорч ирсэн хүсэлтийг дараа сарын цалинтай хамт тооцно. Хариуцсан ажилтны баталгааг заавал авна уу.',
        'required_fields': [
            {'key': 'overtime_date', 'label': 'Илүү цаг ажилласан огноо', 'type': 'date', 'required': True, 'options': []},
            {'key': 'hours', 'label': 'Цагийн тоо', 'type': 'number', 'required': True, 'options': []},
            {'key': 'reason', 'label': 'Шалтгаан', 'type': 'textarea', 'required': True, 'options': []},
            # select_dynamic: source='dept_heads' — хэлтсийн захиралуудыг динамик ачаална
            {
                'key': 'supervisor', 'label': 'Хариуцсан ажилтан',
                'type': 'select_dynamic', 'source': 'dept_heads',
                'required': False, 'options': [],
            },
        ],
    },
    # ── pk=8  Си ─ МТ хэлтэс ─────────────────────────────────────────────────
    {
        'id': 8,
        'name': 'Системд нэвтрэх эрх авах хүсэлт',
        'target_department': 'Мэдээлэл технологийн хэлтэс',
        'requires_attachment': False,
        'instructions': 'МТ хэлтэс 2 ажлын өдрийн дотор эрхийг идэвхжүүлнэ. Системийн нэрийг үнэн зөвөөр бичнэ үү. Мэдээллийн аюулгүй байдлын бодлогын дагуу өгсөн эрхийг зөвхөн ажлын зориулалтаар ашиглана.',
        'required_fields': [
            {'key': 'system_name', 'label': 'Системийн нэр', 'type': 'text', 'required': True, 'options': []},
            {
                'key': 'access_type', 'label': 'Эрхийн төрөл', 'type': 'select',
                'required': True,
                'options': ['Харах эрх', 'Засах эрх', 'Бүтэн эрх'],
            },
            {'key': 'reason', 'label': 'Шалтгаан', 'type': 'textarea', 'required': True, 'options': []},
            {
                'key': 'duration', 'label': 'Эрхийн хугацаа', 'type': 'select',
                'required': False,
                'options': ['1 сар', '3 сар', '6 сар', '1 жил', 'Хязгааргүй'],
            },
        ],
    },
    # ── pk=9  Су ─ Нийтлэг ───────────────────────────────────────────────────
    {
        'id': 9,
        'name': 'Сургалтад хамрагдах хүсэлт',
        'target_department': 'Хүний нөөцийн хэлтэс',
        'requires_attachment': False,
        'instructions': 'Сургалт эхлэхээс дор хаяж 7 ажлын өдрийн өмнө хүсэлт илгээнэ үү. Сургалт дууссаны дараа хүний нөөцийн хэлтэст тайлан болон гэрчилгээний хуулбарыг ирүүлнэ.',
        'required_fields': [
            {'key': 'training_name', 'label': 'Сургалтын нэр', 'type': 'text', 'required': True, 'options': []},
            {'key': 'training_org', 'label': 'Зохион байгуулагч байгууллага', 'type': 'text', 'required': True, 'options': []},
            {'key': 'training_date', 'label': 'Огноо', 'type': 'date', 'required': True, 'options': []},
            {'key': 'training_cost', 'label': 'Зардал (₮)', 'type': 'number', 'required': False, 'options': []},
            {'key': 'relevance', 'label': 'Ажилд хамаарах байдал', 'type': 'textarea', 'required': False, 'options': []},
        ],
    },
    # ── pk=10  Т ─ МТ хэлтэс ─────────────────────────────────────────────────
    {
        'id': 10,
        'name': 'Тоног төхөөрөмжийн хүсэлт',
        'target_department': 'Мэдээлэл технологийн хэлтэс',
        'requires_attachment': False,
        'instructions': 'Техникийн үзүүлэлтийг аль болох нарийвчлан тайлбарлана уу. Захиалга баталгаажихаас хойш 7–14 ажлын өдөрт хүргэлт хийгдэнэ. Яаралтай шаардлага бол тусгайлан тэмдэглэнэ үү.',
        'required_fields': [
            {'key': 'item_name', 'label': 'Тоног төхөөрөмжийн нэр', 'type': 'text', 'required': True, 'options': []},
            {'key': 'quantity', 'label': 'Тоо (ширхэг)', 'type': 'number', 'required': True, 'options': []},
            {'key': 'reason', 'label': 'Авах шалтгаан', 'type': 'textarea', 'required': True, 'options': []},
            {'key': 'specs', 'label': 'Техникийн үзүүлэлт', 'type': 'textarea', 'required': False, 'options': []},
            {'key': 'estimated_cost', 'label': 'Тооцоолсон зардал (₮)', 'type': 'number', 'required': False, 'options': []},
        ],
    },
    # ── pk=11  Х ─ Аж ахуй ───────────────────────────────────────────────────
    {
        'id': 11,
        'name': 'Хангамж, материалын хүсэлт',
        'target_department': 'Аж ахуйн хэлтэс',
        'requires_attachment': False,
        'instructions': 'Хэрэгцээтэй тоо хэмжээгээ оновчтой тооцоолж бичнэ үү. Аж ахуйн хэлтэс долоо хоногт нэг удаа (мягмар гарагт) материал олгодог тул цаг тухайд нь хүсэлт илгээнэ үү.',
        'required_fields': [
            {'key': 'item_name', 'label': 'Материал / хэрэгслэлийн нэр', 'type': 'text', 'required': True, 'options': []},
            {'key': 'quantity', 'label': 'Тоо хэмжээ', 'type': 'number', 'required': True, 'options': []},
            {'key': 'purpose', 'label': 'Ашиглах зорилго', 'type': 'textarea', 'required': True, 'options': []},
            {'key': 'estimated_cost', 'label': 'Тооцоолсон зардал (₮)', 'type': 'number', 'required': False, 'options': []},
        ],
    },
    # ── pk=12  Цт ─ Нийтлэг ──────────────────────────────────────────────────
    {
        'id': 12,
        'name': 'Цалингийн тодорхойлолт авах хүсэлт',
        'target_department': 'Хүний нөөцийн хэлтэс',
        'requires_attachment': False,
        'instructions': 'Тодорхойлолт гарснаас хойш 3 ажлын өдрийн дотор хүний нөөцийн хэлтэст ирж авна уу. Хугацаа хэтрэх тохиолдолд дахин хүсэлт гаргах шаардлагатай болно.',
        'required_fields': [
            {
                'key': 'purpose', 'label': 'Зориулалт', 'type': 'select',
                'required': True,
                'options': ['Банкны зээлд', 'Нийгмийн даатгалд', 'Байгууллагад', 'Тэтгэвэрт', 'Бусад'],
            },
            {
                'key': 'language', 'label': 'Хэрэгтэй хэл', 'type': 'select',
                'required': False,
                'options': ['Монгол хэлээр', 'Англи хэлээр', 'Монгол, Англи хоёулаа'],
            },
        ],
    },
    # ── pk=13  Цу ─ Санхүү ───────────────────────────────────────────────────
    {
        'id': 13,
        'name': 'Цалингийн урьдчилгаа авах хүсэлт',
        'target_department': 'Санхүүгийн хэлтэс',
        'requires_attachment': False,
        'instructions': 'Урьдчилгааны дүн нэг сарын цалингийн 50%-иас хэтрэхгүй байна. Эргэн төлөлтийн хугацаа 6 сараас хэтрэхгүй байна. Жилд нэгээс илүү удаа хүсэлт гаргах боломжгүй.',
        'required_fields': [
            {'key': 'advance_amount', 'label': 'Урьдчилгааны дүн (₮)', 'type': 'number', 'required': True, 'options': []},
            {'key': 'reason', 'label': 'Авах шалтгаан', 'type': 'textarea', 'required': True, 'options': []},
            {'key': 'repayment_months', 'label': 'Эргэн төлөх хугацаа (сар)', 'type': 'number', 'required': True, 'options': []},
        ],
    },
    # ── pk=14  Ч ─ Нийтлэг ───────────────────────────────────────────────────
    {
        'id': 14,
        'name': 'Чөлөө авах хүсэлт',
        'target_department': '__own_dept__',
        'requires_attachment': False,
        'instructions': 'Ээлжийн амралтыг дор хаяж 5 ажлын өдрийн өмнө, бусад чөлөөний хүсэлтийг 2 ажлын өдрийн өмнө илгээнэ үү. Эмчилгээний чөлөөний хувьд буцаж ирсний дараа эмчийн тодорхойлолтыг HR-д өгнө.',
        'required_fields': [
            {
                'key': 'leave_type', 'label': 'Чөлөөний төрөл', 'type': 'select',
                'required': True,
                'options': ['Ээлжийн амралт', 'Эмчилгээний чөлөө', 'Хувийн чөлөө',
                            'Тусгай чөлөө', 'Хүүхэд асрах чөлөө'],
            },
            {'key': 'leave_start', 'label': 'Эхлэх огноо', 'type': 'date', 'required': True, 'options': []},
            {'key': 'leave_end', 'label': 'Дуусах огноо', 'type': 'date', 'required': True, 'options': []},
            {'key': 'leave_reason', 'label': 'Шалтгаан', 'type': 'textarea', 'required': True, 'options': []},
        ],
    },
    # ── pk=15  Ш ─ Хүний нөөц ────────────────────────────────────────────────
    {
        'id': 15,
        'name': 'Шинэ ажилтан авах хүсэлт',
        'target_department': 'Хүний нөөцийн хэлтэс',
        'requires_attachment': False,
        'instructions': 'Тавих шаардлага болон чадварыг нарийвчлан бичнэ үү. Ажлын зар нийтлэгдэхэд 5 ажлын өдөр шаардагдана. Байрны хуваарилалт болон техник хэрэгслийн шаардлагыг мөн урьдчилан тодорхойлно уу.',
        'required_fields': [
            {'key': 'position', 'label': 'Ажлын байрны нэр / Албан тушаал', 'type': 'text', 'required': True, 'options': []},
            {'key': 'headcount', 'label': 'Авах тоо', 'type': 'number', 'required': True, 'options': []},
            {'key': 'requirements', 'label': 'Тавих шаардлага, чадвар', 'type': 'textarea', 'required': True, 'options': []},
            {
                'key': 'work_type', 'label': 'Ажлын хэлбэр', 'type': 'select',
                'required': False,
                'options': ['Бүтэн цагийн', 'Хагас цагийн', 'Цагийн'],
            },
            {'key': 'start_date', 'label': 'Ажилд гарах хугацаа', 'type': 'date', 'required': False, 'options': []},
        ],
    },
    # ── pk=16  А ─ Хүний нөөц ── Ажлаас гарах ───────────────────────────────
    {
        'id': 16,
        'name': 'Ажлаас гарах өргөдөл',
        'target_department': 'Хүний нөөцийн хэлтэс',
        'requires_attachment': False,
        'instructions': 'Ажлаас чөлөөлөгдөх хүсэлтийг дор хаяж 30 хоногийн өмнө заавал илгээнэ үү. Хамтран ажиллагчдад ажлаа хэрхэн шилжүүлэхээ тодорхойлно уу. HR болон хэлтсийн даргатай урьдчилан ярилцсан байх нь зүйтэй.',
        'required_fields': [
            {
                'key': 'last_work_date', 'label': 'Сүүлийн ажлын өдөр',
                'type': 'date', 'required': True, 'options': [],
            },
            {
                'key': 'reason', 'label': 'Гарах шалтгаан', 'type': 'select',
                'required': True,
                'options': ['Хувийн шалтгаан', 'Өөр ажилд шилжих', 'Гэр бүлийн шалтгаан',
                            'Эрүүл мэндийн шалтгаан', 'Бусад'],
            },
            {
                'key': 'notice_period', 'label': 'Урьдчилан мэдэгдэж буй хугацаа (хоног)',
                'type': 'number', 'required': True, 'options': [],
            },
            {
                'key': 'handover_plan', 'label': 'Ажил шилжүүлэлтийн төлөвлөгөө',
                'type': 'textarea', 'required': False, 'options': [],
            },
        ],
    },
]

# ── Бүтцийг шалгах тусгай функц ───────────────────────────────────────────────
def validate_field_def(f):
    """required_fields-ийн нэг элементийн бүтцийг шалгана."""
    assert 'key' in f and f['key'], f'key байхгүй: {f}'
    assert 'label' in f and f['label'], f'label байхгүй: {f}'
    assert f.get('type') in ('text', 'textarea', 'number', 'date', 'select', 'select_dynamic'), \
        f'Буруу type: {f}'
    assert isinstance(f.get('required'), bool), f'required bool биш: {f}'
    assert isinstance(f.get('options'), list), f'options list биш: {f}'
    if f['type'] == 'select':
        assert len(f['options']) > 0, f'select type-д options хоосон байж болохгүй: {f}'

# ── Үүсгэх ────────────────────────────────────────────────────────────────────
for t in TYPES:
    # Бүтцийн шалгалт
    for fld in t['required_fields']:
        validate_field_def(fld)

    obj = ApplicationType.objects.create(
        id=t['id'],
        name=t['name'],
        description='',
        instructions=t.get('instructions', ''),
        required_fields=t['required_fields'],
        requires_attachment=t['requires_attachment'],
        target_department=t['target_department'],
        is_active=True,
    )
    attach = '  📎' if t['requires_attachment'] else ''
    dept_label = t['target_department'] or 'Бүх захирлууд'
    print(f'  [+] pk={t["id"]:2d}  {obj.name:50s}  [{dept_label}]{attach}')

print(f'\nНийт {len(TYPES)} өргөдлийн төрөл амжилттай үүсгэгдлээ (pk 1–{TYPES[-1]["id"]}).')
