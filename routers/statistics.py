"""
Statistics router - provides analytics and insights on ECHR cases
"""
import logging
from datetime import datetime
from typing import Dict, List, Tuple
from fastapi import APIRouter, Depends
from sqlalchemy import func, extract, and_, Integer
from sqlalchemy.orm import Session

from models import StatisticsResponse, TrendsResponse, YearlyTrendResponse
from database import get_db, Case
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter(prefix="/api/v1", tags=["statistics"])


@router.get(
    "/statistics",
    response_model=StatisticsResponse,
)
async def get_statistics(db: Session = Depends(get_db)) -> StatisticsResponse:
    """
    Get comprehensive statistics on ECHR cases
    
    Returns:
    - Total cases, violations, pending, resolved counts
    - Cases by country
    - Cases by year
    - Cases by article
    - Top countries
    - Top articles
    - Violation rate
    """
    try:
        # Total counts
        total_cases = db.query(func.count(Case.id)).scalar() or 0
        violation_cases = (
            db.query(func.count(Case.id)).filter(Case.violation == True).scalar() or 0
        )
        
        # Pending vs resolved approximation based on status
        pending_cases = (
            db.query(func.count(Case.id))
            .filter(Case.status.ilike("%pending%"))
            .scalar()
            or 0
        )
        resolved_cases = total_cases - pending_cases

        # Violation rate
        violation_rate = (
            (violation_cases / total_cases * 100) if total_cases > 0 else 0
        )

        # Cases by country (parse semicolon-separated countries)
        all_cases = db.query(Case.country).filter(Case.country.isnot(None)).all()
        country_counts = {}
        for (country_str,) in all_cases:
            if country_str:
                # Split by semicolon and count each country
                countries = [c.strip() for c in country_str.split(';') if c.strip()]
                for country in countries:
                    country_counts[country] = country_counts.get(country, 0) + 1
        
        by_country = country_counts
        top_countries = sorted(
            country_counts.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:10]

        # Cases by year
        years_data = (
            db.query(
                extract("year", Case.judgementdate).label("year"),
                func.count(Case.id).label("count"),
            )
            .filter(Case.judgementdate.isnot(None))
            .group_by(extract("year", Case.judgementdate))
            .order_by(extract("year", Case.judgementdate))
            .all()
        )
        by_year = {int(year): count for year, count in years_data if year}

        # Cases by article (split comma-separated articles)
        articles_data = (
            db.query(Case.article)
            .filter(Case.article.isnot(None))
            .all()
        )
        article_counts: Dict[str, int] = {}
        for (articles,) in articles_data:
            if articles:
                for article in articles.split(","):
                    article = article.strip()
                    if article:
                        article_counts[article] = article_counts.get(article, 0) + 1

        # Sort articles by count
        by_article = dict(
            sorted(article_counts.items(), key=lambda x: x[1], reverse=True)
        )
        top_articles = list(by_article.items())[:20]

        return StatisticsResponse(
            total_cases=total_cases,
            violation_cases=violation_cases,
            pending_cases=pending_cases,
            resolved_cases=resolved_cases,
            by_country=by_country,
            by_year=by_year,
            by_article=by_article,
            top_countries=top_countries,
            top_articles=top_articles,
            violation_rate=round(violation_rate, 2),
        )

    except Exception as e:
        logger.error(f"Error generating statistics: {e}")
        raise


