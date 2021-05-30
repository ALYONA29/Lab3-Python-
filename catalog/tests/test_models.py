from django.test import TestCase

# Create your tests here.

from catalog.models import Director


class DirectorModelTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        """Set up non-modified objects used by all test methods."""
        Director.objects.create(first_name='Big', last_name='Bob')

    def test_first_name_label(self):
        director = Director.objects.get(id=1)
        field_label = director._meta.get_field('first_name').verbose_name
        self.assertEquals(field_label, 'first name')

    def test_last_name_label(self):
        director = Director.objects.get(id=1)
        field_label = director._meta.get_field('last_name').verbose_name
        self.assertEquals(field_label, 'last name')

    def test_date_of_birth_label(self):
        director = Director.objects.get(id=1)
        field_label = director._meta.get_field('date_of_birth').verbose_name
        self.assertEquals(field_label, 'date of birth')

    def test_date_of_death_label(self):
        director = Director.objects.get(id=1)
        field_label = director._meta.get_field('date_of_death').verbose_name
        self.assertEquals(field_label, 'died')

    def test_first_name_max_length(self):
        director = Director.objects.get(id=1)
        max_length = director._meta.get_field('first_name').max_length
        self.assertEquals(max_length, 100)

    def test_last_name_max_length(self):
        director = Director.objects.get(id=1)
        max_length = director._meta.get_field('last_name').max_length
        self.assertEquals(max_length, 100)

    def test_object_name_is_last_name_comma_first_name(self):
        director = Director.objects.get(id=1)
        expected_object_name = '{0}, {1}'.format(director.last_name, director.first_name)

        self.assertEquals(str(director), expected_object_name)

    def test_get_absolute_url(self):
        director = Director.objects.get(id=1)
        # This will also fail if the urlconf is not defined.
        self.assertEquals(director.get_absolute_url(), '/catalog/director/1')
