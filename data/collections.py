MINIO_BASE_URL = "http://localhost:9000/craft-resource-media"

STATUS_DRAFT = "черновик"
STATUS_PUBLISHED = "опубликован"
STATUS_DELETED = "удален"

craft_resources = [
    {
        "id": 1,
        "resource_name": "Каменная кладка",
        "resource_category": "работы",
        "measure_unit": "человеко-день",
        "historical_price": 117,
        "price_currency": "коп.",
        "base_year": 1880,
        "resource_description": (
            "Поденная плата каменщику по ведомостям справочных цен Санкт-Петербурга. "
            "В смете умножается на число человеко-дней, затраченных на кладку стен и сводов."
        ),
        "image_key": "masonry.jpg",
        "video_key": "masonry.mp4",
        "resource_status": STATUS_PUBLISHED,
        "liked_by": [3, 7, 11, 12, 18],
    },
    {
        "id": 2,
        "resource_name": "Малярные работы",
        "resource_category": "работы",
        "measure_unit": "человеко-день",
        "historical_price": 130,
        "price_currency": "коп.",
        "base_year": 1880,
        "resource_description": (
            "Поденная плата маляру. Самая дорогая из отделочных работ в справочнике: "
            "окраска фасада требовала лесов и подготовки поверхности."
        ),
        "image_key": "painting.jpg",
        "video_key": "painting.mp4",
        "resource_status": STATUS_PUBLISHED,
        "liked_by": [7, 18],
    },
    {
        "id": 3,
        "resource_name": "Плотничные работы",
        "resource_category": "работы",
        "measure_unit": "человеко-день",
        "historical_price": 128,
        "price_currency": "коп.",
        "base_year": 1880,
        "resource_description": (
            "Поденная плата плотнику. Учитывается при расчёте стропил, лесов, "
            "перекрытий и временных построек на площадке."
        ),
        "image_key": "carpentry.jpg",
        "video_key": "carpentry.mp4",
        "resource_status": STATUS_PUBLISHED,
        "liked_by": [1, 4, 9, 15],
    },
    {
        "id": 4,
        "resource_name": "Слесарные работы",
        "resource_category": "работы",
        "measure_unit": "человеко-день",
        "historical_price": 148,
        "price_currency": "коп.",
        "base_year": 1880,
        "resource_description": (
            "Поденная плата слесарю, самая высокая расценка в справочнике. "
            "Кованые связи, решётки и оконные приборы считались квалифицированной работой."
        ),
        "image_key": "metalwork.jpg",
        "video_key": "metalwork.mp4",
        "resource_status": STATUS_PUBLISHED,
        "liked_by": [2, 5, 8, 13, 17, 21],
    },
    {
        "id": 5,
        "resource_name": "Столярные работы",
        "resource_category": "работы",
        "measure_unit": "человеко-день",
        "historical_price": 121,
        "price_currency": "коп.",
        "base_year": 1880,
        "resource_description": (
            "Поденная плата столяру. Двери, оконные переплёты, резьба и иконостасы "
            "считались по этой расценке отдельно от плотничных работ."
        ),
        "image_key": "joinery.jpg",
        "video_key": "joinery.mp4",
        "resource_status": STATUS_PUBLISHED,
        "liked_by": [6, 10, 14],
    },
    {
        "id": 6,
        "resource_name": "Штукатурные работы",
        "resource_category": "работы",
        "measure_unit": "человеко-день",
        "historical_price": 111,
        "price_currency": "коп.",
        "base_year": 1880,
        "resource_description": (
            "Поденная плата штукатуру. Расценка покрывает и вытяжку карнизов, "
            "и лепной декор фасада по готовым формам."
        ),
        "image_key": "plastering.jpg",
        "video_key": "plastering.mp4",
        "resource_status": STATUS_PUBLISHED,
        "liked_by": [19],
    },
    {
        "id": 7,
        "resource_name": "Подсобные работы",
        "resource_category": "работы",
        "measure_unit": "человеко-день",
        "historical_price": 79,
        "price_currency": "коп.",
        "base_year": 1880,
        "resource_description": (
            "Поденная плата чернорабочему, нижняя граница расценок. "
            "Замес раствора, подноска кирпича и разборка лесов считаются по ней."
        ),
        "image_key": "labouring.jpg",
        "video_key": "labouring.mp4",
        "resource_status": STATUS_PUBLISHED,
        "liked_by": [16, 20],
    },
    {
        "id": 8,
        "resource_name": "Кирпич",
        "resource_category": "материалы",
        "measure_unit": "100 штук",
        "historical_price": 200,
        "price_currency": "коп. серебром",
        "base_year": 1861,
        "resource_description": (
            "Розничная цена московского кирпича по изданию 1861 года: двадцать рублей "
            "серебром за тысячу, то есть два рубля за сотню. Год и валюта отличаются от расценок на работы, "
            "поэтому в модели хранятся отдельными полями."
        ),
        "image_key": "brick.jpg",
        "video_key": "brick.mp4",
        "resource_status": STATUS_PUBLISHED,
        "liked_by": [1, 2, 3, 9, 11, 14, 22],
    },
    {
        "id": 9,
        "resource_name": "Известь",
        "resource_category": "материалы",
        "measure_unit": "бочка",
        "historical_price": None,
        "price_currency": "коп.",
        "base_year": 1890,
        "resource_description": (
            "Вяжущее для кладочного раствора и побелки. Позиция заведена, "
            "но цена по источнику пока не подтверждена, поэтому остаётся черновиком."
        ),
        "image_key": "lime.jpg",
        "video_key": "lime.mp4",
        "resource_status": STATUS_DRAFT,
        "liked_by": [],
    },
    {
        "id": 10,
        "resource_name": "Кровельные работы",
        "resource_category": "работы",
        "measure_unit": "человеко-день",
        "historical_price": None,
        "price_currency": "коп.",
        "base_year": 1880,
        "resource_description": (
            "Позиция исключена из справочника: в ведомостях справочных цен "
            "Санкт-Петербурга кровельщик отдельной строкой не значится."
        ),
        "image_key": "roofing.jpg",
        "video_key": "roofing.mp4",
        "resource_status": STATUS_DELETED,
        "liked_by": [],
    },
]
