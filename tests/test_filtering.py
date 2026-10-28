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
    Variant,
)
from renderer.render import (
    filter_categorised,
    filter_entry_list_dated,
    filter_free_text,
    filter_sections,
    filter_tagged_list,
    matches,
    resolve_tags,
)

def dated_entry(title, tags, start_date=date(2020, 1, 1)):
    return DatedEntry(
        title=title,
        organisation="Crown Gas & Power",
        start_date=start_date,
        highlights=["Did the thing."],
        tags=tags,
    )

def category(name, tags):
    return Category(name=name, items=["Python"], tags=tags)

def tagged_entry(name, tags):
    return TaggedEntry(name=name, details=["Built the thing."], tags=tags)

class TestMatches:
    def test_true_when_one_tag_overlaps(self):
        assert matches(["core", "backend"], {"backend"}) is True

    def test_false_when_no_tag_overlaps(self):
        assert matches(["backend"], {"frontend"}) is False

    def test_false_when_the_item_has_no_tags(self):
        assert matches([], {"core"}) is False

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
