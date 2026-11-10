#!/bin/bash
# Database initialization script
# Note: Do not use 'set -e' as this script is sourced by postgresql-start hooks

# Wait for postgres to be ready
until pg_isready -U "$POSTGRESQL_USER" -d "$POSTGRESQL_DATABASE" > /dev/null 2>&1; do
    sleep 1
done

# Run init SQL
psql -v ON_ERROR_STOP=1 --username "$POSTGRESQL_USER" --dbname "$POSTGRESQL_DATABASE" <<-EOSQL
    CREATE TABLE IF NOT EXISTS reviews (
        id SERIAL PRIMARY KEY,
        original_text TEXT NOT NULL,
        preprocessed_text TEXT NOT NULL,
        sentiment VARCHAR(20) NOT NULL CHECK (sentiment IN ('positive', 'negative', 'neutral')),
        compound_score REAL NOT NULL,
        positive_score REAL NOT NULL,
        negative_score REAL NOT NULL,
        neutral_score REAL NOT NULL,
        created_at TIMESTAMP NOT NULL DEFAULT NOW()
    );

    CREATE INDEX IF NOT EXISTS idx_reviews_sentiment ON reviews(sentiment);
    CREATE INDEX IF NOT EXISTS idx_reviews_created_at ON reviews(created_at DESC);
    CREATE INDEX IF NOT EXISTS idx_reviews_compound_score ON reviews(compound_score);

    -- Add comments
    COMMENT ON TABLE reviews IS 'Stores analyzed product and movie reviews with sentiment scores';
    COMMENT ON COLUMN reviews.compound_score IS 'Overall sentiment score from -1 (most negative) to 1 (most positive)';
EOSQL
