-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;

-- Videos table
CREATE TABLE IF NOT EXISTS videos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    filename VARCHAR(255) NOT NULL,
    device_id VARCHAR(100),
    file_size_bytes BIGINT,
    duration_seconds FLOAT,
    resolution VARCHAR(20),
    fps FLOAT,
    uploaded_at TIMESTAMP DEFAULT NOW(),
    processing_status VARCHAR(50) DEFAULT 'pending',
    frame_count INTEGER,
    minio_path TEXT,
    recorded_at TIMESTAMP
);

-- Extracted frames table
CREATE TABLE IF NOT EXISTS frames (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    video_id UUID REFERENCES videos(id) ON DELETE CASCADE,
    frame_number INTEGER NOT NULL,
    timestamp_ms BIGINT,
    minio_path TEXT NOT NULL,
    width INTEGER,
    height INTEGER,
    extracted_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(video_id, frame_number)
);

-- Detection results table
CREATE TABLE IF NOT EXISTS detection_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    image_id VARCHAR(255) UNIQUE NOT NULL,
    frame_id UUID REFERENCES frames(id) ON DELETE CASCADE,
    frame_path TEXT,
    annotated_image_path TEXT,
    total_defects INTEGER DEFAULT 0,
    detection_timestamp TIMESTAMP DEFAULT NOW(),
    model_version VARCHAR(50),
    processing_time_ms FLOAT
);

-- Defects table
CREATE TABLE IF NOT EXISTS defects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    detection_result_id UUID REFERENCES detection_results(id) ON DELETE CASCADE,
    class_name VARCHAR(50) NOT NULL,
    confidence FLOAT NOT NULL,
    bbox_x_min FLOAT NOT NULL,
    bbox_y_min FLOAT NOT NULL,
    bbox_x_max FLOAT NOT NULL,
    bbox_y_max FLOAT NOT NULL,
    area_pixels INTEGER,
    mask_path TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Severity scores table
CREATE TABLE IF NOT EXISTS severity_scores (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    defect_id UUID REFERENCES defects(id) ON DELETE CASCADE,
    severity_score FLOAT CHECK (severity_score BETWEEN 0 AND 10),
    risk_category VARCHAR(20),
    risk_score FLOAT,
    computed_at TIMESTAMP DEFAULT NOW(),
    model_version VARCHAR(50)
);

-- GPS metadata table
CREATE TABLE IF NOT EXISTS gps_metadata (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    frame_id UUID REFERENCES frames(id) ON DELETE CASCADE,
    location GEOGRAPHY(POINT, 4326),
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    altitude DOUBLE PRECISION,
    speed DOUBLE PRECISION,
    heading DOUBLE PRECISION,
    timestamp_ms BIGINT,
    accuracy FLOAT
);

-- IMU metadata table
CREATE TABLE IF NOT EXISTS imu_metadata (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    frame_id UUID REFERENCES frames(id) ON DELETE CASCADE,
    accel_x FLOAT,
    accel_y FLOAT,
    accel_z FLOAT,
    gyro_x FLOAT,
    gyro_y FLOAT,
    gyro_z FLOAT,
    timestamp_ms BIGINT
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_videos_status ON videos(processing_status);
CREATE INDEX IF NOT EXISTS idx_frames_video ON frames(video_id);
CREATE INDEX IF NOT EXISTS idx_detection_image ON detection_results(image_id);
CREATE INDEX IF NOT EXISTS idx_defects_class ON defects(class_name);
CREATE INDEX IF NOT EXISTS idx_defects_detection ON defects(detection_result_id);
CREATE INDEX IF NOT EXISTS idx_severity_category ON severity_scores(risk_category);
CREATE INDEX IF NOT EXISTS idx_severity_score ON severity_scores(severity_score DESC);
CREATE INDEX IF NOT EXISTS idx_gps_frame ON gps_metadata(frame_id);
CREATE INDEX IF NOT EXISTS idx_gps_location ON gps_metadata USING GIST(location);

-- Insert sample data for testing (optional)
-- This can be removed in production
COMMENT ON TABLE videos IS 'Stores uploaded video metadata';
COMMENT ON TABLE frames IS 'Stores extracted frames from videos';
COMMENT ON TABLE detection_results IS 'Stores defect detection results';
COMMENT ON TABLE defects IS 'Stores individual defect detections';
COMMENT ON TABLE severity_scores IS 'Stores severity and risk scores for defects';
COMMENT ON TABLE gps_metadata IS 'Stores GPS coordinates for frames';
COMMENT ON TABLE imu_metadata IS 'Stores IMU sensor data for frames';
