from rest_framework import serializers

from cinema.models import (
    Genre,
    Actor,
    CinemaHall,
    Movie,
    MovieSession,
    Ticket,
    Order,
)


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ("id", "name")


class ActorSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = Actor
        fields = ("id", "first_name", "last_name", "full_name")

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"


class CinemaHallSerializer(serializers.ModelSerializer):
    class Meta:
        model = CinemaHall
        fields = ("id", "name", "rows", "seats_in_row", "capacity")


class MovieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Movie
        fields = ("id", "title", "description", "duration", "genres", "actors")


class MovieListSerializer(MovieSerializer):
    genres = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field="name"
    )
    actors = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field="first_name"
    )


class MovieDetailSerializer(MovieSerializer):
    genres = GenreSerializer(many=True, read_only=True)
    actors = ActorSerializer(many=True, read_only=True)

    class Meta:
        model = Movie
        fields = ("id", "title", "description", "duration", "genres", "actors")


class MovieSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovieSession
        fields = ("id", "show_time", "movie", "cinema_hall")


class MovieSessionListSerializer(MovieSessionSerializer):
    movie_title = serializers.CharField(source="movie.title", read_only=True)
    cinema_hall_name = serializers.CharField(
        source="cinema_hall.name", read_only=True
    )
    cinema_hall_capacity = serializers.IntegerField(
        source="cinema_hall.capacity", read_only=True
    )
    tickets_available = serializers.SerializerMethodField()

    class Meta:
        model = MovieSession
        fields = (
            "id",
            "show_time",
            "movie_title",
            "cinema_hall_name",
            "cinema_hall_capacity",
            "tickets_available",
        )

    def get_tickets_available(self, obj):
        return obj.cinema_hall.capacity - obj.tickets.count()


class MovieSessionDetailSerializer(MovieSessionSerializer):
    movie = MovieListSerializer(many=False, read_only=True)
    cinema_hall = CinemaHallSerializer(many=False, read_only=True)

    class Meta:
        model = MovieSession
        fields = ("id", "show_time", "movie", "cinema_hall")


class MovieSessionDetailWithTakenSerializer(MovieSessionDetailSerializer):
    taken_places = serializers.SerializerMethodField()
    tickets_available = serializers.SerializerMethodField()

    class Meta(MovieSessionDetailSerializer.Meta):
        fields = MovieSessionDetailSerializer.Meta.fields + (
            "taken_places",
            "tickets_available",
        )

    def get_taken_places(self, obj):
        return obj.tickets.count()

    def get_tickets_available(self, obj):
        total_capacity = obj.cinema_hall.capacity
        taken = obj.tickets.count()
        return total_capacity - taken


class TicketSerializer(serializers.ModelSerializer):
    movie_session = MovieSessionListSerializer(read_only=True)

    class Meta:
        model = Ticket
        fields = ["id", "row", "seat", "movie_session"]


class TicketCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ["row", "seat", "movie_session"]

    def validate(self, data):
        session = data["movie_session"]
        row = data["row"]
        seat = data["seat"]
        if Ticket.objects.filter(movie_session=session,
                                 row=row, seat=seat).exists():
            raise serializers.ValidationError(
                f"Место {row}-{seat} уже занято на сеансе {session.id}"
            )
        return data


class OrderSerializer(serializers.ModelSerializer):
    tickets = TicketSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ["id", "tickets", "created_at"]


class OrderCreateSerializer(serializers.ModelSerializer):
    tickets = serializers.PrimaryKeyRelatedField(many=True,
                                                 queryset=Ticket.objects.all())

    class Meta:
        model = Order
        fields = ["tickets"]

    def create(self, validated_data):
        user = self.context["request"].user
        tickets = validated_data.pop("tickets")
        order = Order.objects.create(user=user)
        order.tickets.set(tickets)
        return order
