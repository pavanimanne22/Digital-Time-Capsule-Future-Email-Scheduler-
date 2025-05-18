            CREATE TABLE IF NOT EXISTS messages (
                id INT AUTO_INCREMENT PRIMARY KEY, 
                recipient_email TEXT, 
                cc_emails TEXT, 
                bcc_emails TEXT,
                subject VARCHAR(255), 
                message_text TEXT, 
                scheduled_date DATETIME, 
                status ENUM('pending', 'sent') DEFAULT 'pending',
                attachment_path VARCHAR(500) NULL
            )