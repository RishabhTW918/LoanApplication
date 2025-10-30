-- Create UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create applications table
CREATE TABLE IF NOT EXISTS applications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pan_number VARCHAR(10) NOT NULL,
    applicant_name VARCHAR(255),
    monthly_income_inr DECIMAL(12, 2) NOT NULL CHECK (monthly_income_inr > 0),
    loan_amount_inr DECIMAL(12, 2) NOT NULL CHECK (loan_amount_inr > 0),
    loan_type VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    cibil_score INTEGER CHECK (cibil_score >= 300 AND cibil_score <= 900),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_status CHECK (status IN ('PENDING', 'PRE_APPROVED', 'REJECTED', 'MANUAL_REVIEW')),
    CONSTRAINT chk_loan_type CHECK (loan_type IN ('PERSONAL', 'HOME', 'AUTO'))
);

-- Create index for faster lookups
CREATE INDEX idx_applications_pan ON applications(pan_number);
CREATE INDEX idx_applications_status ON applications(status);
CREATE INDEX idx_applications_created_at ON applications(created_at DESC);

-- Create updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_applications_updated_at
    BEFORE UPDATE ON applications
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();