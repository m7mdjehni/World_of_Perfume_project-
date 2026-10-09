from rest_framework import serializers

from .models import Order, OrderItem, Perfume


class PerfumeSerializer(serializers.ModelSerializer):
    """Serializes Perfume for the REST API.

    `image` is stored as a raw path/URL on the model but always served back
    resolved to a usable URL (via Perfume.image_url), matching the contract
    the front-end (main.js) already expects.
    """

    class Meta:
        model = Perfume
        fields = [
            'id',
            'name',
            'description',
            'price',
            'image',
            'show_in_carousel',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['image'] = instance.image_url()
        return representation


class OrderItemInputSerializer(serializers.Serializer):
    """One cart line coming in from the client: which perfume, how many."""
    perfume = serializers.PrimaryKeyRelatedField(queryset=Perfume.objects.all())
    quantity = serializers.IntegerField(min_value=1)


class OrderItemSerializer(serializers.ModelSerializer):
    """One cart line going back out, with its snapshotted name/price and
    computed line total."""
    total_price = serializers.CharField(source='total_price_display', read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'perfume', 'perfume_name', 'unit_price', 'quantity', 'total_price']
        read_only_fields = ['id', 'perfume_name', 'unit_price', 'total_price']


class OrderSerializer(serializers.ModelSerializer):
    """Serializes a whole cart checkout: who ordered, when, every line in
    the cart, and the grand total.

    Input shape (what the front-end's "submit order" button sends):
        { "items": [{"perfume": 3, "quantity": 2}, {"perfume": 5, "quantity": 1}] }

    `perfume_name` / `unit_price` are snapshotted server-side per line from
    each Perfume at creation time, and `user` is taken from the request,
    never from client input.
    """
    username = serializers.CharField(source='user.username', read_only=True)
    items = OrderItemSerializer(many=True, read_only=True)
    total_quantity = serializers.IntegerField(read_only=True)
    total_price = serializers.CharField(source='total_price_display', read_only=True)
    order_time = serializers.CharField(read_only=True)

    # Write-only input: the list of cart lines to create this order from.
    cart_items = OrderItemInputSerializer(many=True, write_only=True, source='items')

    class Meta:
        model = Order
        fields = [
            'id',
            'username',
            'items',
            'cart_items',
            'total_quantity',
            'total_price',
            'order_time',
            'created_at',
        ]
        read_only_fields = ['id', 'username', 'items', 'total_quantity', 'total_price', 'order_time', 'created_at']

    def validate_cart_items(self, value):
        if not value:
            raise serializers.ValidationError("The cart is empty.")
        return value

    def create(self, validated_data):
        cart_items = validated_data.pop('items')
        user = self.context['request'].user
        order = Order.objects.create(user=user)
        OrderItem.objects.bulk_create([
            OrderItem(
                order=order,
                perfume=entry['perfume'],
                perfume_name=entry['perfume'].name,
                unit_price=entry['perfume'].price,
                quantity=entry['quantity'],
            )
            for entry in cart_items
        ])
        return order
