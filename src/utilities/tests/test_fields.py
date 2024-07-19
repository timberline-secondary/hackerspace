from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError

from django_tenants.test.cases import TenantTestCase
from queryset_sequence import QuerySetSequence

from utilities.fields import GFKChoiceField, RestrictedFileFormField
from utilities.models import RestrictedFileField


User = get_user_model()


class GFKChoiceFieldTest(TenantTestCase):
    def setUp(self):
        self.user1 = User.objects.create(username='johndoe', first_name='John', last_name='Doe')
        self.user2 = User.objects.create(username='janedoe', first_name='Jane', last_name='Doe')
        self.group1 = Group.objects.create(name='Editors')

    def _ct_pk(self, obj):
        return f'{ContentType.objects.get_for_model(obj).pk}-{obj.pk}'

    def test_basics(self):
        f = GFKChoiceField(
            queryset=QuerySetSequence(
                User.objects.filter(pk__in=[self.user1.pk, self.user2.pk]),
                Group.objects.filter(pk__in=[self.group1.pk]),
            ),
        )
        self.assertEqual(
            list(f.choices),
            [
                ('', '---------'),
                (
                    'user',
                    [
                        (self._ct_pk(self.user1), 'johndoe'),
                        (self._ct_pk(self.user2), 'janedoe'),
                    ],
                ),
                (
                    'group',
                    [
                        (self._ct_pk(self.group1), 'Editors'),
                    ],
                ),
            ],
        )
        with self.assertRaises(ValidationError):
            f.clean('')
        with self.assertRaises(ValidationError):
            f.clean(None)
        with self.assertRaises(ValidationError):
            f.clean('-')

        # Invalid types that require TypeError to be caught.
        with self.assertRaises(ValidationError):
            f.clean([['fail']])
        with self.assertRaises(ValidationError):
            f.clean([{'foo': 'bar'}])

        self.assertEqual(f.clean(self._ct_pk(self.user2)).get_full_name(), 'Jane Doe')
        self.assertEqual(f.clean(self._ct_pk(self.group1)).name, 'Editors')


class RestrictedFileFieldTest(TenantTestCase):
    def setUp(self):
        self.default_file_field = RestrictedFileField()
        self.image_file_field = RestrictedFileField(content_types=['image/jpeg', 'image/png'])

    def test_content_type(self):
        "Ensure the default content type is 'All', and that the content type can be set correctly."

        # ensure default content type is 'All'
        self.assertEqual(self.default_file_field.content_types, 'All')

        # ensure content type is set correctly
        self.assertEqual(self.image_file_field.content_types, ['image/jpeg', 'image/png'])


class RestrictedFileFormFieldTest(TenantTestCase):
    def setUp(self):
        self.default_file_field = RestrictedFileFormField()
        self.image_file_field = RestrictedFileFormField(content_types=['image/jpeg', 'image/png'])

    def test_content_type(self):
        "Ensure the default content type is 'All', and that the content type can be set correctly."

        # ensure default content type is 'All'
        self.assertEqual(self.default_file_field.content_types, 'All')

        # ensure content type is set correctly
        self.assertEqual(self.image_file_field.content_types, ['image/jpeg', 'image/png'])
