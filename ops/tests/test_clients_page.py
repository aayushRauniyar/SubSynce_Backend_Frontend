from django.test import TestCase
from django.urls import reverse

from ops.tests.helpers import login, make_site, make_user


class ClientsListTests(TestCase):
    def test_name_links_to_detail_and_no_view_button(self):
        site = make_site()
        client = site.client_id
        login(self.client, make_user("ADMINISTRATOR"))
        resp = self.client.get(reverse("ops:clients"))
        detail = reverse("ops:client_detail", args=[client.pk])
        self.assertContains(resp, f'<a href="{detail}"', count=1)
        self.assertNotContains(resp, ">visibility</span>")
        self.assertEqual(self.client.get(detail).status_code, 200)
