from django.shortcuts import render
import asyncio
import logging
from time import sleep
# Create your views here.

from .models import Movie, Director, MovieInstance, Genre

logger = logging.getLogger(__name__)

def index(request):
    """View function for home page of site."""
    # Generate counts of some of the main objects
    num_movies = Movie.objects.all().count()
    num_instances = MovieInstance.objects.all().count()
    # Available copies of movies
    num_instances_available = MovieInstance.objects.filter(status__exact='a').count()
    num_directors = Director.objects.count()  # The 'all()' is implied by default.

    # Number of visits to this view, as counted in the session variable.
    num_visits = request.session.get('num_visits', 1)
    request.session['num_visits'] = num_visits+1

    logger.info("Visit home page")

    # Render the HTML template index.html with the data in the context variable.
    return render(
        request,
        'index.html',
        context={'num_movies': num_movies, 'num_instances': num_instances,
                 'num_instances_available': num_instances_available, 'num_directors': num_directors,
                 'num_visits': num_visits},
    )


from django.views import generic


class MovieListView(generic.ListView):
    """Generic class-based view for a list of Movies."""
    model = Movie
    paginate_by = 10


class MovieDetailView(generic.DetailView):
    """Generic class-based detail view for a movie."""
    model = Movie


class DirectorListView(generic.ListView):
    """Generic class-based list view for a list of directors."""
    model = Director
    paginate_by = 10


class DirectorDetailView(generic.DetailView):
    """Generic class-based detail view for an director."""
    model = Director


from django.contrib.auth.mixins import LoginRequiredMixin


class LoanedMoviesByUserListView(LoginRequiredMixin, generic.ListView):
    """Generic class-based view listing movies on loan to current user."""
    model = MovieInstance
    template_name = 'catalog/movieinstance_list_borrowed_user.html'
    paginate_by = 10

    def get_queryset(self):
        logger.info("Movies on loan")
        return MovieInstance.objects.filter(borrower=self.request.user).filter(status__exact='o').order_by('due_back')


from django.contrib.auth.mixins import PermissionRequiredMixin


class LoanedMoviesAllListView(PermissionRequiredMixin, generic.ListView):
    """Generic class-based view listing all movies on loan. Only visible to users with can_mark_returned permission."""
    model = MovieInstance
    permission_required = 'catalog.can_mark_returned'
    template_name = 'catalog/movieinstance_list_borrowed_all.html'
    paginate_by = 10

    def get_queryset(self):
        logger.info("Movies on loan")
        #return MovieInstance.objects.filter(status__exact='o').order_by('due_back')
        return MovieInstance.objects.select_related("movie").order_by('due_back')


from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse
import datetime
from django.contrib.auth.decorators import login_required, permission_required

# from .forms import RenewMovieForm
from catalog.forms import RenewMovieForm


@login_required
@permission_required('catalog.can_mark_returned', raise_exception=True)
async def renew_movie_employer(request, pk):
    """View function for renewing a specific MovieInstance by employer."""
    movie_instance = asyncio.create_task(get_object_or_404(MovieInstance, pk=pk))

    # If this is a POST request then process the Form data
    if request.method == 'POST':

        # Create a form instance and populate it with data from the request (binding):
        form = asyncio.create_task(RenewMovieForm(request.POST))

        # Check if the form is valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required (here we just write it to the model due_back field)
            movie_instance.due_back = form.cleaned_data['renewal_date']
            movie_instance.save()

            # redirect to a new URL:
            logger.info("Renew movie")
            return await HttpResponseRedirect(reverse('all-borrowed'))

    # If this is a GET (or any other method) create the default form
    else:
        logger.warning("Create the default form")
        proposed_renewal_date = datetime.date.today() + datetime.timedelta(weeks=3)
        form = RenewMovieForm(initial={'renewal_date': proposed_renewal_date})

    context = {
        'form': await form,
        'movie_instance': await movie_instance,
    }

    return await render(request, 'catalog/movie_renew_employer.html', context)


from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import Director


class DirectorCreate(PermissionRequiredMixin, CreateView):
    model = Director
    fields = ['first_name', 'last_name', 'date_of_birth', 'date_of_death']
    initial = {'date_of_death': '11/05/2021'}
    permission_required = 'catalog.can_mark_returned'


class DirectorUpdate(PermissionRequiredMixin, UpdateView):
    model = Director
    fields = '__all__' 
    permission_required = 'catalog.can_mark_returned'


class DirectorDelete(PermissionRequiredMixin, DeleteView):
    model = Director
    success_url = reverse_lazy('directors')
    permission_required = 'catalog.can_mark_returned'


# Classes created for the forms challenge
class MovieCreate(PermissionRequiredMixin, CreateView):
    model = Movie
    fields = ['title', 'director', 'summary', 'isbn', 'genre', 'country']
    permission_required = 'catalog.can_mark_returned'


class MovieUpdate(PermissionRequiredMixin, UpdateView):
    model = Movie
    fields = ['title', 'director', 'summary', 'isbn', 'genre', 'country']
    permission_required = 'catalog.can_mark_returned'


class MovieDelete(PermissionRequiredMixin, DeleteView):
    model = Movie
    success_url = reverse_lazy('movies')
    permission_required = 'catalog.can_mark_returned'
