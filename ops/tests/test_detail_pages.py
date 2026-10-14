import uuid
from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from authuser.model.user import UserDetail
from invoice.model.invoicemanagement import ContractorInvoice
from ops.tests.helpers import login, make_schedule, make_site, make_user
from work.model.workcomplete import CompleteWork


class SubcontractorDetailTests(TestCase):
    def setUp(self):
        self.admin = make_user("ADMINISTRATOR")
        self.alex = make_user("CONTRACTOR", username="alex")
        UserDetail.objects.create(user=self.alex, first_name="Alex", last_name="Ng", phone="0400111222")
        self.site = make_site(contractor=self.alex, name="Shield Station")
        today = timezone.localdate()
        self.upcoming = make_schedule(self.site, self.admin, day=today + timedelta(days=1))
        done = make_schedule(self.site, self.admin, day=today - timedelta(days=1), status="COMPLETED")
        CompleteWork.objects.create(schedule=done, completed_by=self.alex, check_in_time=timezone.now(),
                                    check_out_time=timezone.now(), status="COMPLETED")
        ContractorInvoice.objects.create(invoice_number="INV-1", site=self.site, invoice_date=today,
                                         service_period_start=today, service_period_end=today,
                                         amount=500, created_by=self.alex, status="APPROVED")

    def test_list_links_name_and_has_no_view_button(self):
        login(self.client, self.admin)
        resp = self.client.get(reverse("ops:subcontractors"))
        self.assertContains(resp, reverse("ops:subcontractor_detail", args=[self.alex.pk]))
        self.assertNotContains(resp, "openViewModal")

    def test_detail_shows_profile_sites_upcoming_work_and_earnings(self):
        login(self.client, self.admin)
        resp = self.client.get(reverse("ops:subcontractor_detail", args=[self.alex.pk]))
        for text in ("Alex Ng", "@alex", "0400111222", "Shield Station", "$500.00",
                     reverse("ops:site_detail", args=[self.site.pk]),
                     reverse("ops:schedule_detail", args=[self.upcoming.pk])):
            self.assertContains(resp, text)
        self.assertEqual(resp.context["completed_count"], 1)

    def test_detail_staff_only_and_404_for_non_contractor(self):
        login(self.client, self.alex)
        self.assertRedirects(self.client.get(reverse("ops:subcontractor_detail", args=[self.alex.pk])),
                             reverse("ops:dashboard"), fetch_redirect_response=False)
        self.client.logout()
        login(self.client, self.admin)
        self.assertEqual(self.client.get(reverse("ops:subcontractor_detail", args=[self.admin.pk])).status_code, 404)


class ScheduleDetailTests(TestCase):
    def setUp(self):
        self.admin = make_user("ADMINISTRATOR")
        self.alex = make_user("CONTRACTOR", username="alex")
        self.site = make_site(contractor=self.alex, name="Shield Station")
        self.schedule = make_schedule(self.site, self.admin, day=timezone.localdate())
        self.schedule.notes = "Bring ladder."
        self.schedule.save()

    def test_list_links_to_detail(self):
        login(self.client, self.admin)
        resp = self.client.get(reverse("ops:schedules"))
        self.assertContains(resp, reverse("ops:schedule_detail", args=[self.schedule.pk]))

    def test_detail_without_and_with_work_record(self):
        login(self.client, self.admin)
        url = reverse("ops:schedule_detail", args=[self.schedule.pk])
        resp = self.client.get(url)
        for text in ("Shield Station", "Bring ladder.", self.site.address, "No work recorded",
                     reverse("ops:subcontractor_detail", args=[self.alex.pk]),
                     reverse("ops:client_detail", args=[self.site.client_id.pk])):
            self.assertContains(resp, text)
        work = CompleteWork.objects.create(schedule=self.schedule, completed_by=self.alex,
                                           check_in_time=timezone.now(), completion_notes="All done.")
        resp = self.client.get(url)
        self.assertContains(resp, "All done.")
        self.assertContains(resp, reverse("ops:completion_detail", args=[work.pk]))

    def test_unknown_schedule_404(self):
        login(self.client, self.admin)
        self.assertEqual(self.client.get(reverse("ops:schedule_detail", args=[uuid.uuid4()])).status_code, 404)
