from django.views.generic import CreateView, TemplateView
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.utils.html import strip_tags

from braces.views import LoginRequiredMixin

from oauth2_provider.models import AccessToken

from geokey.core.decorators import handle_exceptions_for_admin

from .forms import AppCreateForm
from .models import Application


# ############################################################################
#
# Admin views
#
# ############################################################################


class ApplicationOverview(LoginRequiredMixin, TemplateView):
    """
    Displays an overview of all apps a developer has registered
    `/admin/apps/`
    """
    template_name = 'applications/application_overview.html'

    @handle_exceptions_for_admin
    def get_context_data(self, **kwargs):
        context = super(ApplicationOverview, self).get_context_data(**kwargs)
        context['apps'] = Application.objects.get_list(self.request.user)
        return context


class ApplicationConnected(LoginRequiredMixin, TemplateView):
    """
    Displays an overview of all apps a user has connected
    `/admin/apps/connected`
    """
    template_name = 'applications/application_connected.html'

    @handle_exceptions_for_admin
    def get_context_data(self, **kwargs):
        tokens = AccessToken.objects.filter(
            user=self.request.user).distinct('application')

        apps = [token.application for token in tokens]
        return super(ApplicationConnected, self).get_context_data(
            connected_apps=apps,
            **kwargs
        )


class ApplicationDisconnect(LoginRequiredMixin, TemplateView):
    template_name = 'base.html'

    def get(self, request, app_id):
        app = Application.objects.get(pk=app_id)

        tokens = AccessToken.objects.filter(
            user=self.request.user,
            application=app
        )
        if tokens:
            tokens.delete()
            messages.success(self.request, "The connection has been deleted.")

        url = reverse('admin:app_connected')
        return HttpResponseRedirect(url)


class ApplicationCreate(LoginRequiredMixin, CreateView):
    """
    Displays the Create Application page.
    `/admin/apps/register`
    """
    form_class = AppCreateForm
    template_name = 'applications/application_create.html'

    def get_success_url(self):
        """
        Returns the redirect url to be called after successful app registering
        """
        return reverse(
            'admin:app_settings',
            kwargs={'app_id': self.object.id}
        )

    def form_valid(self, form):
        """
        Is called if the form is valid.
        """
        form.instance.user = self.request.user
        form.instance.client_type = 'public'
        messages.success(self.request, "The application has been created.")
        return super(ApplicationCreate, self).form_valid(form)


class ApplicationSettings(LoginRequiredMixin, TemplateView):
    """
    Displays the Application Settings page.
    `/admin/apps/settings`
    """
    template_name = 'applications/application_settings.html'

    @handle_exceptions_for_admin
    def get_context_data(self, app_id, **kwargs):
        app = Application.objects.as_owner(self.request.user, app_id)
        users = AccessToken.objects.values('user').filter(
            application=app).distinct().count()
        return super(ApplicationSettings, self).get_context_data(
            application=app, users=users, **kwargs)

    def post(self, request, app_id):
        context = self.get_context_data(app_id)
        app = context.pop('application')
        data = request.POST

        app.name = strip_tags(data.get('name'))
        app.description = strip_tags(data.get('description'))
        app.download_url = data.get('download_url')
        app.redirect_uris = data.get('redirect_uris')
        app.authorization_grant_type = data.get('authorization_grant_type')
        app.save()

        messages.success(self.request, "The application has been updated.")
        context['application'] = app
        return self.render_to_response(context)


class ApplicationDelete(LoginRequiredMixin, TemplateView):
    template_name = 'base.html'

    @handle_exceptions_for_admin
    def get_context_data(self, app_id, **kwargs):
        app = Application.objects.as_owner(self.request.user, app_id)
        return super(ApplicationDelete, self).get_context_data(
            application=app, **kwargs)

    def get(self, request, app_id):
        context = self.get_context_data(app_id)
        app = context.pop('application', None)

        if app is not None:
            app.delete()

            messages.success(self.request, "The application has been deleted.")
            url = reverse('admin:app_overview')
            return HttpResponseRedirect(url)

        return self.render_to_response(context)
