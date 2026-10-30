from datetime import date
from pydantic import BaseModel

# A line that only appears when its own tags match the variant. Lines written as
# plain strings have no tags of their own and appear whenever their parent does.
class TaggedText(BaseModel):
    text: str
    tags: list[str]

class Category(BaseModel):
    name: str
    items: list[str | TaggedText]
    tags: list[str]

class DatedEntry(BaseModel):
    title: str
    organisation: str
    start_date: date
    end_date: date | None = None
    highlights: list[str | TaggedText]
    tags: list[str]

class Link(BaseModel):
    text: str
    url: str

class Section(BaseModel):
    name: str
    shape: str
    file: str

class TaggedEntry(BaseModel):
    name: str
    organisation: str | None = None
    details: list[str | TaggedText]
    tech: list[str] = []
    tags: list[str]

class Categorised(BaseModel):
    categories: list[Category]

class Contact(BaseModel):
    name: str
    email: str
    links: list[Link]

class EntryListDated(BaseModel):
    entries: list[DatedEntry]

class FreeText(BaseModel):
    text: str
    tags: list[str]

class Manifest(BaseModel):
    sections: list[Section]

class TaggedList(BaseModel):
    entries: list[TaggedEntry]

class Variant(BaseModel):
    include_tags: list[str]