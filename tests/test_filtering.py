from datetime import date

from renderer.models import (
    Categorised,
    Category,
    DatedEntry,
    EntryListDated,
    FreeText,
    Manifest,
    Section,
    TaggedEntry,
    TaggedList,
    TaggedText,
    Variant,
)
from renderer.render import (
    filter_categorised,
    filter_entry_list_dated,
    filter_free_text,
    filter_lines,
    filter_sections,
    filter_tagged_list,
    matches,
    resolve_tags,
)

def dated_entry(title, tags, start_date=date(2020, 1, 1), highlights=None):
    return DatedEntry(
        title=title,
        organisation="Crown Gas & Power",
        start_date=start_date,
        highlights=highlights if highlights is not None else ["Did the thing."],
        tags=tags,
    )

def category(name, tags, items=None):
    return Category(name=name, items=items if items is not None else ["Python"], tags=tags)

def tagged_entry(name, tags, details=None):
    return TaggedEntry(
        name=name,
        details=details if details is not None else ["Built the thing."],
        tags=tags,
    )

class TestMatches:
    def test_true_when_one_tag_overlaps(self):
        assert matches(["core", "backend"], {"backend"}) is True

    def test_false_when_no_tag_overlaps(self):
        assert matches(["backend"], {"frontend"}) is False

    def test_false_when_the_item_has_no_tags(self):
        assert matches([], {"core"}) is False

class TestFilterLines:
    def test_an_untagged_line_is_always_kept(self):
        assert filter_lines(["Always here."], {"core"}) == ["Always here."]

    def test_a_tagged_line_is_kept_as_plain_text_when_it_matches(self):
        lines = [TaggedText(text="CI and AWS.", tags=["devops"])]
        assert filter_lines(lines, {"core", "devops"}) == ["CI and AWS."]

    def test_a_tagged_line_is_dropped_when_it_does_not_match(self):
        lines = [TaggedText(text="CI and AWS.", tags=["devops"])]
        assert filter_lines(lines, {"core"}) == []

    def test_source_order_is_kept_across_untagged_and_tagged_lines(self):
        lines = [
            "First.",
            TaggedText(text="Second.", tags=["devops"]),
            TaggedText(text="Dropped.", tags=["frontend"]),
            "Third.",
        ]
        assert filter_lines(lines, {"core", "devops"}) == ["First.", "Second.", "Third."]

class TestFreeText:
    def test_kept_when_tagged(self):
        data = FreeText(text="A summary.", tags=["core"])
        assert filter_free_text(data, {"core"}) is data

    def test_dropped_when_not_tagged(self):
        data = FreeText(text="A summary.", tags=["niche"])
        assert filter_free_text(data, {"core"}) is None

class TestEntryListDated:
    def test_keeps_only_matching_entries(self):
        data = EntryListDated(entries=[
            dated_entry("Kept", ["core"]),
            dated_entry("Dropped", ["niche"]),
        ])
        filtered = filter_entry_list_dated(data, {"core"})
        assert [entry.title for entry in filtered.entries] == ["Kept"]

    def test_returns_none_when_nothing_matches(self):
        data = EntryListDated(entries=[dated_entry("Dropped", ["niche"])])
        assert filter_entry_list_dated(data, {"core"}) is None

    def test_a_core_entry_does_not_bring_in_its_tagged_highlights(self):
        # "core" on the entry means "always show this job", not "show every
        # bullet in the fact bank" - a tagged bullet still has to match.
        data = EntryListDated(entries=[dated_entry("Developer", ["core"], highlights=[
            "Untagged.",
            TaggedText(text="Only for DevOps roles.", tags=["devops"]),
        ])])
        filtered = filter_entry_list_dated(data, {"core"})
        assert filtered.entries[0].highlights == ["Untagged."]

    def test_an_entry_whose_highlights_are_all_filtered_out_is_still_shown(self):
        data = EntryListDated(entries=[dated_entry("Developer", ["core"], highlights=[
            TaggedText(text="Only for DevOps roles.", tags=["devops"]),
        ])])
        filtered = filter_entry_list_dated(data, {"core"})
        assert [entry.title for entry in filtered.entries] == ["Developer"]
        assert filtered.entries[0].highlights == []

    def test_filtering_does_not_change_the_loaded_data(self):
        tagged = TaggedText(text="Only for DevOps roles.", tags=["devops"])
        data = EntryListDated(entries=[dated_entry("Developer", ["core"], highlights=[tagged])])
        filter_entry_list_dated(data, {"core"})
        assert data.entries[0].highlights == [tagged]

