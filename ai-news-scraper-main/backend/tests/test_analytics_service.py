from backend.services.analytics.trends import AnalyticsService


def sample_articles():
    return [
        {
            "article_id": "a1",
            "title": "OpenAI launches new model",
            "clean_content": "OpenAI releases a new model built with PyTorch and Python.",
            "source": "TechCrunch AI",
            "author": "Reporter One",
            "keywords": "openai, model, pytorch",
            "detected_language": "en",
            "published_date": "2026-05-11T10:00:00Z",
            "category": "AI Models",
        },
        {
            "article_id": "a2",
            "title": "PyTorch makes training easier",
            "clean_content": "PyTorch and Docker simplify deployment.",
            "source": "OpenAI Blog",
            "author": "Reporter Two",
            "keywords": "pytorch, docker",
            "detected_language": "en",
            "published_date": "2026-05-10T10:00:00Z",
            "category": "Tooling",
        },
    ]


def test_compute_trends_and_full_analytics_are_consistent():
    articles = sample_articles()

    trends = AnalyticsService.compute_trends(articles, days=7)
    analytics = AnalyticsService.generate_full_analytics(articles, days=7)

    assert trends["total_articles"] == 2
    assert analytics["total_articles"] == 2
    assert analytics["trends"]["total_articles"] == 2
    assert len(analytics["source_distribution"]) == 2
    assert len(analytics["top_keywords"]) >= 2


def test_compute_top_tools_uses_article_text_not_hardcoded_list():
    tools = AnalyticsService.compute_top_tools(sample_articles(), top_n=5)

    tool_names = {tool["name"] for tool in tools}

    assert "OpenAI" in tool_names or "OPENAI" in tool_names
    assert any("PyTorch" in name or "PYTORCH" in name for name in tool_names)