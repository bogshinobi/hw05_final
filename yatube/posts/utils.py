from django.conf import settings
from django.core.paginator import Paginator


def page_context(request, queryset):
    paginator = Paginator(queryset, settings.POST_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
    }
    return context
