def filter_by_query(queryset, query, fields):
    if query:
        query = query.strip()
        if query:
            from django.db.models import Q

            q_obj = Q()
            for field in fields:
                q_obj |= Q(**{f"{field}__icontains": query})
            return queryset.filter(q_obj)
    return queryset
