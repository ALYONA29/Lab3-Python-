from django.test import TestCase

# Create your tests here.


from catalog.models import Director
from django.urls import reverse


class DirectorListViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Create directors for pagination tests
        number_of_directors = 13
        for director_id in range(number_of_directors):
            Director.objects.create(first_name='Christian {0}'.format(director_id),
                                  last_name='Surname {0}'.format(director_id))

    def test_view_url_exists_at_desired_location(self):
        response = self.client.get('/catalog/directors/')
        self.assertEqual(response.status_code, 200)

    def test_view_url_accessible_by_name(self):
        response = self.client.get(reverse('directors'))
        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        response = self.client.get(reverse('directors'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'catalog/director_list.html')

    def test_pagination_is_ten(self):
        response = self.client.get(reverse('directors'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue('is_paginated' in response.context)
        self.assertTrue(response.context['is_paginated'] is True)
        self.assertEqual(len(response.context['author_list']), 10)

    def test_lists_all_directors(self):
        # Get second page and confirm it has (exactly) the remaining 3 items
        response = self.client.get(reverse('directors')+'?page=2')
        self.assertEqual(response.status_code, 200)
        self.assertTrue('is_paginated' in response.context)
        self.assertTrue(response.context['is_paginated'] is True)
        self.assertEqual(len(response.context['director_list']), 3)


import datetime
from django.utils import timezone

from catalog.models import MovieInstance, Movie, Genre, Country
from django.contrib.auth.models import User  # Required to assign User as a borrower


class LoanedMovieInstancesByUserListViewTest(TestCase):

    def setUp(self):
        # Create two users
        test_user1 = User.objects.create_user(username='testuser1', password='1X<ISRUkw+tuK')
        test_user2 = User.objects.create_user(username='testuser2', password='2HJ1vRV0Z&3iD')

        test_user1.save()
        test_user2.save()

        # Create a movie
        test_director = Director.objects.create(first_name='John', last_name='Smith')
        test_genre = Genre.objects.create(name='Fantasy')
        test_country = Language.objects.create(name='Greate Britain')
        test_movie = Movie.objects.create(
            title='Movie Title',
            summary='My movie summary',
            isbn='ABCDEFG',
            director=test_director,
            country=test_country,
        )
        # Create genre as a post-step
        genre_objects_for_movie = Genre.objects.all()
        test_movie.genre.set(genre_objects_for_movie)
        test_movie.save()

        # Create 30 MovieInstance objects
        number_of_movie_copies = 30
        for movie_copy in range(number_of_movie_copies):
            return_date = timezone.now() + datetime.timedelta(days=movie_copy % 5)
            if movie_copy % 2:
                the_borrower = test_user1
            else:
                the_borrower = test_user2
            status = 'm'
            MovieInstance.objects.create(movie=test_movie, imprint='Unlikely Imprint, 2021', due_back=return_date,
                                        borrower=the_borrower, status=status)

    def test_redirect_if_not_logged_in(self):
        response = self.client.get(reverse('my-borrowed'))
        self.assertRedirects(response, '/accounts/login/?next=/catalog/mymovies/')

    def test_logged_in_uses_correct_template(self):
        login = self.client.login(username='testuser1', password='1X<ISRUkw+tuK')
        response = self.client.get(reverse('my-borrowed'))

        # Check our user is logged in
        self.assertEqual(str(response.context['user']), 'testuser1')
        # Check that we got a response "success"
        self.assertEqual(response.status_code, 200)

        # Check we used correct template
        self.assertTemplateUsed(response, 'catalog/movieinstance_list_borrowed_user.html')

    def test_only_borrowed_movies_in_list(self):
        login = self.client.login(username='testuser1', password='1X<ISRUkw+tuK')
        response = self.client.get(reverse('my-borrowed'))

        # Check our user is logged in
        self.assertEqual(str(response.context['user']), 'testuser1')
        # Check that we got a response "success"
        self.assertEqual(response.status_code, 200)

        # Check that initially we don't have any movies in list (none on loan)
        self.assertTrue('movieinstance_list' in response.context)
        self.assertEqual(len(response.context['movieinstance_list']), 0)

        # Now change all movies to be on loan
        get_ten_movies = MovieInstance.objects.all()[:10]

        for copy in get_ten_movies:
            copy.status = 'o'
            copy.save()

        # Check that now we have borrowed movies in the list
        response = self.client.get(reverse('my-borrowed'))
        # Check our user is logged in
        self.assertEqual(str(response.context['user']), 'testuser1')
        # Check that we got a response "success"
        self.assertEqual(response.status_code, 200)

        self.assertTrue('movieinstance_list' in response.context)

        # Confirm all movies belong to testuser1 and are on loan
        for movieitem in response.context['movieinstance_list']:
            self.assertEqual(response.context['user'], movieitem.borrower)
            self.assertEqual(movieitem.status, 'o')

    def test_pages_paginated_to_ten(self):

        # Change all movies to be on loan.
        # This should make 15 test user ones.
        for copy in MovieInstance.objects.all():
            copy.status = 'o'
            copy.save()

        login = self.client.login(username='testuser1', password='1X<ISRUkw+tuK')
        response = self.client.get(reverse('my-borrowed'))

        # Check our user is logged in
        self.assertEqual(str(response.context['user']), 'testuser1')
        # Check that we got a response "success"
        self.assertEqual(response.status_code, 200)

        # Confirm that only 10 items are displayed due to pagination
        # (if pagination not enabled, there would be 15 returned)
        self.assertEqual(len(response.context['movieinstance_list']), 10)

    def test_pages_ordered_by_due_date(self):

        # Change all movies to be on loan
        for copy in MovieInstance.objects.all():
            copy.status = 'o'
            copy.save()

        login = self.client.login(username='testuser1', password='1X<ISRUkw+tuK')
        response = self.client.get(reverse('my-borrowed'))

        # Check our user is logged in
        self.assertEqual(str(response.context['user']), 'testuser1')
        # Check that we got a response "success"
        self.assertEqual(response.status_code, 200)

        # Confirm that of the items, only 10 are displayed due to pagination.
        self.assertEqual(len(response.context['movieinstance_list']), 10)

        last_date = 0
        for copy in response.context['movieinstance_list']:
            if last_date == 0:
                last_date = copy.due_back
            else:
                self.assertTrue(last_date <= copy.due_back)


from django.contrib.auth.models import Permission  # Required to grant the permission needed to set a movie as returned.


class RenewMovieInstancesViewTest(TestCase):

    def setUp(self):
        # Create a user
        test_user1 = User.objects.create_user(username='testuser1', password='1X<ISRUkw+tuK')
        test_user1.save()

        test_user2 = User.objects.create_user(username='testuser2', password='2HJ1vRV0Z&3iD')
        test_user2.save()
        permission = Permission.objects.get(name='Set movie as returned')
        test_user2.user_permissions.add(permission)
        test_user2.save()

        # Create a movie
        test_director = Director.objects.create(first_name='John', last_name='Smith')
        test_genre = Genre.objects.create(name='Fantasy')
        test_country = Country.objects.create(name='Greate Britain')
        test_movie = Movie.objects.create(title='Movie Title', summary='My movie summary',
                                        isbn='ABCDEFG', director=test_director, country=test_country,)
        # Create genre as a post-step
        genre_objects_for_movie = Genre.objects.all()
        test_movie.genre.set(genre_objects_for_movie)
        test_movie.save()

        # Create a MovieInstance object for test_user1
        return_date = datetime.date.today() + datetime.timedelta(days=5)
        self.test_movieinstance1 = MovieInstance.objects.create(movie=test_movie,
                                                              imprint='Unlikely Imprint, 2021', due_back=return_date,
                                                              borrower=test_user1, status='o')

        # Create a MovieInstance object for test_user2
        return_date = datetime.date.today() + datetime.timedelta(days=5)
        self.test_movieinstance2 = MovieInstance.objects.create(movie=test_movie, imprint='Unlikely Imprint, 2021',
                                                              due_back=return_date, borrower=test_user2, status='o')

    def test_redirect_if_not_logged_in(self):
        response = self.client.get(reverse('renew-movie-employer', kwargs={'pk': self.test_movieinstance1.pk}))
        # Manually check redirect (Can't use assertRedirect, because the redirect URL is unpredictable)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/accounts/login/'))

    def test_forbidden_if_logged_in_but_not_correct_permission(self):
        login = self.client.login(username='testuser1', password='1X<ISRUkw+tuK')
        response = self.client.get(reverse('renew-movie-employer', kwargs={'pk': self.test_movieinstance1.pk}))
        self.assertEqual(response.status_code, 403)


    def test_logged_in_with_permission_borrowed_movie(self):
        login = self.client.login(username='testuser2', password='2HJ1vRV0Z&3iD')
        response = self.client.get(reverse('renew-movie-employer', kwargs={'pk': self.test_movieinstance2.pk}))

        # Check that it lets us login - this is our movie and we have the right permissions.
        self.assertEqual(response.status_code, 200)

    def test_logged_in_with_permission_another_users_borrowed_movie(self):
        login = self.client.login(username='testuser2', password='2HJ1vRV0Z&3iD')
        response = self.client.get(reverse('renew-movie-employer', kwargs={'pk': self.test_movieinstance1.pk}))

        # Check that it lets us login. We're a employer, so we can view any users movie
        self.assertEqual(response.status_code, 200)

    def test_uses_correct_template(self):
        login = self.client.login(username='testuser2', password='2HJ1vRV0Z&3iD')
        response = self.client.get(reverse('renew-movie-employer', kwargs={'pk': self.test_movieinstance1.pk}))
        self.assertEqual(response.status_code, 200)

        # Check we used correct template
        self.assertTemplateUsed(response, 'catalog/movie_renew_employer.html')

    def test_form_renewal_date_initially_has_date_three_weeks_in_future(self):
        login = self.client.login(username='testuser2', password='2HJ1vRV0Z&3iD')
        response = self.client.get(reverse('renew-movie-employer', kwargs={'pk': self.test_movieinstance1.pk}))
        self.assertEqual(response.status_code, 200)

        date_3_weeks_in_future = datetime.date.today() + datetime.timedelta(weeks=3)
        self.assertEqual(response.context['form'].initial['renewal_date'], date_3_weeks_in_future)

    def test_form_invalid_renewal_date_past(self):
        login = self.client.login(username='testuser2', password='2HJ1vRV0Z&3iD')

        date_in_past = datetime.date.today() - datetime.timedelta(weeks=1)
        response = self.client.post(reverse('renew-movie-employer', kwargs={'pk': self.test_movieinstance1.pk}),
                                    {'renewal_date': date_in_past})
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'renewal_date', 'Invalid date - renewal in past')

    def test_form_invalid_renewal_date_future(self):
        login = self.client.login(username='testuser2', password='2HJ1vRV0Z&3iD')
        
        invalid_date_in_future = datetime.date.today() + datetime.timedelta(weeks=5)
        response = self.client.post(reverse('renew-movie-employer', kwargs={'pk': self.test_movieinstance1.pk}),
                                    {'renewal_date': invalid_date_in_future})
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'renewal_date', 'Invalid date - renewal more than 4 weeks ahead')

    def test_redirects_to_all_borrowed_movie_list_on_success(self):
        login = self.client.login(username='testuser2', password='2HJ1vRV0Z&3iD')
        valid_date_in_future = datetime.date.today() + datetime.timedelta(weeks=2)
        response = self.client.post(reverse('renew-movie-employer', kwargs={'pk': self.test_movieinstance1.pk}),
                                    {'renewal_date': valid_date_in_future})
        self.assertRedirects(response, reverse('all-borrowed'))

    def test_HTTP404_for_invalid_movie_if_logged_in(self):
        import uuid
        test_uid = uuid.uuid4()  # unlikely UID to match our movieinstance!
        login = self.client.login(username='testuser2', password='2HJ1vRV0Z&3iD')
        response = self.client.get(reverse('renew-movie-employer', kwargs={'pk': test_uid}))
        self.assertEqual(response.status_code, 404)


class DirectorCreateViewTest(TestCase):
    """Test case for the DirectorCreate view (Created as Challenge)."""

    def setUp(self):
        # Create a user
        test_user1 = User.objects.create_user(username='testuser1', password='1X<ISRUkw+tuK')
        test_user2 = User.objects.create_user(username='testuser2', password='2HJ1vRV0Z&3iD')

        test_user1.save()
        test_user2.save()

        permission = Permission.objects.get(name='Set disk as returned')
        test_user2.user_permissions.add(permission)
        test_user2.save()

        # Create a movie
        test_director = Director.objects.create(first_name='John', last_name='Smith')

    def test_redirect_if_not_logged_in(self):
        response = self.client.get(reverse('director-create'))
        self.assertRedirects(response, '/accounts/login/?next=/catalog/director/create/')

    def test_forbidden_if_logged_in_but_not_correct_permission(self):
        login = self.client.login(username='testuser1', password='1X<ISRUkw+tuK')
        response = self.client.get(reverse('director-create'))
        self.assertEqual(response.status_code, 403)

    def test_logged_in_with_permission(self):
        login = self.client.login(username='testuser2', password='2HJ1vRV0Z&3iD')
        response = self.client.get(reverse('director-create'))
        self.assertEqual(response.status_code, 200)

    def test_uses_correct_template(self):
        login = self.client.login(username='testuser2', password='2HJ1vRV0Z&3iD')
        response = self.client.get(reverse('director-create'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'catalog/director_form.html')

    def test_form_date_of_death_initially_set_to_expected_date(self):
        login = self.client.login(username='testuser2', password='2HJ1vRV0Z&3iD')
        response = self.client.get(reverse('author-create'))
        self.assertEqual(response.status_code, 200)

        expected_initial_date = datetime.date(2021, 5, 11)
        response_date = response.context['form'].initial['date_of_death']
        response_date = datetime.datetime.strptime(response_date, "%d/%m/%Y").date()
        self.assertEqual(response_date, expected_initial_date)

    def test_redirects_to_detail_view_on_success(self):
        login = self.client.login(username='testuser2', password='2HJ1vRV0Z&3iD')
        response = self.client.post(reverse('author-create'),
                                    {'first_name': 'Christian Name', 'last_name': 'Surname'})
