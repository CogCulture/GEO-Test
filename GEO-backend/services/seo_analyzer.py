# import logging
# import os
# import json
# import contextlib
# from typing import List, Dict, Any
# from bs4 import BeautifulSoup

# from .seo_crawler import crawl_site
# from .seo_prompts import get_system_prompt

# logger = logging.getLogger(__name__)

# # ─── Paid.ai / OpenTelemetry Tracing ──────────────────────────────────────────
# try:
#     from openinference.instrumentation import using_attributes
# except ImportError:
#     using_attributes = None

# def _build_paid_context(user_id: str = None):
#     """Build a context manager that attaches Paid.ai trace attributes to all
#     Anthropic API calls made inside it."""
#     @contextlib.contextmanager
#     def _ctx():
#         if using_attributes and user_id:
#             with using_attributes(
#                 user_id=user_id,
#                 session_id=user_id,
#                 metadata={
#                     "externalCustomerId": user_id,
#                     "externalProductId": "seo_analyzer",
#                 },
#                 tags=["seo_analyzer"],
#             ):
#                 yield
#         else:
#             yield
#     return _ctx()

# def extract_relevant_html_for_skill(html: str, skill: str) -> str:
#     """Uses BeautifulSoup to strip out irrelevant parts of the HTML based on the SEO skill to save tokens."""
#     if not html:
#         return ""
        
#     try:
#         soup = BeautifulSoup(html, 'html.parser')
        
#         # Always remove script, style, and noscript tags unless they are specifically needed
#         if skill not in ["schema", "visual", "performance"]:
#             for element in soup(["script", "style", "noscript"]):
#                 element.decompose()
                
#         if skill == "schema":
#             # Extract ONLY JSON-LD schema scripts
#             schemas = soup.find_all('script', type='application/ld+json')
#             if not schemas:
#                 return "No JSON-LD schema found."
#             return "\n".join(str(s) for s in schemas)
            
#         elif skill == "content":
#             # Extract text-heavy elements, headers, main blocks (remove nav/footer to focus on core content)
#             for element in soup(["nav", "footer", "aside"]):
#                 element.decompose()
#             body = soup.find('body')
#             text = body.get_text(separator=' ', strip=True) if body else soup.get_text(separator=' ', strip=True)
#             return text[:3000] # Limit length to save tokens
            
#         elif skill in ["technical", "sitemap"]:
#             # Need head, meta, title, semantic architecture
#             head = soup.find('head')
#             links = soup.find_all('a', href=True)
#             output = ""
#             if head:
#                 # Remove inline scripts/styles from head
#                 for element in head(["script", "style"]):
#                     element.decompose()
#                 output += str(head) + "\n"
#             output += "<!-- Top 50 Links Found: -->\n"
#             for link in links[:50]:
#                 href = link.get('href')
#                 text = link.get_text(strip=True)[:50]
#                 output += f"<a href='{href}'>{text}</a>\n"
#             return output[:3000]
            
#         elif skill == "performance":
#             # Focus on images, preloads, and basic structure
#             images = soup.find_all('img')
#             preloads = soup.find_all('link', rel="preload")
#             output = "<!-- Top 20 Images: -->\n"
#             for img in images[:20]:
#                 output += str(img) + "\n"
#             output += "<!-- Preloads: -->\n"
#             for p in preloads:
#                 output += str(p) + "\n"
#             head = soup.find('head')
#             if head:
#                 for element in head(["script", "style"]):
#                     element.decompose()
#                 output += str(head) + "\n"
#             return output[:3000]
            
#         elif skill == "visual":
#             # Focus on Viewport meta, stylesheets, inline styles, and H1/Header layout
#             meta_viewport = soup.find('meta', attrs={'name': 'viewport'})
#             styles = soup.find_all('link', rel='stylesheet')
#             inline_styles = soup.find_all('style')
#             output = f"Viewport: {meta_viewport}\n"
#             output += "Stylesheets: " + "\n".join(str(s) for s in styles) + "\n"
#             output += "Inline styles snippet: " + "\n".join(str(s)[:200] for s in inline_styles) + "\n"
            
#             header = soup.find('header')
#             h1 = soup.find('h1')
#             if header: output += f"Header structure: {str(header)[:500]}\n"
#             if h1: output += f"H1: {h1}\n"
#             return output[:3000]
            
