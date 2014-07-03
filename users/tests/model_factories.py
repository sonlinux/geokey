import factory

from django.utils import timezone

from ..models import User, UserGroup, ViewUserGroup


class UserF(factory.django.DjangoModelFactory):
    FACTORY_FOR = User

    @classmethod
    def _setup_next_sequence(cls):
        try:
            return cls._associated_class.objects.values_list(
                'id', flat=True).order_by('-id')[0] + 1
        except IndexError:
            return 0

    display_name = factory.Sequence(lambda n: "display_name%s" % n)
    email = factory.Sequence(lambda n: "email%s@example.com" % n)
    password = ''
    is_active = True

    last_login = timezone.datetime(2000, 1, 1).replace(tzinfo=timezone.utc)
    date_joined = timezone.datetime(1999, 1, 1).replace(
        tzinfo=timezone.utc)

    @classmethod
    def _prepare(cls, create, **kwargs):
        password = kwargs.pop('password', None)
        user = super(UserF, cls)._prepare(create, **kwargs)
        if password:
            user.set_password(password)
            if create:
                user.save()
        return user


class UserGroupF(factory.django.DjangoModelFactory):
    FACTORY_FOR = UserGroup

    name = factory.Sequence(lambda n: 'name_%d' % n)
    description = factory.LazyAttribute(lambda o: '%s description' % o.name)
    project = factory.SubFactory('projects.tests.model_factories.ProjectF')
    can_contribute = True
    can_moderate = False
    view_all_contrib = False
    read_all_contrib = False

    @factory.post_generation
    def add_users(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for user in extracted:
                self.users.add(user)


class ViewUserGroupFactory(factory.django.DjangoModelFactory):
    FACTORY_FOR = ViewUserGroup

    usergroup = factory.SubFactory(UserGroupF)
    view = factory.SubFactory('dataviews.tests.model_factories.ViewFactory')
    can_read = True
    can_view = True
