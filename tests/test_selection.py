from src.selection.selector import newsletter_word_count

def test_newsletter_word_count():
    a = [{"headline":"Market rises","what_happened":"Stocks gained today","why_it_matters":"Clients may benefit","source_name":"Excluded Source","url":"https://x.com"}]
    assert newsletter_word_count(a, ["Top Stories"], ["STI +0.42%"]) == 12
