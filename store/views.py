from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect
from rest_framework import generics, permissions, parsers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from .ai import generate_description
from .models import Order, Perfume
from .serializers import OrderSerializer, PerfumeSerializer

class IsAdminUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_superuser)
        
def index(request):
    """Render the storefront page. Perfume cards and the carousel are
    populated client-side via the /api/products/ JSON endpoint, matching
    the behaviour of the original main.js fetchProducts() call."""
    return render(request, 'store/index.html', {
        'is_authenticated': request.user.is_authenticated,
    })


def register(request):
    """Simple self-service sign-up so visitors can create an account and
    unlock write access to the API (adding/editing/deleting perfumes)."""
    if request.user.is_authenticated:
        return redirect('store:index')

    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('store:index')
    else:
        form = UserCreationForm()

    return render(request, 'registration/register.html', {'form': form})


class PerfumeListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/products/       -> list all perfumes (public)
    POST /api/products/       -> create a perfume (authenticated users only)
    POST /api/products/add/   -> same as above, kept as an alias for the
                                  existing front-end (main.js addProduct()).
    """
    queryset = Perfume.objects.all()
    serializer_class = PerfumeSerializer
    parser_classes = [parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser]

    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [IsAdminUser()]


class PerfumeDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/products/<id>/ -> retrieve a single perfume (public)
    PUT    /api/products/<id>/ -> full update (authenticated users only)
    PATCH  /api/products/<id>/ -> partial update (authenticated users only)
    DELETE /api/products/<id>/ -> delete (authenticated users only)
    """
    queryset = Perfume.objects.all()
    serializer_class = PerfumeSerializer
    parser_classes = [parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser]

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.AllowAny()]
        return [IsAdminUser()]


class OrderCreateView(generics.CreateAPIView):
    """
    POST /api/orders/ -> place an order for a perfume (authenticated users
    only). Shows up in the admin site with the username, quantity, price,
    and when the order was placed.
    """
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


@api_view(['POST'])
@permission_classes([IsAdminUser])
def generate_description_api(request):
    """AI Integration: POST {name, notes} -> {description}.

    Requires authentication since it's a content-authoring helper for
    people managing the catalog, not a public endpoint.
    """
    name = (request.data.get('name') or '').strip()
    notes = (request.data.get('notes') or '').strip()
    if not name:
        return Response({'error': 'name is required.'}, status=status.HTTP_400_BAD_REQUEST)

    description = generate_description(name, notes)
    return Response({'description': description})
