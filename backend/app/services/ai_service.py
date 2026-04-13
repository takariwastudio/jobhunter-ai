import json
from typing import Optional
import anthropic
from app.config import get_settings
from app.schemas.cv import ParsedProfileData, ExperienceItem, EducationItem, SkillItem, LanguageItem

settings = get_settings()


class AIService:
    """Service for AI-powered CV parsing using Anthropic Claude."""

    def __init__(self):
        self.client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = "claude-3-5-sonnet-20241022"  # Latest Claude 3.5 Sonnet

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
