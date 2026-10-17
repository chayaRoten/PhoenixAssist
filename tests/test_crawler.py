from app.crawler import answer_from_documents, extract_page_text, extract_public_links, normalize_url


def test_normalize_url_keeps_site_root_and_relative_paths():
    assert normalize_url("https://www.fnx.co.il/faq/") == "https://www.fnx.co.il/faq/"
    assert normalize_url("/products") == "https://www.fnx.co.il/products"
    assert normalize_url("#section") == "https://www.fnx.co.il/"


def test_extract_public_links_filters_out_external_and_duplicates():
    html = """
    <html><body>
      <a href="/products">Products</a>
      <a href="/faq/">FAQ</a>
      <a href="/products">Products Duplicate</a>
      <a href="https://example.com/outside">Outside</a>
      <a href="#top">Anchor</a>
      <a href="javascript:void(0)">JS</a>
      <a href="https://employer.fnx.co.il/signin">Employer Portal</a>
      <a href="https://smart.fnx.co.il/">Smart Portal</a>
    </body></html>
    """
    links = extract_public_links(html, "https://www.fnx.co.il")
    assert links == [
        "https://www.fnx.co.il/products",
        "https://www.fnx.co.il/faq/",
    ]


def test_extract_page_text_keeps_main_content_but_drops_nav_and_footer():
    html = """
    <html><body>
      <nav>Top Nav</nav>
      <main>
        <h1>Insurance coverage</h1>
        <p>We provide protection for your home.</p>
        <p>Coverage is transparent and clear.</p>
      </main>
      <footer>Contact us</footer>
    </body></html>
    """
    text = extract_page_text(html)
    assert "Insurance coverage" in text
    assert "protection for your home" in text
    assert "Top Nav" not in text
    assert "Contact us" not in text


def test_extract_page_text_drops_duplicate_nested_blocks_and_site_controls():
        html = """
        <main>
            <section>
                <h2>ביטוח מקיף</h2>
                <p>ביטוח מקיף מעניק כיסוי לנזקי רכוש ולצד שלישי.</p>
                <ul><li>שירותי דרך וגרירה</li></ul>
                <button>לדעת עוד על ביטוח מקיף עוד סגור</button>
            </section>
        </main>
        """

        text = extract_page_text(html)

        assert text.count("ביטוח מקיף מעניק") == 1
        assert "לדעת עוד" not in text
        assert "שירותי דרך וגרירה" in text


def test_answer_from_documents_returns_relevant_excerpt_and_source():
    docs = [
        {
            "source_url": "https://www.fnx.co.il/car-insurance/comprehensive/",
            "title": "ביטוח מקיף לרכב",
            "text": "ביטוח מקיף לרכב מעניק כיסוי לנזקי רכוש.\nמחיר הביטוח משתנה לפי פרטי הנהג.",
        },
        {
            "source_url": "https://www.fnx.co.il/",
            "title": "הפניקס",
            "text": "מידע כללי על החברה ועל מגוון השירותים.",
        },
    ]

    answer, sources = answer_from_documents("מה כולל ביטוח מקיף לרכב?", docs)

    assert "כיסוי לנזקי רכוש" in answer
    assert "מחיר הביטוח משתנה" not in answer
    assert sources == ["https://www.fnx.co.il/car-insurance/comprehensive/"]


def test_answer_from_documents_does_not_cite_unrelated_pages():
    docs = [
        {
            "source_url": "https://www.fnx.co.il/",
            "title": "הפניקס",
            "text": "מידע כללי על שירותים פיננסיים וביטוח.",
        }
    ]

    answer, sources = answer_from_documents("מה גובה ההשתתפות העצמית?", docs)

    assert "לא מצאתי" in answer
    assert sources == []


def test_answer_from_documents_clarifies_confusion_instead_of_matching_content():
    docs = [
        {
            "source_url": "https://www.fnx.co.il/car-insurance/comprehensive/",
            "title": "ביטוח מקיף",
            "text": "ביטוח מקיף מעניק כיסוי לנזקי רכוש ולצד שלישי.",
        }
    ]

    answer, sources = answer_from_documents("לא הבנתי", docs)

    assert "איזו נקודה תרצי שאסביר" in answer
    assert sources == []
