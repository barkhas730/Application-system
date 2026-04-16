from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def query_update(context, **kwargs):
    """
    Одоогийн GET параметрүүдийг хэвээр үлдээж,
    зарим параметрийг солих template tag.

    Жишээ: pagination дахь 'page' параметрийг солихдоо
    бусад filter-үүдийг алдагдуулахгүй.

    Хэрэглэх: {% query_update page=2 %}
    """
    request = context['request']
    # Одоогийн GET параметрүүдийн хуулбар авна (mutable)
    params = request.GET.copy()

    # Дамжуулсан шинэ утгуудаар дарж бичнэ
    for key, value in kwargs.items():
        params[key] = value

    return params.urlencode()


@register.simple_tag(takes_context=True)
def sort_url(context, field):
    """
    Эрэмбэлэх баганы URL үүсгэх tag.
    Хэрэв одоо тэр баганаар ascending эрэмбэлж байвал descending болгоно,
    бусад тохиолдолд ascending болгоно.
    Мөн page=1 рүү буцаана.

    Хэрэглэх: {% sort_url 'status' %}
    """
    request = context['request']
    params = request.GET.copy()

    current_sort = params.get('sort', '')

    # Toggle логик: ascending -> descending, өөр -> ascending
    if current_sort == field:
        params['sort'] = '-' + field
    else:
        params['sort'] = field

    # Sort солигдоход 1-р хуудас руу буцна
    params['page'] = '1'

    return params.urlencode()
