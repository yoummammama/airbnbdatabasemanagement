-- =========================================================================
-- UECS3203 Advanced Database Systems - Assignment 1
-- Section 3: Data Analysis
-- 6 analysis queries + 1 procedure + 2 functions
-- Run the whole file in MySQL Workbench (it handles DELIMITER blocks).
-- =========================================================================

USE airbnb_db;

-- -------------------------------------------------------------------------
-- Query 1: Top 10 most expensive listings (premium listing identification)
-- ORDER BY price DESC sorts the table so the most expensive listings come
-- first, and LIMIT 10 keeps only the top 10. This combination is the most
-- efficient and natural way to identify "premium" listings: it requires no
-- arbitrary cut-off value, works with an index on price, and returns a
-- focused, readable shortlist instead of the full table.
-- -------------------------------------------------------------------------
SELECT id, name, neighbourhood, room_type, price 

FROM airbnb_listings 

ORDER BY price DESC 

LIMIT 10; 

-- -------------------------------------------------------------------------
-- Query 2: Top 10 most-reviewed listings
-- number_of_reviews is a count of how many guests actually left a review,
-- so it reflects listing popularity/booking volume only indirectly. It does
-- NOT measure guest satisfaction: a listing can be heavily reviewed because
-- it is cheap, central, or newsworthy, while guests are actually unhappy.
-- Satisfaction is better judged from review_rate_number (the star rating),
-- which is why both columns are selected here side by side.
-- -------------------------------------------------------------------------
SELECT id, name, neighbourhood, number_of_reviews, review_rate_number 

FROM airbnb_listings 

ORDER BY number_of_reviews DESC 

LIMIT 10; 

-- -------------------------------------------------------------------------
-- Query 3: Value-for-money listings
-- The thresholds (price < $150, number_of_reviews > 50, review_rate_number
-- > 4.7) were deliberately chosen to represent "value-for-money" listings:
-- a price ceiling keeps the listing affordable, a minimum review count
-- filters out brand-new/untested listings, and a high star rating ensures
-- prior guests were satisfied. Sorting by rating then price surfaces the
-- best-rated affordable options first.
-- -------------------------------------------------------------------------
SELECT  

    name, 

    neighbourhood_group, 

    room_type, 

    price, 

    number_of_reviews, 

    review_rate_number 

FROM airbnb_listings 

WHERE price < 150  

  AND number_of_reviews > 50  

  AND review_rate_number > 4.7 

ORDER BY review_rate_number DESC, price ASC 

LIMIT 15; 

-- -------------------------------------------------------------------------
-- Query 4: Borough-level market summary
-- COUNT, AVG, MIN, MAX (and AVG again for availability) collapse every
-- listing in a borough into one row, giving a compact market summary per
-- neighbourhood group: how many listings exist, the typical price, the
-- cheapest and most expensive offers, and average availability. Aggregates
-- are the right tool here because the goal is a comparative overview of
-- boroughs, not an inspection of individual rows.
-- -------------------------------------------------------------------------
SELECT  

    neighbourhood_group AS borough, 

    COUNT(*) AS total_listings, 

    ROUND(AVG(price), 2) AS avg_price, 

    ROUND(MIN(price), 2) AS min_price, 

    ROUND(MAX(price), 2) AS max_price, 

    ROUND(AVG(availability_365), 0) AS avg_availability_days 

FROM airbnb_listings 

WHERE price > 0 AND price < 10000  

GROUP BY neighbourhood_group 

ORDER BY avg_price DESC; 

