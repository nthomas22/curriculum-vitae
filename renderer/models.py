from datetime import date
from pydantic import BaseModel

class Category(BaseModel):
    name: str
    items: list[str]
    tags: list[str]

class DatedEntry(BaseModel):
    title: str
    organisation: str
    start_date: date
    end_date: date | None = None
    highlights: list[str]
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
    details: list[str]
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