LISTINGS_URL = "https://raw.githubusercontent.com/SimplifyJobs/New-Grad-Positions/dev/.github/scripts/listings.json"
WANTED_CATEGORIES = {
    "Software",
    "Software Engineering",
    "Forward Deployed Engineer",
    "Infrastructure Enginee",
}


def fetch_listings(client):
    response = client.get(LISTINGS_URL)
    response.raise_for_status()
    return response.json()


def is_open(job):
    return job["active"] and job["is_visible"]


def rejection_reason(job, filters):
    ## Job Category
    if job["category"] not in WANTED_CATEGORIES:
        return f"category: {job['category']}"
    if 


def site_for(url):
    pass
