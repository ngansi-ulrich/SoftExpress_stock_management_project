from io import BytesIO

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from PIL import Image

from agencies.models import Agency
from .models import Employee

def image_upload(name='profile.png', image_format='PNG', color='red'):
	image = Image.new('RGB', (2, 2), color=color)
	content = BytesIO()
	image.save(content, format=image_format)
	return SimpleUploadedFile(
		name,
		content.getvalue(),
		content_type=f'image/{image_format.lower()}',
	)


class ProfilePictureTests(TestCase):
	@classmethod
	def setUpTestData(cls):
		cls.agency = Agency.objects.create(name='Test Agency')
		cls.staff_user = User.objects.create_user(username='staff', password='test-pass')
		cls.other_user = User.objects.create_user(username='other', password='test-pass')
		cls.staff = Employee.objects.create(
			user=cls.staff_user,
			first_name='Staff',
			last_name='User',
			email='staff@example.com',
			phone='123',
			role='STAFF',
			agency=cls.agency,
		)
		cls.other_employee = Employee.objects.create(
			user=cls.other_user,
			first_name='Other',
			last_name='User',
			email='other@example.com',
			phone='456',
			role='STAFF',
			agency=cls.agency,
		)

	def test_staff_can_upload_and_navbar_uses_saved_picture(self):
		self.client.force_login(self.staff_user)

		response = self.client.post('/profile/', {'profile_picture': image_upload()})

		self.assertRedirects(response, '/profile/')
		self.staff.refresh_from_db()
		self.assertTrue(self.staff.profile_picture.name.startswith('profile_pictures/'))

		response = self.client.get('/employee/dashboard/')
		self.assertContains(response, self.staff.profile_picture.url)

	def test_staff_cannot_choose_another_employee_by_posted_id(self):
		self.client.force_login(self.staff_user)

		response = self.client.post(
			'/profile/',
			{
				'employee_id': self.other_employee.pk,
				'profile_picture': image_upload('other.png', color='blue'),
			},
		)

		self.assertRedirects(response, '/profile/')
		self.staff.refresh_from_db()
		self.other_employee.refresh_from_db()
		self.assertTrue(self.staff.profile_picture)
		self.assertFalse(self.other_employee.profile_picture)

	def test_invalid_image_format_is_rejected(self):
		self.client.force_login(self.staff_user)

		response = self.client.post(
			'/profile/',
			{'profile_picture': SimpleUploadedFile(
				'not-an-image.gif', b'not an image', content_type='image/gif'
			)},
		)

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'valid image')
		self.staff.refresh_from_db()
		self.assertFalse(self.staff.profile_picture)

	def test_each_role_can_update_only_its_own_picture(self):
		for role in ('CEO', 'MANAGER'):
			user = User.objects.create_user(username=role.lower(), password='test-pass')
			employee = Employee.objects.create(
				user=user,
				first_name=role,
				last_name='User',
				email=f'{role.lower()}@example.com',
				phone='789',
				role=role,
				agency=self.agency,
			)
			self.client.force_login(user)

			response = self.client.post('/profile/', {'profile_picture': image_upload(f'{role.lower()}.png')})

			self.assertRedirects(response, '/profile/')
			employee.refresh_from_db()
			self.assertTrue(employee.profile_picture)

	def test_replacing_and_removing_picture_updates_employee(self):
		self.client.force_login(self.staff_user)
		self.client.post('/profile/', {'profile_picture': image_upload('first.png')})
		self.staff.refresh_from_db()
		old_picture = self.staff.profile_picture.name

		self.client.post('/profile/', {'profile_picture': image_upload('second.png', color='blue')})
		self.staff.refresh_from_db()
		self.assertNotEqual(self.staff.profile_picture.name, old_picture)

		response = self.client.post('/profile/', {'remove_picture': 'on'})

		self.assertRedirects(response, '/profile/')
		self.staff.refresh_from_db()
		self.assertFalse(self.staff.profile_picture)

	def test_superuser_without_employee_profile_can_upload_picture(self):
		superuser = User.objects.create_superuser(username='ceo', password='test-pass')
		self.client.force_login(superuser)

		response = self.client.post('/profile/', {'profile_picture': image_upload('ceo.png')})

		self.assertRedirects(response, '/profile/')
		employee = Employee.objects.get(user=superuser)
		self.assertEqual(employee.role, 'CEO')
		self.assertTrue(employee.profile_picture)
