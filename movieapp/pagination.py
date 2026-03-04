from rest_framework.pagination import PageNumberPagination

class MoviePagination(PageNumberPagination):
    page_size = 10              # 10 records per page
    page_size_query_param = None
    max_page_size = 100000