#         else:
#             # Fallback
#             return html[:3000]
            
#     except Exception as e:
#         logger.warning(f"Error parsing HTML for {skill}: {e}")
#         return html[:3000]

# def evaluate_seo_skills(url: str, skills: List[str], max_pages: int = 30, user_id: str = None) -> Dict[str, Any]:
#     """
#     Coordinates the crawling of exactly max 30 pages natively and 
#     evaluates them via Claude LLM using exactly transcribed system prompts.
#     """
#     api_key = os.environ.get("ANTHROPIC_API_KEY")
#     if not api_key:
#         raise ValueError("ANTHROPIC_API_KEY environment variable is not set")
        
#     import anthropic
#     client = anthropic.Anthropic(api_key=api_key)
    
#     logger.info(f"Starting native SEO crawl for {url} (max {max_pages} pages)")
#     pages = crawl_site(url, max_pages)
    
#     if not pages:
#         raise ValueError("Could not extract any content from the site. Check URL or site blocking protections.")
        
#     logger.info(f"Successfully crawled {len(pages)} pages")
    
#     results = {}
    
#     for skill in skills:
#         logger.info(f"Evaluating SEO skill: {skill}")
#         system_prompt = get_system_prompt(skill)
        
#         # Build optimized HTML summary specifically for this skill
#         skill_crawled_summary = f"Total Pages Crawled: {len(pages)}\n\n"
#         for i, p in enumerate(pages):
#             extracted = extract_relevant_html_for_skill(p['html'], skill)
#             if extracted.strip():
#                 skill_crawled_summary += f"--- Page {i+1}: {p['url']} ---\n"
#                 skill_crawled_summary += extracted + "\n...(truncated)\n\n"
        
#         user_prompt = f"Analyze the following HTML extracts for the domain {url} perfectly fulfilling your system instructions.\n\n[Crawled HTML Extract Begins]\n{skill_crawled_summary}\n[Crawled HTML Extract Ends]"
        
#         try:
#             with _build_paid_context(user_id):
#                 # We use claude-sonnet-4-20250514 as it's the default anthropic model in the code base
#                 response = client.messages.create(
#                     model="claude-sonnet-4-20250514",
#                     max_tokens=4096,
#                     system=system_prompt,
#                     messages=[{
#                         "role": "user",
#                         "content": user_prompt
#                     }]
#                 )
            
#             result_text = ""
#             for block in response.content:
#                 if hasattr(block, 'text'):
#                     result_text += block.text
                    
#             results[skill] = result_text.strip()
#             logger.info(f"✅ Successfully evaluated skill {skill}")
            
#         except Exception as e:
#             logger.error(f"❌ Error evaluating skill {skill} via Claude: {e}")
#             results[skill] = f"Error generating analysis: {str(e)}"
            
#     return {
#         "url": url,
#         "pages_crawled": len(pages),
#         "results": results,
#     }

import logging
import os
import json
import contextlib
from typing import List, Dict, Any
from bs4 import BeautifulSoup

from .seo_crawler import crawl_site
from .seo_prompts import get_system_prompt, SUPPORTED_SKILLS

logger = logging.getLogger(__name__)

# ─── Paid.ai / OpenTelemetry Tracing ──────────────────────────────────────────
try:
    from openinference.instrumentation import using_attributes
except ImportError:
    using_attributes = None

def _build_paid_context(user_id: str = None):
    """Build a context manager that attaches Paid.ai trace attributes to all
    Anthropic API calls made inside it."""
    @contextlib.contextmanager
    def _ctx():
        if using_attributes and user_id:
            with using_attributes(
                user_id=user_id,
                session_id=user_id,
                metadata={
                    "externalCustomerId": user_id,
                    "externalProductId": "seo_analyzer",
                },
                tags=["seo_analyzer"],
            ):
                yield
        else:
            yield
    return _ctx()


