# YojanaVaani — Data Pipeline

This directory holds the data scraping, ingestion, and vector-indexing scripts to be implemented in **Phase 2 — Scheme Database**:

1. `scrape_schemes.py`: Scrapes schemes across 4–5 priority categories from [myScheme.gov.in](https://www.myscheme.gov.in/).
2. `load_schemes.py`: Loads structured scheme data into PostgreSQL `schemes` table.
3. `build_index.py`: Embeds scheme criteria using `paraphrase-multilingual-mpnet-base-v2` into Chroma.
4. `test_retrieval.py`: CLI tool for testing multi-category semantic retrieval.
