-- User feedback table for loan number verification
CREATE TABLE IF NOT EXISTS loan_call_feedback (
    id INT AUTO_INCREMENT PRIMARY KEY,
    orkuid VARCHAR(100) NOT NULL,
    loan_number VARCHAR(20),
    is_relevant BOOLEAN DEFAULT NULL,  -- thumbs up/down
    corrected_loan_number VARCHAR(20), -- user can type correct loan
    feedback_type ENUM('irrelevant', 'wrong_loan', 'confirmed', 'corrected'),
    user_id VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_orkuid (orkuid),
    INDEX idx_loan (loan_number),
    UNIQUE KEY unique_feedback (orkuid, loan_number, user_id)
);

-- Track loan officer accuracy
CREATE TABLE IF NOT EXISTS loan_officer_accuracy (
    phone_number VARCHAR(50) PRIMARY KEY,
    total_calls INT DEFAULT 0,
    relevant_calls INT DEFAULT 0,
    irrelevant_calls INT DEFAULT 0,
    accuracy_rate DECIMAL(5,2),
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);