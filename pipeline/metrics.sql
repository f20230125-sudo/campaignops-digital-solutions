-- Period membership uses the event timestamp in Asia/Dubai.
-- Distinct counts are recalculated for each grouping, never summed from daily uniques.
WITH scoped AS (
 SELECT e.*, p.id AS period FROM events e CROSS JOIN periods p
 WHERE CAST(timezone('Asia/Dubai', e.occurred_at) AS DATE) BETWEEN p.start_date AND p.end_date
), messages AS (
 SELECT period, campaign, market, entity_id,
   bool_or(kind='delivered') delivered,
   bool_or(kind='click' AND flag='human') clicked
 FROM scoped WHERE kind IN ('delivered','click') GROUP BY ALL
), email AS (
 SELECT period, coalesce(campaign,'all') campaign, coalesce(market,'all') market,
 count(*) FILTER (WHERE delivered) delivered,
 count(*) FILTER (WHERE delivered AND clicked) clicked
 FROM messages GROUP BY GROUPING SETS ((period,campaign,market),(period,campaign),(period,market),(period))
), sessions AS (
 SELECT period,campaign,market,entity_id,
 bool_or(kind='session' AND split_part(flag,'|',2)='landing') eligible,
 bool_or(kind='registration') registered,
 bool_or(kind='session' AND (value>10 OR try_cast(split_part(flag,'|',1) AS INTEGER)>=2)) engaged
 FROM scoped WHERE kind IN ('session','registration') GROUP BY ALL
), web AS (
 SELECT period,coalesce(campaign,'all') campaign,coalesce(market,'all') market,
 count(*) FILTER(WHERE eligible) sessions,
 count(*) FILTER(WHERE eligible AND (engaged OR registered)) engaged,
 count(*) FILTER(WHERE eligible AND registered) registered
 FROM sessions GROUP BY GROUPING SETS ((period,campaign,market),(period,campaign),(period,market),(period))
), people AS (
 SELECT period,campaign,market,parent_id,entity_id,
 bool_or(kind='webinar_registration') registered,
 bool_or(kind='attendance' AND flag='attendee' AND value>0) attended
 FROM scoped WHERE kind IN ('webinar_registration','attendance') GROUP BY ALL
), webinars AS (
 SELECT period,coalesce(campaign,'all') campaign,coalesce(market,'all') market,
 count(*) FILTER(WHERE registered) registrants,
 count(*) FILTER(WHERE registered AND attended) attendees,
 count(*) FILTER(WHERE NOT registered AND attended) unmatched_attendees
 FROM people GROUP BY GROUPING SETS ((period,campaign,market),(period,campaign),(period,market),(period))
), keys AS (SELECT period,campaign,market FROM email UNION SELECT period,campaign,market FROM web UNION SELECT period,campaign,market FROM webinars)
SELECT k.*, coalesce(e.delivered,0) delivered,coalesce(e.clicked,0) clicked,
 coalesce(w.sessions,0) sessions,coalesce(w.engaged,0) engaged,coalesce(w.registered,0) registrations,
 coalesce(b.registrants,0) registrants,coalesce(b.attendees,0) attendees,coalesce(b.unmatched_attendees,0) unmatched_attendees
FROM keys k LEFT JOIN email e USING(period,campaign,market) LEFT JOIN web w USING(period,campaign,market) LEFT JOIN webinars b USING(period,campaign,market)
ORDER BY period,campaign,market;
