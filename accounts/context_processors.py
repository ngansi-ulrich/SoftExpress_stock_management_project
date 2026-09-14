from django.db.models import F, Q


def navbar_notifications(request):
    if not request.user.is_authenticated:
        return {}

    from accounts.permissions import get_agency_scope, UNRESTRICTED
    from inventory.models import Inventory
    from transfers.models import Transfer

    scope = get_agency_scope(request.user)
    if scope is False or scope is None:
        return {'navbar_notification_count': 0, 'navbar_notification_items': []}

    inventory_qs = Inventory.objects.select_related('product', 'agency')
    transfer_qs = Transfer.objects.select_related('product', 'source_agency', 'destination_agency')

    if scope is not UNRESTRICTED:
        inventory_qs = inventory_qs.filter(agency=scope)
        transfer_qs = transfer_qs.filter(Q(source_agency=scope) | Q(destination_agency=scope))

    out_of_stock = inventory_qs.filter(quantity=0)
    low_stock = inventory_qs.filter(quantity__gt=0, quantity__lte=F('minimum_stock'))
    pending_transfers = transfer_qs.filter(status='PENDING')

    from django.urls import reverse
    items = []

    for i in out_of_stock[:3]:
        items.append({
            'icon': 'bi-x-circle', 'color': 'danger',
            'title': 'Out of stock',
            'text': f"{i.product.name}{f' ({i.agency.name})' if i.agency else ''}",
            'url': reverse('inventory_list'),
        })
    for i in low_stock[:3]:
        items.append({
            'icon': 'bi-exclamation-triangle', 'color': 'warning',
            'title': 'Low stock',
            'text': f"{i.product.name} — {i.quantity} left",
            'url': reverse('stock_alerts'),
        })
    for t in pending_transfers[:3]:
        items.append({
            'icon': 'bi-arrow-left-right', 'color': 'primary',
            'title': 'Pending transfer',
            'text': f"{t.transfer_number} ({t.source_agency.name} → {t.destination_agency.name})",
            'url': reverse('transfer_detail', kwargs={'pk': t.pk}),
        })

    total = out_of_stock.count() + low_stock.count() + pending_transfers.count()

    return {
        'navbar_notification_count': total,
        'navbar_notification_items': items[:5],
    }