class TestCategorised:
    def test_keeps_only_matching_categories(self):
        data = Categorised(categories=[
            category("Languages", ["core"]),
            category("Hobbies", ["niche"]),
        ])
        filtered = filter_categorised(data, {"core"})
        assert [item.name for item in filtered.categories] == ["Languages"]

    def test_returns_none_when_nothing_matches(self):
        data = Categorised(categories=[category("Hobbies", ["niche"])])
        assert filter_categorised(data, {"core"}) is None

    def test_keeps_only_matching_items_within_a_category(self):
        data = Categorised(categories=[category("Languages", ["core"], items=[
            "Python",
            TaggedText(text="Rust", tags=["backend"]),
            TaggedText(text="jQuery", tags=["frontend"]),
        ])])
        filtered = filter_categorised(data, {"core", "backend"})
        assert filtered.categories[0].items == ["Python", "Rust"]

    def test_a_category_whose_items_are_all_filtered_out_is_dropped(self):
        data = Categorised(categories=[
            category("Languages", ["core"]),
            category("Systems", ["core"], items=[TaggedText(text="C", tags=["embedded"])]),
        ])
        filtered = filter_categorised(data, {"core"})
        assert [item.name for item in filtered.categories] == ["Languages"]

class TestTaggedList:
    def test_keeps_only_matching_entries(self):
        data = TaggedList(entries=[
            tagged_entry("Fusion", ["core"]),
            tagged_entry("Side project", ["niche"]),
        ])
        filtered = filter_tagged_list(data, {"core"})
        assert [entry.name for entry in filtered.entries] == ["Fusion"]

    def test_returns_none_when_nothing_matches(self):
        data = TaggedList(entries=[tagged_entry("Side project", ["niche"])])
        assert filter_tagged_list(data, {"core"}) is None

    def test_keeps_only_matching_details_within_an_entry(self):
        data = TaggedList(entries=[tagged_entry("Fusion", ["core"], details=[
            "Untagged.",
            TaggedText(text="Rust pricing engine.", tags=["rust"]),
            TaggedText(text="Nuxt frontend.", tags=["frontend"]),
        ])])
        filtered = filter_tagged_list(data, {"core", "rust"})
        assert filtered.entries[0].details == ["Untagged.", "Rust pricing engine."]

class TestResolveTags:
    def test_core_is_added_to_the_variant_tags(self):
        assert resolve_tags(Variant(include_tags=["backend"])) == {"backend", "core"}

    def test_core_is_not_duplicated_when_the_variant_lists_it(self):
        assert resolve_tags(Variant(include_tags=["core"])) == {"core"}

    def test_core_alone_when_the_variant_lists_nothing(self):
        assert resolve_tags(Variant(include_tags=[])) == {"core"}

class TestFilterSections:
    def manifest(self):
        return Manifest(sections=[
            Section(name="summary", shape="free_text", file="summary.yaml"),
            Section(name="experience", shape="entry_list_dated", file="experience.yaml"),
            Section(name="skills", shape="categorised", file="skills.yaml"),
        ])

    def sections(self, experience_tags):
        return {
            "summary": FreeText(text="A summary.", tags=["core"]),
            "experience": EntryListDated(entries=[dated_entry("Developer", experience_tags)]),
            "skills": Categorised(categories=[category("Languages", ["core"])]),
        }

    def test_output_follows_manifest_order_not_dictionary_order(self):
        filtered = filter_sections(self.sections(["core"]), self.manifest(), {"core"})
        assert [section["name"] for section in filtered] == ["summary", "experience", "skills"]

    def test_a_section_with_no_matching_entries_is_left_out_entirely(self):
        filtered = filter_sections(self.sections(["niche"]), self.manifest(), {"core"})
        assert [section["name"] for section in filtered] == ["summary", "skills"]

    def test_each_section_carries_its_shape_through(self):
        filtered = filter_sections(self.sections(["core"]), self.manifest(), {"core"})
        assert [section["shape"] for section in filtered] == [
            "free_text", "entry_list_dated", "categorised",
        ]
