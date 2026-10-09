from django.contrib import admin
from .models import Order, OrderItem, Perfume, PageVisit


@admin.register(Perfume)
class PerfumeAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'show_in_carousel', 'created_at')
    list_filter = ('show_in_carousel',)
    search_fields = ('name', 'description')


class OrderItemInline(admin.TabularInline):
    """Perfume lines inside a cart order. Staff pick a perfume and a
    quantity; the name/price snapshot is filled in automatically on save
    (see OrderAdmin.save_formset), so perfume_name/unit_price are not
    editable fields here."""
    model = OrderItem
    extra = 1
    fields = ('perfume', 'quantity', 'unit_price', 'total_price_display')
    readonly_fields = ('unit_price', 'total_price_display')

    def total_price_display(self, obj):
        return obj.total_price_display() if obj and obj.pk else "—"
    total_price_display.short_description = "Line total"


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """One row per cart checkout: who ordered, what time (hour:minute),
    how many perfumes total, and the grand total price — as requested."""
    list_display = ('id', 'user', 'order_date', 'order_time', 'total_quantity', 'total_price_display')
    list_filter = ('created_at',)
    search_fields = ('user__username',)
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'
    inlines = [OrderItemInline]

    def save_formset(self, request, form, formset, change):
        """Whenever a line's perfume is set/changed in the admin, snapshot
        its current name and price onto the OrderItem (matching what the
        storefront checkout does automatically)."""
        instances = formset.save(commit=False)
        for instance in instances:
            if isinstance(instance, OrderItem) and instance.perfume:
                instance.perfume_name = instance.perfume.name
                instance.unit_price = instance.perfume.price
            instance.save()
        for obj in formset.deleted_objects:
            obj.delete()
        formset.save_m2m()


@admin.register(PageVisit)
class PageVisitAdmin(admin.ModelAdmin):
    """Read-only log of storefront page views. The change list's own
    pagination footer ("N page visits") doubles as the total visitor
    counter, and changelist_view puts that same total front and center
    at the top of the list too.
    """
    list_display = ('path', 'ip_address', 'visited_at')
    list_filter = ('path',)
    date_hierarchy = 'visited_at'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['title'] = f"Page Visits — {PageVisit.objects.count()} total"
        return super().changelist_view(request, extra_context=extra_context)
