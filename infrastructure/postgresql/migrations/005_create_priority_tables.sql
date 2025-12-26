-- Migration 005: Create Priorisation tables

-- Create priority_scores table
CREATE TABLE IF NOT EXISTS priority_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    segment_id INTEGER NOT NULL,
    
    -- Priority components (0-100 scale)
    severity_score FLOAT NOT NULL,
    traffic_score FLOAT DEFAULT 50.0,
    density_score FLOAT DEFAULT 50.0,
    age_score FLOAT DEFAULT 50.0,
    accessibility_score FLOAT DEFAULT 50.0,
    
    -- Final priority score (0-100 scale)
    total_priority_score FLOAT NOT NULL,
    priority_level VARCHAR(20) NOT NULL,
    
    -- Metadata
    defect_count INTEGER DEFAULT 0,
    avg_severity FLOAT,
    max_severity FLOAT,
    road_name VARCHAR(255),
    road_type VARCHAR(50),
    
    -- Maintenance info
    estimated_cost FLOAT,
    estimated_duration_days INTEGER,
    maintenance_urgency VARCHAR(50),
    last_inspection_date TIMESTAMP,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_segment FOREIGN KEY (segment_id) REFERENCES road_segments(id) ON DELETE CASCADE,
    CONSTRAINT unique_segment_priority UNIQUE (segment_id)
);

-- Create maintenance_tasks table
CREATE TABLE IF NOT EXISTS maintenance_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    segment_id INTEGER NOT NULL,
    
    -- Task details
    task_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'PENDING',
    priority_score FLOAT NOT NULL,
    
    -- Scheduling
    scheduled_date TIMESTAMP,
    completion_date TIMESTAMP,
    assigned_team VARCHAR(100),
    
    -- Cost
    estimated_cost FLOAT,
    actual_cost FLOAT,
    
    -- Notes
    description TEXT,
    notes TEXT,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_priority_segment_id ON priority_scores(segment_id);
CREATE INDEX IF NOT EXISTS idx_priority_score ON priority_scores(total_priority_score DESC);
CREATE INDEX IF NOT EXISTS idx_priority_level ON priority_scores(priority_level);
CREATE INDEX IF NOT EXISTS idx_priority_calculated ON priority_scores(calculated_at DESC);

CREATE INDEX IF NOT EXISTS idx_task_segment_id ON maintenance_tasks(segment_id);
CREATE INDEX IF NOT EXISTS idx_task_status ON maintenance_tasks(status);
CREATE INDEX IF NOT EXISTS idx_task_scheduled ON maintenance_tasks(scheduled_date);
CREATE INDEX IF NOT EXISTS idx_task_priority ON maintenance_tasks(priority_score DESC);

-- Migration complete
