from decimal import Decimal

from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.test import TestCase
from django.urls import reverse

from accounts.models import Employee
from agencies.models import Agency
from inventory.models import Inventory
from products.models import Category, Product
from sales.models import Sale


class StaffAccessTests(TestCase):
	def setUp(self):
		self.agency = Agency.objects.create(
			name='Staff Test Agency', city='Douala', address='Test address', is_active=True
		)
		self.other_agency = Agency.objects.create(
			name='Other Agency', city='Yaounde', address='Other address', is_active=True
		)
		self.user = User.objects.create_user(username='staff-test', password='test-pass')
		self.employee = Employee.objects.create(
			user=self.user,
			first_name='Staff',
			last_name='Member',
			email='staff-test@example.com',
			phone='600000000',
			role='STAFF',
			agency=self.agency,
		)
		self.manager_user = User.objects.create_user(username='manager-test', password='test-pass')
		Employee.objects.create(
			user=self.manager_user,
			first_name='Manager',
			last_name='Member',
			email='manager-test@example.com',
			phone='611111111',
			role='MANAGER',
			agency=self.agency,
		)
		category = Category.objects.create(name='Test Category')
		self.product = Product.objects.create(
			agency=self.agency,
			name='Agency Product',
			brand='Test',
			model='A',
			selling_price=Decimal('10.00'),
			category=category,
		)
		self.other_product = Product.objects.create(
			agency=self.other_agency,
			name='Other Product',
			brand='Test',
			model='B',
			selling_price=Decimal('10.00'),
			category=category,
		)
		Inventory.objects.create(agency=self.agency, product=self.product, quantity=2)
		Inventory.objects.create(agency=self.other_agency, product=self.other_product, quantity=10)

	def test_staff_dashboard_and_manager_page_boundary(self):
		self.client.force_login(self.user)
		self.assertEqual(self.client.get(reverse('employee_dashboard')).status_code, 200)
		self.assertEqual(self.client.get(reverse('manager_dashboard')).status_code, 403)
		self.assertEqual(self.client.get(reverse('employee_list')).status_code, 403)

	def test_staff_product_and_inventory_views_are_agency_scoped(self):
		self.client.force_login(self.user)
		response = self.client.get(reverse('employee_products'))
		self.assertContains(response, 'Agency Product')
		self.assertNotContains(response, 'Other Product')
		response = self.client.get(reverse('employee_inventory'))
		self.assertContains(response, 'Agency Product')
		self.assertNotContains(response, 'Other Product')

	def test_staff_cannot_adjust_stock_or_access_user_administration(self):
		self.client.force_login(self.user)
		self.assertEqual(self.client.get(reverse('stock_adjustment')).status_code, 403)
		self.assertEqual(self.client.get(reverse('user_list')).status_code, 302)

	def test_manager_can_still_access_manager_dashboard(self):
		self.client.force_login(self.manager_user)
		self.assertEqual(self.client.get(reverse('manager_dashboard')).status_code, 200)
