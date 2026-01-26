from ninja.pagination import PageNumberPagination

class CustomPagination(PageNumberPagination):
    page_size = 10  # default

    def paginate_queryset(self, queryset, pagination, request, **params):
        # Let parent build the page
        page = super().paginate_queryset(queryset, pagination, request, **params)
        self._page = page
        self._pagination = pagination
        return page

    def get_paginated_response(self, items, **kwargs):
        # Some Ninja versions call with extra kwargs
        page = getattr(self, "_page", None)
        if page is None:
            # Fallback (shouldn't happen)
            return {"items": items, "count": len(items)}

        return {
            "items": items,
            "count": page.paginator.count,
            "page": page.number,
            "page_size": page.paginator.per_page,
            "total_pages": page.paginator.num_pages,
        }

