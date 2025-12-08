-- Create videos table
CREATE TABLE IF NOT EXISTS videos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_size INTEGER NOT NULL,
    duration FLOAT,
    fps FLOAT,
    width INTEGER,
    height INTEGER,
    codec VARCHAR(50),
    storage_path VARCHAR(500) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    frames_extracted INTEGER DEFAULT 0,
    frames_total INTEGER,
    error_message TEXT,
    uploaded_at TIMESTAMP DEFAULT NOW(),
    processing_started_at TIMESTAMP,
    processing_completed_at TIMESTAMP,
    upload_user_id VARCHAR(100),
    video_metadata TEXT
);

-- Create frames table
CREATE TABLE IF NOT EXISTS frames (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id UUID NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
    frame_number INTEGER NOT NULL,
    timestamp FLOAT NOT NULL,
    storage_path VARCHAR(500) NOT NULL,
    file_size INTEGER,
    detection_completed BOOLEAN DEFAULT FALSE,
    detection_id UUID,
    extracted_at TIMESTAMP DEFAULT NOW(),
    latitude FLOAT,
    longitude FLOAT,
    altitude FLOAT
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_videos_status ON videos(status);
CREATE INDEX IF NOT EXISTS idx_videos_uploaded_at ON videos(uploaded_at);
CREATE INDEX IF NOT EXISTS idx_frames_video_id ON frames(video_id);
CREATE INDEX IF NOT EXISTS idx_frames_detection_completed ON frames(detection_completed);
CREATE INDEX IF NOT EXISTS idx_frames_timestamp ON frames(timestamp);

-- Add comments
COMMENT ON TABLE videos IS 'Uploaded videos for processing';
COMMENT ON TABLE frames IS 'Extracted frames from videos';
