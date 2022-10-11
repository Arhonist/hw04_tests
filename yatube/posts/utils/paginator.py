from django.core.paginator import Paginator


def get_page_obj(request, post_list, posts_displayed: int):
    paginator = Paginator(post_list, posts_displayed)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)
