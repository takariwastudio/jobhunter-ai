import json
from typing import Optional, List
import anthropic
from app.config import get_settings
from app.schemas.cv import ParsedProfileData, ExperienceItem, EducationItem, SkillItem, LanguageItem

settings = get_settings()


class AIService:
    """Service for AI-powered CV parsing using Anthropic Claude."""

    def __init__(self):
        self.client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = "claude-sonnet-4-6"

    async def parse_cv(self, cv_text: str) -> ParsedProfileData:
        """
        Parse CV text and extract structured information using Claude.

        Args:
            cv_text: Raw text extracted from CV

        Returns:
            ParsedProfileData with structured information
        """
        # Truncate if text is too long (Claude has token limits)
        max_chars = 15000
        if len(cv_text) > max_chars:
            cv_text = cv_text[:max_chars] + "\n[...truncated]"

        prompt = f"""You are an expert HR professional and resume parser. Your task is to extract structured information from the following CV/resume text.

Please extract the following information and respond ONLY with a valid JSON object:
{{
    "full_name": "Candidate's full name",
    "email": "Email address if found",
    "phone": "Phone number if found",
    "summary": "Professional summary or objective statement",
    "experience": [
        {{
            "company": "Company name",
            "title": "Job title",
            "start_date": "Start date (any format or YYYY-MM)",
            "end_date": "End date (any format or YYYY-MM or 'Present')",
            "description": "Brief description of responsibilities"
        }}
    ],
    "education": [
        {{
            "institution": "School/university name",
            "degree": "Degree obtained",
            "start_date": "Start year",
            "end_date": "End year"
        }}
    ],
    "skills": [
        {{
            "name": "Skill name",
            "category": "technical" or "soft",
            "level": "beginner", "intermediate", "advanced", or "expert" (or null if unknown)
        }}
    ],
    "languages": [
        {{
            "name": "Language name",
            "level": "basic", "conversational", "fluent", or "native"
        }}
    ]
}}

Rules:
- Use null for fields that are not found, not found in the text
- For dates, preserve the format found in the CV (e.g., "Jan 2020", "2020", "2020-01")
- Infer skill categories: programming languages, frameworks, tools = "technical"; communication, leadership = "soft"
- If level is unclear, use null
- The response MUST be valid JSON only, no markdown, no comments, no explanations

CV TEXT:
{cv_text}
"""

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                temperature=0,  # More deterministic output
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            # Extract JSON from response
            content = response.content[0].text
            # Remove any markdown code block formatting if present
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()

            # Parse JSON
            data = json.loads(content)

            # Convert to Pydantic model
            return self._dict_to_parsed_profile(data, cv_text)

        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse AI response as JSON: {str(e)}. Response: {content[:500]}")
        except Exception as e:
            raise ValueError(f"Error parsing CV with AI: {str(e)}")

    def _dict_to_parsed_profile(self, data: dict, raw_text: str) -> ParsedProfileData:
        """Convert dictionary response to ParsedProfileData model."""

        # Parse experience
        experiences = []
        for exp in data.get("experience", []) or []:
            if exp:
                experiences.append(ExperienceItem(
                    company=exp.get("company", ""),
                    title=exp.get("title", ""),
                    start_date=exp.get("start_date"),
                    end_date=exp.get("end_date"),
                    description=exp.get("description")
                ))

        # Parse education
        education = []
        for edu in data.get("education", []) or []:
            if edu:
                education.append(EducationItem(
                    institution=edu.get("institution", ""),
                    degree=edu.get("degree", ""),
                    start_date=edu.get("start_date"),
                    end_date=edu.get("end_date")
                ))

        # Parse skills
        skills = []
        for skill in data.get("skills", []) or []:
            if skill:
                skills.append(SkillItem(
                    name=skill.get("name", ""),
                    category=skill.get("category", "technical"),
                    level=skill.get("level")
                ))

        # Parse languages
        languages = []
        for lang in data.get("languages", []) or []:
            if lang:
                languages.append(LanguageItem(
                    name=lang.get("name", ""),
                    level=lang.get("level", "conversational")
                ))

        return ParsedProfileData(
            full_name=data.get("full_name"),
            email=data.get("email"),
            phone=data.get("phone"),
            summary=data.get("summary"),
            experience=experiences,
            education=education,
            skills=skills,
            languages=languages,
            raw_text=raw_text[:5000]  # Store first 5000 chars
        )

    async def generate_cover_letter(
        self,
        profile: ParsedProfileData,
        job_title: str,
        company: str,
        job_description: str
    ) -> str:
        """
        Generate a personalized cover letter based on profile and job.

        Args:
            profile: Parsed profile data
            job_title: Job title
            company: Company name
            job_description: Job description

        Returns:
            Generated cover letter text
        """
        skills_text = ", ".join([s.name for s in profile.skills[:10]])
        experience_text = "\n".join([
            f"- {exp.title} at {exp.company}" for exp in profile.experience[:3]
        ])

        prompt = f"""Write a professional cover letter for the following candidate applying for the position.

CANDIDATE PROFILE:
Name: {profile.full_name}
Summary: {profile.summary or "N/A"}
Key Skills: {skills_text}
Relevant Experience:
{experience_text}

JOB DETAILS:
Title: {job_title}
Company: {company}
Description: {job_description[:1000]}

Write a compelling cover letter that:
1. Opens with enthusiasm for the role and company
2. Highlights 2-3 most relevant skills and experiences
3. Shows alignment with the job requirements
4. Closes with a call to action

Keep it concise (250-350 words) and professional. Address it to "Hiring Manager" if no specific contact is known.
"""

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}]
            )

            return response.content[0].text.strip()

        except Exception as e:
            raise ValueError(f"Error generating cover letter: {str(e)}")

    async def calculate_match_score(
        self,
        profile: ParsedProfileData,
        job_title: str,
        job_description: str,
        requirements: Optional[str] = None
    ) -> dict:
        """
        Calculate match score between profile and job.

        Returns:
            Dict with score, reasoning, matching_skills, missing_skills
        """
        skills_text = ", ".join([s.name for s in profile.skills])
        experience_text = "\n".join([
            f"- {exp.title} at {exp.company}: {exp.description[:200] if exp.description else 'N/A'}"
            for exp in profile.experience[:5]
        ])

        prompt = f"""Analyze how well this candidate matches the job position.

CANDIDATE PROFILE:
Name: {profile.full_name}
Skills: {skills_text}
Experience:
{experience_text}

JOB:
Title: {job_title}
Description: {job_description}
{requirements or ""}

Provide a JSON response with this exact structure:
{{
    "score": 85,
    "reasoning": "Brief explanation of why this candidate is a good/poor match",
    "matching_skills": ["skill1", "skill2"],
    "missing_skills": ["skill3", "skill4"],
    "recommendation": "Proceed with interview" or "Not a strong match"
}}

Score from 0-100 based on skills match, relevant experience, and overall fit.
"""

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                temperature=0,
                messages=[{"role": "user", "content": prompt}]
            )

            content = response.content[0].text
            # Clean up markdown if present
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]

            return json.loads(content.strip())

        except Exception as e:
            raise ValueError(f"Error calculating match score: {str(e)}")

    def _build_profile_summary(self, profile: ParsedProfileData) -> str:
        """Format profile data into a compact text block for Claude."""
        skills_by_category: dict[str, list[str]] = {}
        for s in profile.skills:
            skills_by_category.setdefault(s.category, []).append(s.name)

        skills_text = "\n".join(
            f"  {cat.capitalize()}: {', '.join(names)}"
            for cat, names in skills_by_category.items()
        )

        experience_text = "\n".join(
            f"  - {exp.title} at {exp.company}"
            + (f" ({exp.start_date} – {exp.end_date or 'Present'})" if exp.start_date else "")
            + (f": {exp.description[:150]}" if exp.description else "")
            for exp in profile.experience[:5]
        )

        education_text = "\n".join(
            f"  - {edu.degree} @ {edu.institution}" + (f" ({edu.end_date})" if edu.end_date else "")
            for edu in profile.education[:3]
        )

        languages_text = ", ".join(f"{l.name} ({l.level})" for l in profile.languages)

        parts = [f"Name: {profile.full_name or 'Unknown'}"]
        if profile.summary:
            parts.append(f"Summary: {profile.summary[:300]}")
        if skills_text:
            parts.append(f"Skills:\n{skills_text}")
        if experience_text:
            parts.append(f"Experience:\n{experience_text}")
        if education_text:
            parts.append(f"Education:\n{education_text}")
        if languages_text:
            parts.append(f"Languages: {languages_text}")
        return "\n\n".join(parts)

    async def batch_match_scores(
        self,
        profile: ParsedProfileData,
        jobs: List[dict],
    ) -> List[dict]:
        """
        Score compatibility between a candidate profile and multiple jobs in one call.

        Uses prompt caching so the profile (expensive part) is cached across calls
        from the same user session.

        Args:
            profile: Parsed candidate profile
            jobs: List of dicts with keys: external_id, title, company, description

        Returns:
            List of dicts with keys: external_id, score, reasoning,
            matching_skills, missing_skills, recommendation
        """
        profile_summary = self._build_profile_summary(profile)

        system_prompt = f"""You are an expert technical recruiter. Analyze candidate-job fit with precision.

CANDIDATE PROFILE:
{profile_summary}

SCORING GUIDE:
- 75-100 (strong_match): Candidate meets most requirements; strong overlap in skills and experience level
- 50-74 (good_match): Solid overlap but some gaps; candidate could grow into missing areas
- 25-49 (partial_match): Relevant background but significant skill or domain gaps
- 0-24 (weak_match): Little relevant experience or skills alignment

Always be honest — a weak match should score low, not 50. A strong match can score 90+."""

        jobs_block = "\n\n".join(
            f"JOB {i + 1} (external_id: {job['external_id']})\n"
            f"Title: {job['title']}\nCompany: {job['company']}\n"
            f"Description: {job['description'][:600]}"
            for i, job in enumerate(jobs)
        )

        user_message = f"""Analyze compatibility between the candidate and each of these {len(jobs)} jobs.

{jobs_block}

Return a JSON array with exactly {len(jobs)} objects in the same order as the jobs above:
[
  {{
    "external_id": "<the job's external_id>",
    "score": <integer 0-100>,
    "reasoning": "<2-3 sentences explaining the fit>",
    "matching_skills": ["<skill1>", "<skill2>"],
    "missing_skills": ["<skill3>"],
    "recommendation": "<strong_match|good_match|partial_match|weak_match>"
  }}
]

Respond ONLY with the JSON array. No markdown, no explanations outside the array."""

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=[
                    {
                        "type": "text",
                        "text": system_prompt,
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
                messages=[{"role": "user", "content": user_message}],
            )

            content = response.content[0].text.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]

            results = json.loads(content.strip())
            if not isinstance(results, list):
                raise ValueError("Expected a JSON array from Claude")
            return results

        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse batch match response as JSON: {e}")
        except Exception as e:
            raise ValueError(f"Error in batch match scoring: {e}")
