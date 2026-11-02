import httpx
import pytest

from job_app_tool.feed import LISTINGS_URL, fetch_listings, is_open, rejection_reason, site_for
from job_app_tool.profile import JobFilters


def job(**changes):
    """A job shaped like one entry in listings.json. Pass only what a test cares about."""
    base = {
        "id": "abc-123",
        "company_name": "Acme",
        "title": "Software Engineer, New Grad",
        "url": "https://jobs.lever.co/acme/abc-123",
        "category": "Software",
        "locations": ["Austin, TX"],
        "sponsorship": "Other",
        "active": True,
        "is_visible": True,
        "date_posted": 1793000000,
    }
    return base | changes


def client_returning(status, body=None):
    """An httpx client that answers from memory, so tests never use the network."""
    return httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(status, json=body)))


# fetch_listings(client) downloads the feed and returns the list of jobs.


def test_fetch_returns_the_jobs():
    assert fetch_listings(client_returning(200, [job()])) == [job()]


def test_fetch_uses_the_listings_url():
    seen = []

    def handler(request):
        seen.append(str(request.url))
        return httpx.Response(200, json=[])

    fetch_listings(httpx.Client(transport=httpx.MockTransport(handler)))

    assert seen == [LISTINGS_URL]


def test_failed_fetch_raises_instead_of_returning_no_jobs():
    with pytest.raises(httpx.HTTPStatusError):
        fetch_listings(client_returning(503))


# is_open(job) is True when the job is active and visible.


def test_active_visible_job_is_open():
    assert is_open(job()) is True


@pytest.mark.parametrize("change", [{"active": False}, {"is_visible": False}])
def test_inactive_or_hidden_job_is_not_open(change):
    assert is_open(job(**change)) is False


# rejection_reason(job, filters) returns None to keep a job, or a short reason to drop it.


@pytest.mark.parametrize(
    "category",
    ["Software", "Software Engineering", "AI/ML/Data", "Data Science, AI & Machine Learning"],
)
def test_software_and_ai_categories_are_kept(category):
    assert rejection_reason(job(category=category), JobFilters()) is None


def test_other_categories_are_rejected_with_the_category_named():
    assert "Hardware" in rejection_reason(job(category="Hardware"), JobFilters())


def test_no_location_filter_keeps_every_location():
    assert rejection_reason(job(locations=["Tokyo"]), JobFilters(locations=[])) is None


def test_location_match_ignores_case_and_checks_every_location():
    filters = JobFilters(locations=["remote", "tx"])

    assert rejection_reason(job(locations=["New York, NY", "Austin, TX"]), filters) is None


def test_job_outside_the_profile_locations_is_rejected():
    reason = rejection_reason(job(locations=["Seattle, WA"]), JobFilters(locations=["TX"]))

    assert "location" in reason.lower()


@pytest.mark.parametrize("sponsorship", ["Does Not Offer Sponsorship", "U.S. Citizenship is Required"])
def test_jobs_without_sponsorship_are_rejected_if_you_need_it(sponsorship):
    filters = JobFilters(needs_sponsorship=True)

    assert "sponsorship" in rejection_reason(job(sponsorship=sponsorship), filters).lower()


@pytest.mark.parametrize("sponsorship", ["Other", "Offers Sponsorship"])
def test_unclear_or_offered_sponsorship_is_kept_if_you_need_it(sponsorship):
    filters = JobFilters(needs_sponsorship=True)

    assert rejection_reason(job(sponsorship=sponsorship), filters) is None


def test_sponsorship_is_ignored_if_you_do_not_need_it():
    assert rejection_reason(job(sponsorship="Does Not Offer Sponsorship"), JobFilters()) is None


CANADA_EXCEPTION = JobFilters(needs_sponsorship=True, sponsorship_not_needed_in=["Canada"])


@pytest.mark.parametrize("locations", [["Toronto, ON, Canada"], ["Remote in Canada"], ["Seattle, WA", "Toronto, ON, Canada"]])
def test_no_sponsorship_job_is_kept_if_it_is_in_an_excepted_place(locations):
    no_sponsorship = job(sponsorship="Does Not Offer Sponsorship", locations=locations)

    assert rejection_reason(no_sponsorship, CANADA_EXCEPTION) is None


def test_no_sponsorship_job_outside_the_excepted_place_is_still_rejected():
    no_sponsorship = job(sponsorship="Does Not Offer Sponsorship", locations=["Seattle, WA"])

    assert "sponsorship" in rejection_reason(no_sponsorship, CANADA_EXCEPTION).lower()


# site_for(url) names the application site from the link's host.


@pytest.mark.parametrize(
    "url, site",
    [
        ("https://job-boards.greenhouse.io/acme/jobs/1", "Greenhouse"),
        ("https://boards.greenhouse.io/acme/jobs/1", "Greenhouse"),
        ("https://job-boards.eu.greenhouse.io/acme/jobs/1", "Greenhouse"),
        ("https://jobs.ashbyhq.com/acme/abc", "Ashby"),
        ("https://jobs.lever.co/acme/abc", "Lever"),
        ("https://jobs.eu.lever.co/acme/abc", "Lever"),
        ("https://acme.wd1.myworkdayjobs.com/en-US/careers/job/1", "Workday"),
        ("https://hdhl.fa.us6.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1/job/1", "Oracle"),
        ("https://stripe.com/jobs/listing/engineer/1?gh_jid=123", "Custom"),
        ("https://careers.acme.com/jobs/1", "Custom"),
    ],
)
def test_site_for(url, site):
    assert site_for(url) == site
