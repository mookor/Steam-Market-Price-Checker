
-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- User table
CREATE TABLE users (
    id UUID PRIMARY KEY,
    subscriber BOOLEAN DEFAULT FALSE,
    telegram_id INTEGER NOT NULL,
    currency VARCHAR(3) NOT NULL
);

-- Items table (normalized - no duplication)
CREATE TABLE items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    listing_id INTEGER NOT NULL,
    name VARCHAR(255) NOT NULL,
    current_price_usd REAL NOT NULL,
    current_price_rub REAL NOT NULL,
    url VARCHAR(500) NOT NULL
);

-- User item watchlist (many-to-many relationship)
CREATE TABLE user_item_watchlist (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    item_id UUID NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    buy_target_price REAL NOT NULL CHECK (buy_target_price >= 0),
    sell_target_price REAL NOT NULL CHECK (sell_target_price >= 0),
    url VARCHAR(500) NOT NULL,
    
    -- Check that sell price is greater than buy price
    CONSTRAINT price_check CHECK (sell_target_price > buy_target_price),
    -- Ensure one user can't have duplicate watchlist entries for the same item
    CONSTRAINT unique_user_item_watchlist UNIQUE (user_id, item_id)
);


-- Create indexes for optimization
-- Items table indexes
CREATE INDEX idx_items_listing_id ON items(listing_id);
CREATE INDEX idx_items_name ON items(name);
CREATE INDEX idx_items_current_price_usd ON items(current_price_usd);
CREATE INDEX idx_items_current_price_rub ON items(current_price_rub);

-- Watchlist table indexes
CREATE INDEX idx_watchlist_user_id ON user_item_watchlist(user_id);
CREATE INDEX idx_watchlist_item_id ON user_item_watchlist(item_id);
CREATE INDEX idx_watchlist_prices ON user_item_watchlist(buy_target_price, sell_target_price);





-- Comments to tables
COMMENT ON TABLE users IS 'Table of users in the system';
COMMENT ON TABLE items IS 'Table of Steam items (normalized, no duplication)';
COMMENT ON TABLE user_item_watchlist IS 'Many-to-many table linking users to items they want to track with their target prices';

COMMENT ON COLUMN items.listing_id IS 'ID item in Steam system (unique)';
COMMENT ON COLUMN items.name IS 'Name of item (e.g. Fracture Case)';
COMMENT ON COLUMN items.current_price_usd IS 'Current market price of the item in USD';
COMMENT ON COLUMN items.current_price_rub IS 'Current market price of the item in RUB';
