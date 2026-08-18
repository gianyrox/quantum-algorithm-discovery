# Coverage, Saturation, and Retrieval Feedback v0.10

## Coverage is multidimensional

The system stratifies works by discipline, decade, language, document type, provider, and access status. A field with 10,000 retrieved papers can still be under-covered if all records come from one provider, one era, or one language.

## Discovery yield

Each iteration tracks newly recovered works, terms, concepts, citation edges, and problem signatures. The normalized novelty signal is deliberately broader than new-work count so vocabulary and structural discovery can keep a search open after bibliographic novelty alone declines.

## Audited saturation

A search is saturated only when:

1. the minimum number of iterations has run;
2. recent normalized novelty remains below the configured threshold; and
3. coverage strata are stable when that requirement is enabled.

This is an empirical stopping claim, not a claim that all relevant science has been found.

## Active retrieval

Retrieval priority combines uncertainty, recent novelty, coverage gap, historical gap, and provider disagreement. This directs future search budget toward places with the highest expected information value rather than applying equal fixed quotas to every field.

## Unknown vocabulary

Candidate terms from corpus language are reviewable objects. They can be accepted as retrieval-only terms, mapped to an existing concept, proposed as a new concept, or rejected as ambiguity/noise. Candidate corpus language never silently modifies a source ontology.
