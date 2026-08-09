-- =========================================================================
-- UECS3203 Advanced Database Systems - Assignment 1
-- Section 4 & 5: CRUD Operations and Transaction Management
-- Dataset: Airbnb Open Data (table: airbnb_listings)
-- =========================================================================

USE airbnb_db;   -- change to your actual schema name

-- -------------------------------------------------------------------------
-- Reference: expected table structure (created already by main.py import)
-- -------------------------------------------------------------------------
-- CREATE TABLE airbnb_listings (
--     id                              BIGINT PRIMARY KEY,
--     name                            VARCHAR(255),
--     host_id                         BIGINT,
--     host_identity_verified          VARCHAR(20),
--     host_name                       VARCHAR(100),
--     neighbourhood_group             VARCHAR(50),
--     neighbourhood                   VARCHAR(100),
--     lat                             DECIMAL(9,6),
--     long                            DECIMAL(9,6),
--     country                         VARCHAR(50),
--     country_code                    VARCHAR(5),
--     instant_bookable                VARCHAR(5),
--     cancellation_policy             VARCHAR(20),
--     room_type                       VARCHAR(50),
--     construction_year               INT,
--     price                           DECIMAL(10,2),
--     service_fee                     DECIMAL(10,2),
--     minimum_nights                  INT,
--     number_of_reviews               INT,
--     last_review                     DATE,
--     reviews_per_month               DECIMAL(5,2),
--     review_rate_number              INT,
--     calculated_host_listings_count  INT,
--     availability_365                INT,
--     house_rules                     TEXT,
--     license                         VARCHAR(50)
-- );

-- =========================================================================
-- 4. CRUD OPERATIONS
-- =========================================================================

-- -------------------------------------------------------------------------
-- 4a. CREATE - insert a new listing
-- -------------------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_create_listing;
DELIMITER $$
CREATE PROCEDURE sp_create_listing(
    IN p_id BIGINT,
    IN p_name VARCHAR(255),
    IN p_host_id BIGINT,
    IN p_host_name VARCHAR(100),
    IN p_neighbourhood_group VARCHAR(50),
    IN p_neighbourhood VARCHAR(100),
    IN p_room_type VARCHAR(50),
    IN p_price DECIMAL(10,2),
    IN p_minimum_nights INT,
    IN p_availability_365 INT,
    OUT p_status VARCHAR(100)
)
BEGIN
    DECLARE v_exists INT DEFAULT 0;

    -- exception handler: catch any SQL error and roll back safely
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SET p_status = 'ERROR: insert failed, transaction rolled back';
    END;

    -- basic validation before touching the table
    IF p_id IS NULL THEN
        SET p_status = 'ERROR: id cannot be NULL';
    ELSEIF p_price IS NOT NULL AND p_price < 0 THEN
        SET p_status = 'ERROR: price cannot be negative';
    ELSE
        SELECT COUNT(*) INTO v_exists FROM airbnb_listings WHERE id = p_id;

        IF v_exists > 0 THEN
            SET p_status = CONCAT('ERROR: listing id ', p_id, ' already exists');
        ELSE
            START TRANSACTION;

            INSERT INTO airbnb_listings (
                id, name, host_id, host_name, neighbourhood_group,
                neighbourhood, room_type, price, minimum_nights, availability_365
            ) VALUES (
                p_id, p_name, p_host_id, p_host_name, p_neighbourhood_group,
                p_neighbourhood, p_room_type, p_price, p_minimum_nights, p_availability_365
            );

            COMMIT;
            SET p_status = CONCAT('SUCCESS: listing ', p_id, ' created');
        END IF;
    END IF;
END$$
DELIMITER ;

-- -------------------------------------------------------------------------
-- 4b. RETRIEVE - by primary key
-- -------------------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_retrieve_by_id;
DELIMITER $$
CREATE PROCEDURE sp_retrieve_by_id(IN p_id BIGINT)
BEGIN
    SELECT * FROM airbnb_listings WHERE id = p_id;
END$$
DELIMITER ;

-- -------------------------------------------------------------------------
-- 4b. RETRIEVE - by flexible criteria (column value or range)
-- NULL parameters are ignored, so users can filter by any subset of them
-- -------------------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_retrieve_by_criteria;
DELIMITER $$
CREATE PROCEDURE sp_retrieve_by_criteria(
    IN p_neighbourhood_group VARCHAR(50),
    IN p_room_type VARCHAR(50),
    IN p_min_price DECIMAL(10,2),
    IN p_max_price DECIMAL(10,2)
)
BEGIN
    SELECT id, name, neighbourhood_group, neighbourhood, room_type,
           price, minimum_nights, availability_365
    FROM airbnb_listings
    WHERE (p_neighbourhood_group IS NULL OR neighbourhood_group = p_neighbourhood_group)
      AND (p_room_type IS NULL OR room_type = p_room_type)
      AND (p_min_price IS NULL OR price >= p_min_price)
      AND (p_max_price IS NULL OR price <= p_max_price)
    ORDER BY price ASC;
END$$
DELIMITER ;

