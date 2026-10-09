import re

from django.conf import settings
from django.db import models


class Perfume(models.Model):
    """A single perfume product shown in the grid and carousel."""
    name = models.CharField(max_length=200)
    description = models.CharField(max_length=500, blank=True, default="No description")
    price = models.CharField(max_length=50, blank=True, default="N/A")
    image = models.CharField(
        max_length=500,
        blank=True,
        default="img/perfume1.png",
        help_text="Path (relative to static/store/) or full URL to the product image.",
    )
    show_in_carousel = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return self.name

    def image_url(self):
        """Return a usable image URL: pass through absolute URLs, otherwise
        resolve relative paths against the store's static folder."""
        if self.image.startswith(('http://', 'https://', '/')):
            return self.image
        from django.templatetags.static import static
        url = static(f"store/{self.image}")
        # Always return a root-relative URL so browser requests work from
        # every storefront route (and not only from '/').
        return url if url.startswith('/') else f"/{url}"


def _parse_priced_total(price_text, quantity):
    """Try to parse the numeric part of a free-text price (e.g. "$49.99")
    and multiply by quantity, keeping any surrounding currency symbol.
    Returns (found, prefix, suffix, amount*quantity)."""
    match = re.search(r'[\d.]+', price_text or '')
    if not match:
        return False, "", "", 0.0
    try:
        amount = float(match.group())
    except ValueError:
        return False, "", "", 0.0
    prefix = (price_text or '')[:match.start()]
    suffix = (price_text or '')[match.end():]
    return True, prefix, suffix, amount * quantity


class Order(models.Model):
    """A shopping-cart checkout: one order placed by a logged-in user that
    can bundle several different perfumes together (each as an OrderItem
    line, with its own snapshotted price and quantity)."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order #{self.pk} - {self.user}"

    def total_quantity(self):
        return sum(item.quantity for item in self.items.all())
    total_quantity.short_description = "Items"

    def total_price_display(self):
        """Sum of every line's total, using the currency symbol from the
        first priced item. Falls back to "N/A" if no item has a parseable
        numeric price."""
        total = 0.0
        prefix = suffix = ""
        found_any = False
        for item in self.items.all():
            found, p, s, line_total = _parse_priced_total(item.unit_price, item.quantity)
            if not found:
                continue
            if not found_any:
                prefix, suffix = p, s
                found_any = True
            total += line_total
        return f"{prefix}{total:g}{suffix}" if found_any else "N/A"
    total_price_display.short_description = "Total price"

    def order_time(self):
        """Hour:minute the order was placed, for the admin list."""
        return self.created_at.astimezone().strftime('%H:%M')
    order_time.short_description = "Time"

    def order_date(self):
        return self.created_at.astimezone().strftime('%Y-%m-%d')
    order_date.short_description = "Date"


class OrderItem(models.Model):
    """One perfume line within an Order (a cart can have several).

    The unit price is snapshotted from the Perfume at order time (as free
    text, e.g. "$49.99"), since Perfume.price itself is a free-text field.
    This keeps the order's price accurate even if the perfume's price is
    changed or the perfume is later deleted.
    """
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    perfume = models.ForeignKey(Perfume, on_delete=models.SET_NULL, null=True, related_name='order_items')
    perfume_name = models.CharField(max_length=200)
    unit_price = models.CharField(max_length=50, blank=True, default="N/A")
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.perfume_name} x{self.quantity}"

    def total_price_display(self):
        found, prefix, suffix, total = _parse_priced_total(self.unit_price, self.quantity)
        return f"{prefix}{total:g}{suffix}" if found else "N/A"
    total_price_display.short_description = "Total price"


class PageVisit(models.Model):
    """One row per page view on the public storefront (not the admin/API),
    so we have a simple visitor counter to show in the admin.

    This counts hits, not unique people — there's no login requirement to
    browse the store, so we can't reliably tell two visits by the same
    person apart from two different people.
    """
    path = models.CharField(max_length=255)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    visited_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-visited_at']

    def __str__(self):
        return f"{self.path} @ {self.visited_at:%Y-%m-%d %H:%M}"
