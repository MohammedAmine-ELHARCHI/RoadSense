-- Migration 004: Create GeoRef tables for spatial analysis

-- Enable PostGIS if not already enabled
CREATE EXTENSION IF NOT EXISTS postgis;

-- Create road_segments table
CREATE TABLE IF NOT EXISTS road_segments (
    id SERIAL PRIMARY KEY,
    osm_id VARCHAR(100) UNIQUE,
    name VARCHAR(255),
    road_type VARCHAR(50),
    surface VARCHAR(50),
    max_speed INTEGER,
    lanes INTEGER,
    one_way BOOLEAN DEFAULT FALSE,
    geometry GEOMETRY(LINESTRING, 4326) NOT NULL,
    length_meters FLOAT,
    traffic_importance INTEGER DEFAULT 5,
    last_maintenance_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create georeferenced_defects table
CREATE TABLE IF NOT EXISTS georeferenced_defects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    detection_id UUID NOT NULL,
    frame_id UUID,
    segment_id INTEGER REFERENCES road_segments(id),
    gps_location GEOMETRY(POINT, 4326),
    matched_location GEOMETRY(POINT, 4326),
    distance_to_road FLOAT,
    confidence FLOAT,
    heading FLOAT,
    defect_type VARCHAR(50),
    severity_score FLOAT,
    is_matched BOOLEAN DEFAULT FALSE,
    needs_review BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create spatial_indexes table for metadata
CREATE TABLE IF NOT EXISTS spatial_indexes (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(100) NOT NULL,
    column_name VARCHAR(100) NOT NULL,
    index_name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_road_segments_osm_id ON road_segments(osm_id);
CREATE INDEX IF NOT EXISTS idx_road_segments_geometry ON road_segments USING GIST(geometry);
CREATE INDEX IF NOT EXISTS idx_road_segments_type ON road_segments(road_type);

CREATE INDEX IF NOT EXISTS idx_georef_detection_id ON georeferenced_defects(detection_id);
CREATE INDEX IF NOT EXISTS idx_georef_segment_id ON georeferenced_defects(segment_id);
CREATE INDEX IF NOT EXISTS idx_georef_gps_location ON georeferenced_defects USING GIST(gps_location);
CREATE INDEX IF NOT EXISTS idx_georef_matched_location ON georeferenced_defects USING GIST(matched_location);
CREATE INDEX IF NOT EXISTS idx_georef_is_matched ON georeferenced_defects(is_matched);
CREATE INDEX IF NOT EXISTS idx_georef_needs_review ON georeferenced_defects(needs_review);
CREATE INDEX IF NOT EXISTS idx_georef_defect_type ON georeferenced_defects(defect_type);

-- Insert sample road segment for testing (if needed)
-- This is a sample road in Casablanca, Morocco
INSERT INTO road_segments (osm_id, name, road_type, geometry, length_meters, traffic_importance)
VALUES (
    'sample_road_1',
    'Boulevard Mohammed V',
    'primary',
    ST_GeomFromText('LINESTRING(-7.6177 33.5881, -7.6167 33.5891)', 4326),
    150.0,
    8
) ON CONFLICT (osm_id) DO NOTHING;

-- Record spatial indexes
INSERT INTO spatial_indexes (table_name, column_name, index_name)
VALUES 
    ('road_segments', 'geometry', 'idx_road_segments_geometry'),
    ('georeferenced_defects', 'gps_location', 'idx_georef_gps_location'),
    ('georeferenced_defects', 'matched_location', 'idx_georef_matched_location')
ON CONFLICT DO NOTHING;

-- Migration complete