-- -------------------------------------------------------------------------
-- 4c. UPDATE - update a listing's editable fields by primary key
-- NULL parameters mean "leave this column unchanged"
-- -------------------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_update_listing;
DELIMITER $$
CREATE PROCEDURE sp_update_listing(
    IN p_id BIGINT,
    IN p_price DECIMAL(10,2),
    IN p_minimum_nights INT,
    IN p_availability_365 INT,
    OUT p_status VARCHAR(100)
)
BEGIN
    DECLARE v_exists INT DEFAULT 0;

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SET p_status = 'ERROR: update failed, transaction rolled back';
    END;

    SELECT COUNT(*) INTO v_exists FROM airbnb_listings WHERE id = p_id;

    IF v_exists = 0 THEN
        SET p_status = CONCAT('ERROR: listing id ', p_id, ' not found');
    ELSEIF p_price IS NOT NULL AND p_price < 0 THEN
        SET p_status = 'ERROR: price cannot be negative';
    ELSE
        START TRANSACTION;

        UPDATE airbnb_listings
        SET price             = COALESCE(p_price, price),
            minimum_nights    = COALESCE(p_minimum_nights, minimum_nights),
            availability_365  = COALESCE(p_availability_365, availability_365)
        WHERE id = p_id;

        COMMIT;
        SET p_status = CONCAT('SUCCESS: listing ', p_id, ' updated');
    END IF;
END$$
DELIMITER ;

-- -------------------------------------------------------------------------
-- 4d. DELETE - remove a listing by primary key
-- -------------------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_delete_listing;
DELIMITER $$
CREATE PROCEDURE sp_delete_listing(
    IN p_id BIGINT,
    OUT p_status VARCHAR(100)
)
BEGIN
    DECLARE v_exists INT DEFAULT 0;

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SET p_status = 'ERROR: delete failed, transaction rolled back';
    END;

    SELECT COUNT(*) INTO v_exists FROM airbnb_listings WHERE id = p_id;

    IF v_exists = 0 THEN
        SET p_status = CONCAT('ERROR: listing id ', p_id, ' not found');
    ELSE
        START TRANSACTION;
        DELETE FROM airbnb_listings WHERE id = p_id;
        COMMIT;
        SET p_status = CONCAT('SUCCESS: listing ', p_id, ' deleted');
    END IF;
END$$
DELIMITER ;


-- =========================================================================
-- 5. TRANSACTION MANAGEMENT
-- =========================================================================
-- Demonstrates START TRANSACTION, SAVEPOINT, ROLLBACK TO SAVEPOINT, and
-- COMMIT together, using a batch price-update as the working example.
-- If any single row in the batch fails validation, only that row's change
-- is undone (via SAVEPOINT); the rest of the batch still commits.
-- -------------------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_batch_price_update;
DELIMITER $$
CREATE PROCEDURE sp_batch_price_update(
    IN p_id1 BIGINT, IN p_price1 DECIMAL(10,2),
    IN p_id2 BIGINT, IN p_price2 DECIMAL(10,2),
    OUT p_status VARCHAR(255)
)
proc_body: BEGIN
    DECLARE v_error_count INT DEFAULT 0;

    -- if something unexpected happens, abandon the whole batch
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SET p_status = 'ERROR: unexpected failure, entire batch rolled back';
    END;

    START TRANSACTION;

    -- ---- row 1 ----
    SAVEPOINT sp_row1;
    IF p_price1 < 0 OR NOT EXISTS (SELECT 1 FROM airbnb_listings WHERE id = p_id1) THEN
        ROLLBACK TO SAVEPOINT sp_row1;
        SET v_error_count = v_error_count + 1;
    ELSE
        UPDATE airbnb_listings SET price = p_price1 WHERE id = p_id1;
    END IF;

    -- ---- row 2 ----
    SAVEPOINT sp_row2;
    IF p_price2 < 0 OR NOT EXISTS (SELECT 1 FROM airbnb_listings WHERE id = p_id2) THEN
        ROLLBACK TO SAVEPOINT sp_row2;
        SET v_error_count = v_error_count + 1;
    ELSE
        UPDATE airbnb_listings SET price = p_price2 WHERE id = p_id2;
    END IF;

    COMMIT;

    IF v_error_count = 0 THEN
        SET p_status = 'SUCCESS: both rows updated';
    ELSE
        SET p_status = CONCAT('PARTIAL SUCCESS: ', v_error_count, ' row(s) skipped and rolled back to savepoint, rest committed');
    END IF;
END$$
DELIMITER ;

-- -------------------------------------------------------------------------
-- 5b. Transactional wrapper for delete with explicit rollback path
-- Shows a case where the whole transaction is deliberately rolled back
-- (e.g. deleting a host's listings only if ALL of them can be removed)
-- -------------------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_delete_host_listings_safe;
DELIMITER $$
CREATE PROCEDURE sp_delete_host_listings_safe(
    IN p_host_id BIGINT,
    OUT p_status VARCHAR(255)
)
BEGIN
    DECLARE v_count INT DEFAULT 0;

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SET p_status = 'ERROR: exception occurred, all deletions rolled back';
    END;

    SELECT COUNT(*) INTO v_count FROM airbnb_listings WHERE host_id = p_host_id;

    IF v_count = 0 THEN
        SET p_status = CONCAT('ERROR: no listings found for host_id ', p_host_id);
    ELSE
        START TRANSACTION;
        SAVEPOINT before_delete;

        DELETE FROM airbnb_listings WHERE host_id = p_host_id;

        -- integrity check: confirm nothing is left behind before committing
        IF (SELECT COUNT(*) FROM airbnb_listings WHERE host_id = p_host_id) > 0 THEN
            ROLLBACK TO SAVEPOINT before_delete;
            SET p_status = 'ERROR: deletion incomplete, rolled back to savepoint';
        ELSE
            COMMIT;
            SET p_status = CONCAT('SUCCESS: ', v_count, ' listing(s) deleted for host_id ', p_host_id);
        END IF;
    END IF;
END$$
DELIMITER ;