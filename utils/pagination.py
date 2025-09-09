from rest_framework.pagination import PageNumberPagination

class CustomPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    # 强制返回分页结构，即使数据不足一页
    def paginate_queryset(self, queryset, request, view=None):
        return super().paginate_queryset(queryset, request, view)