from unittest.mock import MagicMock, patch

from django.contrib.auth.models import User
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .ai import generate_description
from .models import Perfume


class PerfumeModelTests(APITestCase):
    def test_seed_fixture_contains_twenty_perfumes(self):
        import json
        from pathlib import Path

        fixture_path = Path(__file__).resolve().parent / "fixtures" / "initial_perfumes.json"
        with fixture_path.open("r", encoding="utf-8") as handle:
            products = json.load(handle)

        self.assertEqual(len(products), 20)
        self.assertTrue(any(item["fields"]["name"] == "Rose Elixir" for item in products))

    def test_str_returns_name(self):
        perfume = Perfume.objects.create(name="Midnight Oud")
        self.assertEqual(str(perfume), "Midnight Oud")

    def test_image_url_resolves_relative_path(self):
        perfume = Perfume.objects.create(name="Rose Garden", image="img/perfume1.png")
        self.assertIn("img/perfume1.png", perfume.image_url())

    def test_image_url_passes_through_absolute_url(self):
        perfume = Perfume.objects.create(
            name="Ocean Breeze", image="https://example.com/p.jpg"
        )
        self.assertEqual(perfume.image_url(), "https://example.com/p.jpg")


class PerfumeApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="tariq", password="StrongPass123")
        self.perfume = Perfume.objects.create(
            name="Amber Nights", description="Warm and cozy.", price="45.00"
        )
        self.list_url = reverse('store:product_list_api')
        self.detail_url = reverse('store:product_detail_api', args=[self.perfume.id])

    # --- Read access is public -------------------------------------------------
    def test_anyone_can_list_products(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_anyone_can_retrieve_a_product(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], "Amber Nights")

    # --- Write access requires authentication (Authentication & Security) -----
    def test_anonymous_user_cannot_create_product(self):
        response = self.client.post(self.list_url, {"name": "Sneaky Scent"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(Perfume.objects.filter(name="Sneaky Scent").exists())

    def test_authenticated_user_can_create_product(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.list_url, {"name": "New Scent", "price": "30.00"})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Perfume.objects.filter(name="New Scent").exists())

    def test_anonymous_user_cannot_delete_product(self):
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Perfume.objects.filter(id=self.perfume.id).exists())

    def test_authenticated_user_can_update_product(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(self.detail_url, {"price": "50.00"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.perfume.refresh_from_db()
        self.assertEqual(self.perfume.price, "50.00")

    def test_authenticated_user_can_delete_product(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Perfume.objects.filter(id=self.perfume.id).exists())


class AuthFlowTests(APITestCase):
    def test_user_can_register(self):
        response = self.client.post(reverse('store:register'), {
            "username": "newuser",
            "password1": "SuperSecret123",
            "password2": "SuperSecret123",
        })
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertTrue(User.objects.filter(username="newuser").exists())

    def test_user_can_log_in(self):
        User.objects.create_user(username="tariq", password="StrongPass123")
        response = self.client.post(reverse('login'), {
            "username": "tariq",
            "password": "StrongPass123",
        })
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)


class OrderApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="buyer", password="StrongPass123")
        self.perfume = Perfume.objects.create(name="Amber Nights", price="$45")
        self.url = reverse('store:order_create_api')

    def test_anonymous_user_cannot_place_order(self):
        response = self.client.post(self.url, {"cart_items": [{"perfume": self.perfume.id, "quantity": 1}]}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_user_can_place_order_with_price_snapshot(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            self.url,
            {"cart_items": [{"perfume": self.perfume.id, "quantity": 2}]},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        order = self.user.orders.get()
        item = order.items.get()
        self.assertEqual(item.perfume_name, "Amber Nights")
        self.assertEqual(item.unit_price, "$45")
        self.assertEqual(item.quantity, 2)
        self.assertEqual(order.total_price_display(), "$90")


class VisitorTrackingTests(APITestCase):
    def test_storefront_page_creates_visit_record(self):
        from .middleware import VisitorTrackingMiddleware
        from .views import index

        request = RequestFactory().get('/')
        request.user = AnonymousUser()
        response = VisitorTrackingMiddleware(index)(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        from .models import PageVisit
        self.assertTrue(PageVisit.objects.filter(path='/').exists())

    def test_storefront_template_keeps_hero_and_intro_sections_balanced(self):
        from .middleware import VisitorTrackingMiddleware
        from .views import index

        request = RequestFactory().get('/')
        request.user = AnonymousUser()
        response = VisitorTrackingMiddleware(index)(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        html = response.content.decode()
        self.assertIn('<div class="hero-art" aria-label="Perfume bottle showcase">', html)
        self.assertIn('</div>\n    </section>\n\n    <section class="intro-strip">', html)
        self.assertLess(html.index('class="hero-art"'), html.index('class="intro-strip"'))


class AiDescriptionTests(APITestCase):
    """Tests use a mocked generator so they run fast, offline, and without
    needing the (large) distilgpt2 weights downloaded — this keeps the
    test suite quick, and covers both the real-model path and the
    fallback path used when the model isn't loaded."""

    def setUp(self):
        self.user = User.objects.create_user(username="tariq", password="StrongPass123")
        self.url = reverse('store:generate_description_api')

    def test_endpoint_requires_authentication(self):
        response = self.client.post(self.url, {"name": "Velvet Rose"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_endpoint_requires_name(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("store.ai._get_generator", return_value=None)
    def test_endpoint_returns_description_with_fallback(self, mock_get_generator):
        """When the local model isn't available, the view still returns a
        usable templated description instead of erroring out."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url, {"name": "Velvet Rose", "notes": "rose, musk"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("Velvet Rose", response.data['description'])

    @patch("store.ai._get_generator")
    def test_generate_description_uses_local_model_when_available(self, mock_get_generator):
        """When the local model is loaded, its generated text (trimmed to
        one or two sentences) is used as the description."""
        mock_generator = MagicMock()
        mock_generator.tokenizer.eos_token_id = 0
        prompt = (
            "Smoky Amber is a luxury perfume with notes of amber, smoke. "
            "In one elegant sentence, it is best described as:"
        )
        mock_generator.return_value = [{
            "generated_text": prompt + " a bold, smoky fragrance for the night. It lingers for hours."
        }]
        mock_get_generator.return_value = mock_generator

        result = generate_description("Smoky Amber", "amber, smoke")
        self.assertIn("Smoky Amber", result)
        self.assertIn("bold, smoky fragrance", result)

    @patch("store.ai._get_generator")
    def test_generate_description_falls_back_if_model_raises(self, mock_get_generator):
        mock_generator = MagicMock()
        mock_generator.side_effect = RuntimeError("model failure")
        mock_get_generator.return_value = mock_generator

        result = generate_description("Smoky Amber", "amber, smoke")
        self.assertIn("Smoky Amber", result)