def extract_relevant_html_for_skill(html: str, skill: str) -> str:
    """
    Uses BeautifulSoup to extract the subset of HTML that each skill prompt
    expects, saving tokens and improving Claude's focus.

    Extraction modes by skill:
      schema      → Only <script type="application/ld+json"> blocks
      content     → Stripped body text (no nav/footer/aside), truncated 3000 chars
      geo         → Head + stripped body text (needs both meta signals + citability)
      technical   → <head> (scripts/styles removed) + top-50 internal links
      sitemap     → same as technical
      hreflang    → same as technical (hreflang tags live in <head>)
      page        → Full stripped HTML (fallback — single-page deep audit)
      performance → Top-20 <img> tags + <link rel="preload"> + <head>
      images      → same as performance
      visual      → Viewport meta + stylesheets + inline style snippets + header/H1
    """
    if not html:
        return ""

    try:
        soup = BeautifulSoup(html, 'html.parser')

        # ── Schema: JSON-LD only ──────────────────────────────────────────────
        if skill == "schema":
            schemas = soup.find_all('script', type='application/ld+json')
            if not schemas:
                return "No JSON-LD schema found."
            return "\n".join(str(s) for s in schemas)

        # ── Content: body text, no nav/footer/aside ───────────────────────────
        elif skill == "content":
            for element in soup(["nav", "footer", "aside", "script", "style", "noscript"]):
                element.decompose()
            body = soup.find('body')
            text = body.get_text(separator=' ', strip=True) if body else soup.get_text(separator=' ', strip=True)
            return text[:3000]

        # ── GEO: head meta signals + body text (combined for citability) ──────
        elif skill == "geo":
            # Extract head (no scripts/styles)
            head = soup.find('head')
            head_output = ""
            if head:
                for element in head(["script", "style"]):
                    element.decompose()
                head_output = str(head) + "\n"

            # Extract body text (no nav/footer)
            for element in soup(["nav", "footer", "aside", "script", "style", "noscript"]):
                element.decompose()
            body = soup.find('body')
            body_text = body.get_text(separator=' ', strip=True) if body else ""

            # Combine: head first (for crawler/meta signals), then body text
            combined = head_output + "\n<!-- Body Text: -->\n" + body_text
            return combined[:4000]  # GEO needs more context — slightly larger window

        # ── Technical / Sitemap / Hreflang: head + top-50 links ──────────────
        elif skill in ["technical", "sitemap", "hreflang"]:
            head = soup.find('head')
            links = soup.find_all('a', href=True)
            output = ""
            if head:
                for element in head(["script", "style"]):
                    element.decompose()
                output += str(head) + "\n"
            output += "<!-- Top 50 Links Found: -->\n"
            for link in links[:50]:
                href = link.get('href', '')
                text = link.get_text(strip=True)[:50]
                output += f"<a href='{href}'>{text}</a>\n"
            return output[:3000]

        # ── Performance / Images: img tags + preloads + head ─────────────────
        elif skill in ["performance", "images"]:
            images = soup.find_all('img')
            preloads = soup.find_all('link', rel="preload")
            output = "<!-- Top 20 Images: -->\n"
            for img in images[:20]:
                output += str(img) + "\n"
            output += "\n<!-- Preload Links: -->\n"
            for p in preloads:
                output += str(p) + "\n"
            head = soup.find('head')
            if head:
                for element in head(["script", "style"]):
                    element.decompose()
                output += "\n<!-- Head: -->\n" + str(head) + "\n"
            return output[:3000]

        # ── Visual: viewport, stylesheets, inline styles, header/H1 ──────────
        elif skill == "visual":
            meta_viewport = soup.find('meta', attrs={'name': 'viewport'})
            stylesheets = soup.find_all('link', rel='stylesheet')
            inline_styles = soup.find_all('style')
            header = soup.find('header')
            h1 = soup.find('h1')

            output = f"<!-- Viewport Meta: -->\n{meta_viewport}\n\n"
            output += "<!-- Stylesheets: -->\n"
            output += "\n".join(str(s) for s in stylesheets) + "\n\n"
            output += "<!-- Inline Styles (first 200 chars each): -->\n"
            output += "\n".join(str(s)[:200] for s in inline_styles) + "\n\n"
            if header:
                output += f"<!-- Header Structure (first 500 chars): -->\n{str(header)[:500]}\n\n"
            if h1:
                output += f"<!-- H1: -->\n{str(h1)}\n"
            return output[:3000]

        # ── Page: full stripped HTML (single-page deep audit) ─────────────────
        elif skill == "page":
            # Keep scripts that are JSON-LD schema (needed for schema sub-check)
            ld_scripts = soup.find_all('script', type='application/ld+json')
            for element in soup(["script", "style", "noscript"]):
                element.decompose()
            # Re-append JSON-LD scripts to body for the page audit
            body = soup.find('body')
            if body and ld_scripts:
                for s in ld_scripts:
                    body.append(s)
            return str(soup)[:4000]

        # ── Fallback ──────────────────────────────────────────────────────────
        else:
            for element in soup(["script", "style", "noscript"]):
                element.decompose()
            return str(soup)[:3000]

    except Exception as e:
        logger.warning(f"Error parsing HTML for skill '{skill}': {e}")
        return html[:3000]


