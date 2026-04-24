import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

import httpx

from app.config import get_settings

settings = get_settings()

# Adzuna supports these country codes
ADZUNA_COUNTRIES = {
    "es", "mx", "ar", "co", "br", "us", "gb", "ca", "au", "de", "fr", "it", "nl", "pl", "ru", "za",
}


@dataclass
class JobResult:
    external_id: str
    title: str
    company: str
    description: str
    source: str
    source_url: str
    location: Optional[str] = None
    salary_range: Optional[str] = None
    job_type: Optional[str] = None
    remote: Optional[bool] = None
    posted_date: Optional[datetime] = None
    raw_data: dict = field(default_factory=dict)


def _adzuna_salary(job: dict) -> Optional[str]:
    sal_min = job.get("salary_min")
    sal_max = job.get("salary_max")
    if sal_min and sal_max:
        return f"{sal_min:,.0f} – {sal_max:,.0f}"
    if sal_min:
        return f"Desde {sal_min:,.0f}"
    if sal_max:
        return f"Hasta {sal_max:,.0f}"
    return None


def _parse_iso(value: str) -> Optional[datetime]:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return None


async def search_adzuna(
    query: str,
    location: str = "",
    country: str = "es",
    page: int = 1,
    results_per_page: int = 10,
) -> list[JobResult]:
    code = country.lower()
    if code not in ADZUNA_COUNTRIES:
        code = "es"

    params: dict = {
        "app_id": settings.ADZUNA_APP_ID,
        "app_key": settings.ADZUNA_APP_KEY,
        "results_per_page": results_per_page,
        "what": query,
        "content-type": "application/json",
    }
    if location:
        params["where"] = location

    url = f"https://api.adzuna.com/v1/api/jobs/{code}/search/{page}"

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()

    results = []
    for job in data.get("results", []):
        results.append(JobResult(
            external_id=str(job.get("id", "")),
            title=job.get("title", ""),
            company=job.get("company", {}).get("display_name", ""),
            description=job.get("description", ""),
            location=job.get("location", {}).get("display_name"),
            salary_range=_adzuna_salary(job),
            job_type=job.get("contract_type"),
            remote=None,
            source="adzuna",
            source_url=job.get("redirect_url", ""),
            posted_date=_parse_iso(job["created"]) if job.get("created") else None,
            raw_data=job,
        ))
    return results


async def search_jsearch(
    query: str,
    location: str = "",
    remote: Optional[bool] = None,
    page: int = 1,
    results_per_page: int = 10,
) -> list[JobResult]:
    full_query = f"{query} in {location}" if location else query

    params: dict = {
        "query": full_query,
        "page": str(page),
        "num_pages": "1",
        "num_pages": str(max(1, results_per_page // 10)),
    }
    if remote is True:
        params["remote_jobs_only"] = "true"

    headers = {
        "X-RapidAPI-Key": settings.JSEARCH_API_KEY,
        "X-RapidAPI-Host": "jsearch.p.rapidapi.com",
    }

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            "https://jsearch.p.rapidapi.com/search",
            params=params,
            headers=headers,
        )
        resp.raise_for_status()
        data = resp.json()

    results = []
    for job in data.get("data", []):
        sal_min = job.get("job_min_salary")
        sal_max = job.get("job_max_salary")
        currency = job.get("job_salary_currency") or ""
        period = job.get("job_salary_period") or ""
        salary_range = None
        if sal_min and sal_max:
            salary_range = f"{currency} {sal_min:,.0f} – {sal_max:,.0f} {period}".strip()
        elif sal_min:
            salary_range = f"{currency} Desde {sal_min:,.0f} {period}".strip()

        posted_date = None
        if ts := job.get("job_posted_at_timestamp"):
            try:
                posted_date = datetime.fromtimestamp(int(ts))
            except Exception:
                pass

        results.append(JobResult(
            external_id=job.get("job_id", ""),
            title=job.get("job_title", ""),
            company=job.get("employer_name", ""),
            description=job.get("job_description", ""),
            location=job.get("job_city") or job.get("job_country"),
            salary_range=salary_range,
            job_type=job.get("job_employment_type"),
            remote=job.get("job_is_remote"),
            source="jsearch",
            source_url=job.get("job_apply_link", ""),
            posted_date=posted_date,
            raw_data=job,
        ))
    return results


async def search_jobs(
    query: str,
    location: str = "",
    country: str = "es",
    remote: Optional[bool] = None,
    page: int = 1,
    results_per_page: int = 10,
    source: str = "all",
) -> list[JobResult]:
    if source == "adzuna":
        return await search_adzuna(query, location, country, page, results_per_page)

    if source == "jsearch":
        return await search_jsearch(query, location, remote, page, results_per_page)

    # "all" — run both in parallel, each gets half the quota
    half = max(5, results_per_page // 2)
    adzuna_res, jsearch_res = await asyncio.gather(
        search_adzuna(query, location, country, page, half),
        search_jsearch(query, location, remote, page, half),
        return_exceptions=True,
    )

    combined: list[JobResult] = []
    # Interleave so both sources appear near the top
    a_list = adzuna_res if isinstance(adzuna_res, list) else []
    j_list = jsearch_res if isinstance(jsearch_res, list) else []
    for a, j in zip(a_list, j_list):
        combined.append(a)
        combined.append(j)
    combined.extend(a_list[len(j_list):])
    combined.extend(j_list[len(a_list):])
    return combined
