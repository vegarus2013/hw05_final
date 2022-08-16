from django.conf import settings
from django.core.paginator import Paginator


def pagination(request, objects):
    paginator = Paginator(objects, settings.PAGE_SIZE)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return page
