from __future__ import annotations

import httpx

from discovery.retrieval.direct.arxiv import ArxivProvider
from discovery.retrieval.direct.crossref import CrossrefProvider
from discovery.retrieval.direct.europe_pmc import EuropePMCProvider
from discovery.retrieval.direct.openalex import OpenAlexProvider
from discovery.retrieval.models import SearchQuery


def test_openalex_search_normalizes_work_and_assets() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/works"
        return httpx.Response(
            200,
            json={
                "results": [
                    {
                        "id": "https://openalex.org/W123",
                        "doi": "https://doi.org/10.1000/example",
                        "display_name": "Spectral example",
                        "publication_year": 2024,
                        "type": "article",
                        "language": "en",
                        "authorships": [
                            {
                                "author": {
                                    "id": "https://openalex.org/A1",
                                    "display_name": "Ada Researcher",
                                }
                            }
                        ],
                        "abstract_inverted_index": {"spectral": [0], "method": [1]},
                        "primary_location": {
                            "pdf_url": "https://example.test/paper.pdf",
                            "landing_page_url": "https://example.test/paper",
                        },
                    }
                ]
            },
            request=request,
        )

    client = httpx.Client(
        transport=httpx.MockTransport(handler), base_url="https://api.openalex.org"
    )
    provider = OpenAlexProvider(client=client)
    response = provider.search(SearchQuery(text="spectral", limit=5))
    assert len(response.hits) == 1
    work = response.hits[0].work
    assert work is not None
    assert work.title == "Spectral example"
    assert work.abstract == "spectral method"
    assert {item.scheme.value for item in work.identifiers} >= {"openalex", "doi"}
    assert len(work.assets) == 2
    assert work.assets[0].rights is not None
    assert work.assets[0].rights.tdm == "unknown"


def test_crossref_search_normalizes_doi() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "message": {
                    "items": [
                        {
                            "DOI": "10.1000/CROSSREF",
                            "title": ["Crossref work"],
                            "published": {"date-parts": [[2023, 1, 1]]},
                            "author": [{"given": "Ada", "family": "Lovelace"}],
                        }
                    ]
                }
            },
            request=request,
        )

    client = httpx.Client(
        transport=httpx.MockTransport(handler), base_url="https://api.crossref.org"
    )
    response = CrossrefProvider(client=client).search(SearchQuery(text="test", limit=1))
    work = response.hits[0].work
    assert work is not None
    assert work.identifiers[0].value == "10.1000/crossref"
    assert work.publication_year == 2023


def test_europe_pmc_search_preserves_pmid_pmcid_and_doi() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "resultList": {
                    "result": [
                        {
                            "id": "123",
                            "pmid": "123",
                            "pmcid": "PMC456",
                            "doi": "10.1000/epmc",
                            "title": "Europe PMC work",
                            "pubYear": "2022",
                            "abstractText": "An abstract.",
                            "authorList": {"author": [{"fullName": "Ada Researcher"}]},
                        }
                    ]
                }
            },
            request=request,
        )

    client = httpx.Client(
        transport=httpx.MockTransport(handler),
        base_url="https://www.ebi.ac.uk/europepmc/webservices/rest",
    )
    response = EuropePMCProvider(client=client).search(SearchQuery(text="biology", limit=1))
    work = response.hits[0].work
    assert work is not None
    assert {item.scheme.value for item in work.identifiers} == {"pmid", "pmcid", "doi"}
    assert work.publication_year == 2022


def test_arxiv_atom_search_preserves_preprint_identity() -> None:
    atom = """<?xml version='1.0' encoding='UTF-8'?>
<feed xmlns='http://www.w3.org/2005/Atom' xmlns:arxiv='http://arxiv.org/schemas/atom'>
  <entry>
    <id>http://arxiv.org/abs/2401.12345v2</id>
    <updated>2024-02-01T00:00:00Z</updated>
    <published>2024-01-01T00:00:00Z</published>
    <title>Quantum-free scientific test</title>
    <summary>We solve a graph problem.</summary>
    <author><name>Ada Researcher</name></author>
    <link href='https://arxiv.org/abs/2401.12345v2' rel='alternate' type='text/html'/>
    <link href='https://arxiv.org/pdf/2401.12345v2' rel='related'
          type='application/pdf' title='pdf'/>
    <arxiv:primary_category term='cs.DS'/>
  </entry>
</feed>"""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=atom, request=request)

    client = httpx.Client(
        transport=httpx.MockTransport(handler), base_url="https://export.arxiv.org"
    )
    response = ArxivProvider(client=client).search(SearchQuery(text="graph", limit=1))
    work = response.hits[0].work
    assert work is not None
    assert work.identifiers[0].scheme.value == "arxiv"
    assert work.identifiers[0].value.startswith("2401.12345")
    assert work.work_type == "preprint"
