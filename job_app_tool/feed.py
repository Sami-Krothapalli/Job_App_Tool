from urllib.parse import urlsplit

LISTINGS_URL = "https://raw.githubusercontent.com/SimplifyJobs/New-Grad-Positions/dev/.github/scripts/listings.json"

WANTED_CATEGORIES = {
    "Software",
    "Software Engineering",
    "AI/ML/Data",
    "Data Science, AI & Machine Learning",
}

NO_SPONSORSHIP = {
    "Does Not Offer Sponsorship",
    "U.S. Citizenship is Required",
}

SITE_DOMAINS = {
    "greenhouse.io": "Greenhouse",
    "ashbyhq.com": "Ashby",
    "lever.co": "Lever",
    "myworkdayjobs.com": "Workday",
    "oraclecloud.com": "Oracle",
}


def fetch_listings(client) -> list[dict]:
    response = client.get(LISTINGS_URL)
    response.raise_for_status()
    return response.json()


def is_open(job) -> bool:
    return job["active"] and job["is_visible"]


def mentions_any(locations, places) -> bool:
    return any(
        place.lower() in location.lower() for location in locations for place in places
    )


def rejection_reason(job, filters) -> str | None:
    if job["category"] not in WANTED_CATEGORIES:
        return f"category: {job['category']}"

    if filters.locations and not mentions_any(job["locations"], filters.locations):
        return f"location: {', '.join(job['locations'])}"

    if (
        filters.needs_sponsorship
        and job["sponsorship"] in NO_SPONSORSHIP
        and not mentions_any(job["locations"], filters.sponsorship_not_needed_in)
    ):
        return f"sponsorship: {job['sponsorship']}"

    return None


def site_for(url) -> str:
    host = urlsplit(url).hostname or ""
    for domain, site in SITE_DOMAINS.items():
        if host == domain or host.endswith("." + domain):
            return site
    return "Custom"
