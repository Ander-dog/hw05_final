from django.core.paginator import Paginator


def get_page_obj(request, post_list, page_capacity):
    paginator = Paginator(post_list, page_capacity)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)