-- -------------------------------------------------------------------------
-- Query 5: Demand segments by availability
-- The CASE expression buckets listings into demand categories based on
-- availability_365 (how many days per year are free). This grouping is used
-- for segment COMPARISON (how price/reviews differ across segments) and
-- must NOT be read as proof of causation: availability is a consequence of
-- demand, pricing, and host behaviour combined, and a cross-tab of segments
-- only shows association, not cause and effect.
-- -------------------------------------------------------------------------
SELECT  
    CASE  
        WHEN availability_365 = 0 THEN 'Fully Booked' 
        WHEN availability_365 BETWEEN 1 AND 90 THEN 'Very High Demand' 
        WHEN availability_365 BETWEEN 91 AND 200 THEN 'High Demand' 
        WHEN availability_365 BETWEEN 201 AND 300 THEN 'Moderate Demand' 
        ELSE 'Low Demand' 
    END AS demand_category, 
    COUNT(*) AS listings, 
    ROUND(AVG(price), 2) AS avg_price, 
    ROUND(AVG(number_of_reviews), 0) AS avg_reviews, 
    ROUND(MIN(price), 2) AS min_price, 
    ROUND(MAX(price), 2) AS max_price 
FROM airbnb_listings 
WHERE price > 0 
GROUP BY demand_category 
ORDER BY avg_price DESC; 

-- -------------------------------------------------------------------------
-- Query 6: Monthly review activity
-- Grouping by month (last_review) aggregates reviews and prices by calendar
-- month, which helps detect two things: (a) seasonality - months with many
-- reviews or higher prices reveal busy/demand seasons; and (b) data-entry
-- issues - impossible dates, stray formats, or months with implausible
-- counts surface when STR_TO_DATE fails or a month looks abnormal, and the
-- guards on last_review filter out exactly those bad rows.
-- -------------------------------------------------------------------------
SELECT  
    DATE_FORMAT(STR_TO_DATE(last_review, '%m/%d/%Y'), '%Y-%m') AS review_month, 
    COUNT(*) AS listings_reviewed, 
    ROUND(AVG(price), 2) AS avg_price, 
    ROUND(AVG(review_rate_number), 1) AS avg_rating 
FROM airbnb_listings 
WHERE last_review IS NOT NULL  
  AND last_review != '' 
  AND STR_TO_DATE(last_review, '%m/%d/%Y') IS NOT NULL 
  AND STR_TO_DATE(last_review, '%m/%d/%Y') <= "2022-4-30" 
GROUP BY review_month 
ORDER BY review_month DESC 
LIMIT 12; 

-- -------------------------------------------------------------------------
-- Query 7: Monthly review activity with low counts
-- Find months with very low review activity (potential data errors)
SELECT 
    DATE_FORMAT(STR_TO_DATE(last_review, '%m/%d/%Y'), '%Y-%m') AS review_month,
    COUNT(*) AS listings_reviewed,
    ROUND(AVG(price), 2) AS avg_price,
    ROUND(AVG(review_rate_number), 2) AS avg_rating
FROM airbnb_listings
WHERE last_review IS NOT NULL 
  AND last_review != ''
  AND STR_TO_DATE(last_review, '%m/%d/%Y') IS NOT NULL
GROUP BY review_month
HAVING COUNT(*) <= 5   -- Unrealistically low activity
ORDER BY review_month DESC;
-- -------------------------------------------------------------------------

DROP PROCEDURE IF EXISTS sp_borough_market_report; 
 
DELIMITER $$ 
 
