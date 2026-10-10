DROP TABLE IF EXISTS `support_tickets`;
CREATE TABLE `support_tickets` (
  `ticket_id` VARCHAR(50) NOT NULL,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `resolved_at` DATETIME DEFAULT NULL,
  `agent` VARCHAR(100) DEFAULT NULL,
  `priority` VARCHAR(20) DEFAULT NULL,       -- e.g., 'Low', 'Medium', 'High'
  `num_interactions` INT DEFAULT 0,          -- Numbers should be integers
  `issue_category` VARCHAR(100) DEFAULT NULL,-- Fixed the typo 'IssUeCat' to standard snake_case
  `channel` VARCHAR(50) DEFAULT NULL,        -- e.g., 'Email', 'Chat', 'Phone'
  `status` VARCHAR(20) DEFAULT 'Open',       -- e.g., 'Open', 'In Progress', 'Resolved'
  `agent_feedback` TEXT DEFAULT NULL,        -- Actual paragraph text is perfect for the TEXT type
  PRIMARY KEY (`ticket_id`)                  -- Added a primary key for faster lookups
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
