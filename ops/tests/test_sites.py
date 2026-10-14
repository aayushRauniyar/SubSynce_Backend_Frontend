from datetime import date, timedelta

from django.test import TestCase
from django.urls import reverse

from ops.tests.helpers import login, make_schedule, make_site, make_user


class SitesPageTests(TestCase):
    def setUp(self):
        self.admin = make_user("ADMINISTRATOR")
        self.alex = make_user("CONTRACTOR", username="alex")
        self.site = make_site(contractor=self.alex, name="Shield Station")
        self.site.cleaning_instructions = "Mop the lobby last."
        self.site.save()

    def test_list_shows_name_link_frequency_contractor_and_actions(self):
        login(self.client, self.admin)
        resp = self.client.get(reverse("ops:sites"))
        self.assertContains(resp, reverse("ops:site_detail", args=[self.site.pk]))
        self.assertContains(resp, ">Contractor</th>")
        self.assertNotContains(resp, ">Address</th>")
        self.assertNotContains(resp, ">Price</th>")
        self.assertContains(resp, "alex")
        self.assertContains(resp, reverse("ops:site_delete", args=[self.site.pk]))

    def test_detail_shows_every_field_and_next_service(self):
        make_schedule(self.site, self.admin, day=date.today() + timedelta(days=2))
        login(self.client, self.admin)
        resp = self.client.get(reverse("ops:site_detail", args=[self.site.pk]))
        self.assertEqual(resp.status_code, 200)
        for text in ("Shield Station", self.site.address, "Weekly", "$450.00", "alex", "Mop the lobby last.",
                     self.site.client_id.first_name, "No photos yet"):
            self.assertContains(resp, text)
        upcoming = (date.today() + timedelta(days=2))
        self.assertContains(resp, f"{upcoming:%a} {upcoming.day} {upcoming:%b %Y}")
        # Deleting from the site's own page returns to the list, not the deleted page.
        self.assertContains(resp, f'name="next" value="{reverse("ops:sites")}"')

    def test_detail_is_staff_only_and_404s_for_unknown_site(self):
        login(self.client, self.alex)
        self.assertRedirects(self.client.get(reverse("ops:site_detail", args=[self.site.pk])), reverse("ops:dashboard"),
                             fetch_redirect_response=False)
        self.client.logout()
        login(self.client, self.admin)
        import uuid
        self.assertEqual(self.client.get(reverse("ops:site_detail", args=[uuid.uuid4()])).status_code, 404)

    def test_no_template_comment_leaks_into_pages(self):
        login(self.client, self.admin)
        for url in (reverse("ops:sites"), reverse("ops:site_detail", args=[self.site.pk])):
            self.assertNotContains(self.client.get(url), "{#")
