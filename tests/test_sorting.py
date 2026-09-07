from datetime import date

from renderer.models import DatedEntry, EntryListDated
from renderer.render import filter_entry_list_dated

def dated_entry(title, start_date, end_date=None):
    return DatedEntry(
        title=title,
        organisation="Crown Gas & Power",
        start_date=start_date,
        end_date=end_date,
        highlights=["Did the thing."],
        tags=["core"],
    )

def titles_after_filtering(entries):
    filtered = filter_entry_list_dated(EntryListDated(entries=entries), {"core"})
    return [entry.title for entry in filtered.entries]

def test_entries_come_back_newest_first():
    entries = [
        dated_entry("Oldest", date(2017, 1, 1), date(2019, 1, 1)),
        dated_entry("Newest", date(2023, 5, 1)),
        dated_entry("Middle", date(2021, 8, 1), date(2023, 5, 1)),
    ]
    assert titles_after_filtering(entries) == ["Newest", "Middle", "Oldest"]

def test_an_ongoing_role_is_placed_by_its_start_date_not_by_its_open_end_date():
    # An entry with no end_date is ongoing. It must not be treated as the most
    # recent thing on the CV - only its start_date decides where it sits.
    entries = [
        dated_entry("Recent finished role", date(2023, 5, 1), date(2025, 1, 1)),
        dated_entry("Long-running old role", date(2017, 1, 1)),
    ]
    assert titles_after_filtering(entries) == ["Recent finished role", "Long-running old role"]

def test_sorting_ignores_entries_that_were_filtered_out():
    entries = [
        dated_entry("Kept old", date(2017, 1, 1)),
        dated_entry("Kept new", date(2023, 1, 1)),
    ]
    entries.insert(1, dated_entry("Dropped newest", date(2025, 1, 1)))
    entries[1].tags = ["niche"]
    assert titles_after_filtering(entries) == ["Kept new", "Kept old"]