@router.get(
    "/trends",
    response_model=TrendsResponse,
)
async def get_trends(db: Session = Depends(get_db)) -> TrendsResponse:
    """
    Get yearly trends for visualization
    
    Returns:
    - Yearly breakdown of cases and violations
    - Year-over-year growth rates
    - Total growth rate
    """
    try:
        # Get yearly data
        yearly_data = (
            db.query(
                extract("year", Case.judgementdate).label("year"),
                func.count(Case.id).label("total"),
                func.sum(Case.violation.cast(Integer)).label("violations"),
            )
            .filter(Case.judgementdate.isnot(None))
            .group_by(extract("year", Case.judgementdate))
            .order_by(extract("year", Case.judgementdate))
            .all()
        )

        trends_list: List[YearlyTrendResponse] = []
        yearly_growth: Dict[int, float] = {}
        previous_count = 0

        for year, total, violations in yearly_data:
            if year is None:
                continue

            year_int = int(year)
            violation_count = int(violations) if violations else 0

            # Get country breakdown for this year
            countries = (
                db.query(Case.country, func.count(Case.id).label("count"))
                .filter(
                    and_(
                        extract("year", Case.judgementdate) == year,
                        Case.country.isnot(None),
                    )
                )
                .group_by(Case.country)
                .all()
            )
            cases_per_country = {country: count for country, count in countries}

            trends_list.append(
                YearlyTrendResponse(
                    year=year_int,
                    total_cases=int(total),
                    violation_cases=violation_count,
                    cases_per_country=cases_per_country,
                )
            )

            # Calculate growth rate
            if previous_count > 0:
                growth = ((int(total) - previous_count) / previous_count) * 100
                yearly_growth[year_int] = round(growth, 2)

            previous_count = int(total)

        # Calculate total growth
        if len(trends_list) > 1:
            first_count = trends_list[0].total_cases
            last_count = trends_list[-1].total_cases
            total_growth = (
                ((last_count - first_count) / first_count * 100)
                if first_count > 0
                else 0
            )
        else:
            total_growth = 0

        return TrendsResponse(
            trends=trends_list,
            yearly_growth=yearly_growth,
            total_cases_growth=round(total_growth, 2),
        )

    except Exception as e:
        logger.error(f"Error generating trends: {e}")
        raise


@router.get("/statistics/country/{country}")
async def get_country_statistics(
    country: str,
    db: Session = Depends(get_db),
):
    """Get statistics for a specific country"""
    try:
        country_cases = db.query(Case).filter(Case.country.ilike(f"%{country}%")).all()

        if not country_cases:
            return {
                "country": country,
                "message": "No cases found for this country",
                "total": 0,
            }

        total = len(country_cases)
        violations = sum(1 for case in country_cases if case.violation)
        articles = {}

        for case in country_cases:
            if case.article:
                for article in case.article.split(","):
                    article = article.strip()
                    articles[article] = articles.get(article, 0) + 1

        years = {}
        for case in country_cases:
            if case.judgementdate:
                year = case.judgementdate.year
                years[year] = years.get(year, 0) + 1

        return {
            "country": country,
            "total_cases": total,
            "violation_cases": violations,
            "violation_rate": round((violations / total * 100) if total > 0 else 0, 2),
            "top_articles": sorted(articles.items(), key=lambda x: x[1], reverse=True)[:10],
            "yearly_breakdown": dict(sorted(years.items())),
        }

    except Exception as e:
        logger.error(f"Error getting country statistics: {e}")
        raise


@router.get("/statistics/article/{article}")
async def get_article_statistics(
    article: str,
    db: Session = Depends(get_db),
):
    """Get statistics for a specific article"""
    try:
        article_cases = (
            db.query(Case)
            .filter(Case.article.ilike(f"%{article}%"))
            .all()
        )

        if not article_cases:
            return {
                "article": article,
                "message": "No cases found for this article",
                "total": 0,
            }

        total = len(article_cases)
        violations = sum(1 for case in article_cases if case.violation)
        countries = {}

        for case in article_cases:
            if case.country:
                countries[case.country] = countries.get(case.country, 0) + 1

        years = {}
        for case in article_cases:
            if case.judgementdate:
                year = case.judgementdate.year
                years[year] = years.get(year, 0) + 1

        return {
            "article": article,
            "total_cases": total,
            "violation_cases": violations,
            "violation_rate": round((violations / total * 100) if total > 0 else 0, 2),
            "top_countries": sorted(countries.items(), key=lambda x: x[1], reverse=True)[:10],
            "yearly_breakdown": dict(sorted(years.items())),
        }

    except Exception as e:
        logger.error(f"Error getting article statistics: {e}")
        raise
