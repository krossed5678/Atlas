from app.newgrounds import parse_track_page, validate_track_url


def test_newgrounds_license_parser_requires_each_track_to_be_reviewed():
    page = "<title>Sunset Suite - Newgrounds.com</title><h2>Licensing Terms</h2><p>You are free to copy, distribute and transmit this work under the following conditions: Attribution: You must give credit to the artist.</p><footer>Credits &amp; Info</footer>"
    record = parse_track_page("https://www.newgrounds.com/audio/listen/12345", page)
    assert record["commercial_status"] == "allowed_with_attribution"
    assert record["downloaded"] is False


def test_newgrounds_license_parser_blocks_noncommercial_tracks():
    page = "<title>Track</title>Licensing Terms<p>Attribution. Noncommercial: You may not use this work for commercial purposes.</p><footer>Credits &amp; Info</footer>"
    assert parse_track_page("https://www.newgrounds.com/audio/listen/12345", page)["commercial_status"] == "not_allowed"
    assert validate_track_url("https://www.newgrounds.com/audio/listen/12345/").endswith("12345")