def evaluate_seo_skills(
    url: str,
    skills: List[str],
    max_pages: int = 30,
    user_id: str = None
) -> Dict[str, Any]:
    """
    Crawls up to max_pages (hard cap: 30) and evaluates each requested SEO skill
    via the Anthropic Claude API using the skill-specific system prompts from
    seo_prompts.py.

    Args:
        url:       The website URL to crawl and analyze.
        skills:    List of skill keys (see SUPPORTED_SKILLS in seo_prompts.py).
        max_pages: Maximum pages to crawl. Capped at 30.
        user_id:   Optional — used for Paid.ai trace attribution.

    Returns:
        {
            "url": str,
            "pages_crawled": int,
            "results": { skill_key: analysis_text, ... },
            "unsupported_skills": [ ... ]   # skills not in SUPPORTED_SKILLS
        }
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable is not set")

    import anthropic
    client = anthropic.Anthropic(api_key=api_key)

    # Validate and split skills
    valid_skills = [s for s in skills if s.lower() in SUPPORTED_SKILLS]
    unsupported = [s for s in skills if s.lower() not in SUPPORTED_SKILLS]
    if unsupported:
        logger.warning(f"Unsupported skills requested (will be skipped): {unsupported}")

    if not valid_skills:
        raise ValueError(
            f"No valid skills provided. Supported: {SUPPORTED_SKILLS}. Got: {skills}"
        )

    # Hard cap on max_pages matching crawler limit
    max_pages = min(max_pages, 30)

    logger.info(f"Starting SEO crawl for {url} | max_pages={max_pages} | skills={valid_skills}")
    pages = crawl_site(url, max_pages)

    if not pages:
        raise ValueError(
            "Could not extract any content from the site. "
            "Check the URL or whether the site blocks crawlers."
        )

    logger.info(f"Crawled {len(pages)} pages successfully")

    results = {}

    for skill in valid_skills:
        logger.info(f"Evaluating skill: {skill}")
        system_prompt = get_system_prompt(skill)

        # Build the skill-specific HTML summary for this skill only
        skill_crawled_summary = f"Total Pages Crawled: {len(pages)}\n\n"
        for i, p in enumerate(pages):
            extracted = extract_relevant_html_for_skill(p['html'], skill)
            if extracted.strip():
                skill_crawled_summary += f"--- Page {i+1}: {p['url']} ---\n"
                skill_crawled_summary += extracted + "\n...(truncated)\n\n"

        user_prompt = (
            f"Analyze the following HTML extracts for the domain {url} "
            f"following your system instructions precisely.\n\n"
            f"[Crawled HTML Extract Begins]\n"
            f"{skill_crawled_summary}\n"
            f"[Crawled HTML Extract Ends]"
        )

        try:
            with _build_paid_context(user_id):
                response = client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=4096,
                    system=system_prompt,
                    messages=[{
                        "role": "user",
                        "content": user_prompt
                    }]
                )

            result_text = ""
            for block in response.content:
                if hasattr(block, 'text'):
                    result_text += block.text

            results[skill] = result_text.strip()
            logger.info(f"✅ Skill '{skill}' completed successfully")

        except Exception as e:
            logger.error(f"❌ Error evaluating skill '{skill}': {e}")
            results[skill] = f"Error generating analysis: {str(e)}"

    return {
        "url": url,
        "pages_crawled": len(pages),
        "results": results,
        "unsupported_skills": unsupported,
    }