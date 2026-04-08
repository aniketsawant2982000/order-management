# core/pagination.py
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class ProductPagination(PageNumberPagination):
    page_size = 6                      # default products per page
    page_size_query_param = 'page_size'  # allow ?page_size=12 in URL
    max_page_size = 50                 # never return more than 50 at once

    def get_paginated_response(self, data):
        return Response({
            'total': self.page.paginator.count,       # total products
            'pages': self.page.paginator.num_pages,   # total pages
            'current_page': self.page.number,         # current page number
            'next': self.get_next_link(),             # URL for next page
            'previous': self.get_previous_link(),     # URL for previous page
            'results': data                           # actual products
        })