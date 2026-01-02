from django_filters import rest_framework as filters
from cinema.models import (
    Movie,
    MovieSession,
    Actor,
    Genre,
)


class MovieFilter(filters.FilterSet):
    genres = filters.ModelMultipleChoiceFilter(
        field_name="genres__id", queryset=Genre.objects.all()
    )
    actors = filters.ModelMultipleChoiceFilter(
        field_name="actors__id", queryset=Actor.objects.all()
    )
    title = filters.CharFilter(field_name="title", lookup_expr="icontains")

    class Meta:
        model = Movie
        fields = ["genres", "actors", "title"]


class MovieSessionFilter(filters.FilterSet):
    movie = filters.ModelChoiceFilter(queryset=Movie.objects.all())
    show_time = filters.DateFilter(field_name="show_time", lookup_expr="date")

    class Meta:
        model = MovieSession
        fields = ["movie", "show_time"]