CREATE PROCEDURE sp_borough_market_report( 
    IN p_borough VARCHAR(50), 
    OUT p_summary VARCHAR(500) 
) 
BEGIN 
    DECLARE v_total INT; 
    DECLARE v_avg_price DECIMAL(10,2); 
    DECLARE v_avg_rating DECIMAL(3,2); 
    DECLARE v_avg_availability INT; 
     
    -- Exception handler for unexpected errors 
    DECLARE EXIT HANDLER FOR SQLEXCEPTION 
    BEGIN 
        SET p_summary = 'ERROR: An unexpected error occurred while generating the report.'; 
    END; 
     
    -- Calculate borough statistics 
    SELECT  
        COUNT(*), 
        ROUND(AVG(price), 2), 
        ROUND(AVG(review_rate_number), 2), 
        ROUND(AVG(availability_365), 0) 
    INTO  
        v_total, 
        v_avg_price, 
        v_avg_rating, 
        v_avg_availability 
    FROM airbnb_listings 
    WHERE neighbourhood_group = p_borough  
      AND price > 0  
      AND price < 10000; 
     
    -- Check if borough exists 
    IF v_total = 0 THEN 
        SET p_summary = CONCAT('ERROR: No listings found for borough: ', p_borough); 
    ELSE 
        -- Build summary message 
        SET p_summary = CONCAT( 
            'Market Report for ', p_borough, '\n', 
            '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n', 
            'Total Listings: ', v_total, '\n', 
            'Average Price: $', v_avg_price, '\n', 
            'Average Rating: ', v_avg_rating, '/5.0\n', 
            'Avg Availability: ', v_avg_availability, ' days\n', 
            '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━' 
        ); 
    END IF; 
     
    -- Return detailed breakdown by room type 
    SELECT  
        room_type, 
        COUNT(*) AS count, 
        ROUND(AVG(price), 2) AS avg_price, 
        ROUND(AVG(review_rate_number), 2) AS avg_rating, 
        ROUND(AVG(availability_365), 0) AS avg_availability 
    FROM airbnb_listings 
    WHERE neighbourhood_group = p_borough  
      AND price > 0  
      AND price < 10000 
    GROUP BY room_type 
    ORDER BY avg_price DESC; 
     
END$$ 
 
DELIMITER ; 

DROP FUNCTION IF EXISTS fn_price_tier; 
 
DELIMITER $$ 
 
CREATE FUNCTION fn_price_tier(p_price DECIMAL(10,2)) 
RETURNS VARCHAR(20) 
DETERMINISTIC 
BEGIN 
    -- Validate input 
    IF p_price IS NULL OR p_price <= 0 THEN 
        RETURN 'Invalid'; 
    ELSEIF p_price < 100 THEN 
        RETURN 'Budget'; 
    ELSEIF p_price < 200 THEN 
        RETURN 'Standard'; 
    ELSEIF p_price < 400 THEN 
        RETURN 'Premium'; 
    ELSE 
        RETURN 'Luxury'; 
    END IF; 
END$$ 
 
DELIMITER ; 

DROP FUNCTION IF EXISTS fn_estimated_revenue; 
 
DELIMITER $$ 
 
CREATE FUNCTION fn_estimated_revenue( 
    p_price DECIMAL(10,2), 
    p_availability INT 
) 
RETURNS DECIMAL(12,2) 
DETERMINISTIC 
BEGIN 
    -- Validate inputs 
    IF p_price IS NULL OR p_price <= 0 THEN 
        RETURN 0.00; 
    END IF; 
     
    IF p_availability IS NULL OR p_availability < 0 THEN 
        SET p_availability = 0; 
    END IF; 
     
    -- Estimate annual revenue assuming 60% occupancy rate
    -- Formula: nightly_price * booked_days
    -- booked_days = (365 - availability) * 0.6
    RETURN p_price * (365 - p_availability) * 0.6;
END$$ 

DELIMITER ;

-- =========================================================================
-- USAGE EXAMPLES (run these after the objects are created)
-- =========================================================================

-- Example 1: call the borough market report (OUT summary is captured in @s)
CALL sp_borough_market_report('Manhattan', @s);
SELECT @s AS summary;

-- Example 2: price tier function on real rows
SELECT id, name, price,
       fn_price_tier(price) AS price_tier
FROM airbnb_listings
WHERE price > 0
ORDER BY price DESC
LIMIT 10;

-- Example 3: estimated annual revenue for top listings
SELECT id, name, price, availability_365,
       fn_estimated_revenue(price, availability_365) AS est_annual_revenue
FROM airbnb_listings
WHERE price > 0
ORDER BY price DESC
LIMIT 10;