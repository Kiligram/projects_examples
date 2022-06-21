# Andrii Rybak

This is a REST API app, that returns data in json format according to the link that was used. There were used such technologies as SQLAlchemy (ORM for PostgreSQL), flask (to make the API).

# PostgreSQL queries used in the app. All these queries are also represent in the app as ORM.

## 1.

    SELECT * FROM
    (SELECT *, row_number() OVER (PARTITION BY localized_name ORDER BY hero_id ASC, count DESC, item_name ASC) as row_num
      FROM
        (SELECT m.id as match_id,
        m_p_d.hero_id,
        her.localized_name,
        p_log.item_id,
        itms.name as item_name,
        count(*)
        FROM purchase_logs as p_log
        JOIN matches_players_details as m_p_d ON p_log.match_player_detail_id = m_p_d.id
        JOIN heroes as her ON m_p_d.hero_id = her.id
        JOIN matches as m ON m_p_d.match_id = m.id
        JOIN items as itms ON p_log.item_id = itms.id
        WHERE ((m_p_d.player_slot >= 0 AND m_p_d.player_slot <= 4 AND m.radiant_win is true) OR 
        (m_p_d.player_slot >= 128 AND m_p_d.player_slot <= 132 AND m.radiant_win is false)) AND m.id = 21421
        GROUP BY m.id, m_p_d.hero_id, her.localized_name, p_log.item_id, itms.name) table1
      ORDER BY hero_id ASC, count DESC, item_name ASC) table2
    WHERE row_num <= 5

## 2.
    SELECT DISTINCT ON (hero_id, winner)
    ability_id,
    name,
    hero_id,
    hero_name,
    winner,
    CONCAT(substr(percent_time, 1, length(percent_time) - 1), '0-', substr(percent_time, 1, length(percent_time) - 1), '9') as rozsah,
    count(*)
    FROM
    (SELECT ab_up.ability_id,
    ab.name,
    her.id as hero_id,
    her.localized_name as hero_name,
    CASE WHEN m_p_d.player_slot >= 0 AND m_p_d.player_slot <= 4 AND m.radiant_win is true THEN true
       WHEN m_p_d.player_slot >= 128 AND m_p_d.player_slot <= 132 AND m.radiant_win is false THEN true
    ELSE false
    END as winner,
    CAST((ab_up.time * 100 / m.duration) AS VARCHAR) as percent_time
    FROM ability_upgrades as ab_up
    JOIN abilities as ab ON ab.id = ab_up.ability_id
    JOIN matches_players_details as m_p_d ON ab_up.match_player_detail_id = m_p_d.id
    JOIN heroes as her ON her.id = m_p_d.hero_id
    JOIN matches as m ON m.id = m_p_d.match_id
    WHERE ab_up.ability_id = 5004) as table1
    GROUP BY ability_id, name, hero_id, hero_name, winner, rozsah
    ORDER BY hero_id ASC, winner DESC, count DESC

## 3.
    SELECT hero_id,
    heroes.localized_name,
    max
    FROM
    (SELECT hero_id,
    max(count)
    FROM (SELECT
    match_id,
    hero_id,
    count(*)
    from(
    SELECT
    row_number() OVER (ORDER BY m_p_d.match_id ASC, g_ob.time ASC) - row_number() over (partition by m_p_d.match_id, m_p_d.hero_id ORDER BY m_p_d.match_id ASC, g_ob.time ASC) as row_num,
    m_p_d.match_id,
    m_p_d.hero_id,
    g_ob.time
    FROM game_objectives as g_ob
    JOIN matches_players_details as m_p_d ON g_ob.match_player_detail_id_1 = m_p_d.id
    WHERE g_ob.subtype = 'CHAT_MESSAGE_TOWER_KILL' AND match_player_detail_id_1 IS not NULL
    ORDER BY m_p_d.match_id ASC, g_ob.time ASC 
    ) table1
    GROUP BY row_num, match_id, hero_id) table2
    GROUP BY hero_id) table3
    JOIN heroes ON hero_id = heroes.id
    ORDER BY max DESC, localized_name ASC

# zad 3 SQL query

## 1. 
    WITH table1 AS(
      SELECT name as patch_version, cast(extract(epoch from release_date) as integer) as patch_start_date FROM patches
      ORDER BY patch_version ASC
    ),
    table2 AS(
    SELECT
      patch_version, 
      patch_start_date,
      LEAD(patch_start_date,1) OVER (ORDER BY patch_version) patch_end_date
    FROM
      table1
    )
    SELECT patch_version, patch_start_date, patch_end_date, mts.id as match_id, ROUND(mts.duration/60.00, 2) as match_duration FROM table2
    LEFT JOIN matches as mts ON mts.start_time >= patch_start_date AND mts.start_time < patch_end_date

## 2.
    SELECT pl.id, 
    CASE WHEN pl.nick IS null THEN 'unknown'
    ELSE pl.nick
    END as player_nick,
    hr.localized_name as hero_localized_name,
    ROUND(mt.duration/60.00, 2) as match_duration_minutes,
    COALESCE(mt_pl_dt.xp_hero, 0) + COALESCE(mt_pl_dt.xp_creep, 0) + COALESCE(mt_pl_dt.xp_other, 0) + COALESCE(mt_pl_dt.xp_roshan, 0) AS experiences_gained,
    mt_pl_dt.level as level_gained,

    CASE WHEN player_slot >= 0 AND player_slot <= 4 AND radiant_win is true THEN true
       WHEN player_slot >= 128 AND player_slot <= 132 AND radiant_win is false THEN true
    ELSE false
    END as winner,

    mt.id as match_id
    FROM players as pl
    JOIN matches_players_details as mt_pl_dt ON mt_pl_dt.player_id = pl.id 
    JOIN heroes as hr ON mt_pl_dt.hero_id = hr.id
    JOIN matches as mt ON mt_pl_dt.match_id = mt.id
    WHERE pl.id = 14944
    ORDER BY match_id ASC

## 3.
    SELECT pl.id, 
    CASE WHEN pl.nick IS null THEN 'unknown'
    ELSE pl.nick
    END as player_nick,
    hr.localized_name as hero_localized_name,
    mt.id as match_id,
    COALESCE(gm_obj.subtype, 'NO_ACTION') as hero_action,
    count(*)

    FROM players as pl
    JOIN matches_players_details as mt_pl_dt ON mt_pl_dt.player_id = pl.id 
    JOIN heroes as hr ON mt_pl_dt.hero_id = hr.id
    JOIN matches as mt ON mt_pl_dt.match_id = mt.id
    LEFT JOIN game_objectives as gm_obj ON mt_pl_dt.id = gm_obj.match_player_detail_id_1
    WHERE pl.id = 14944
    GROUP BY pl.id, hr.localized_name, mt.id, gm_obj.subtype
    ORDER BY match_id ASC

## 4.
    WITH table1 AS( 
      SELECT pl.id, 
      CASE WHEN pl.nick IS null THEN 'unknown'
      ELSE pl.nick
      END as player_nick,
      hr.localized_name as hero_localized_name,
      mt.id as match_id,
      ab.name as ability_name,
      max(ab_upg.level) OVER (PARTITION BY mt.id, ab.name) as upgrade_level
      FROM players as pl
      JOIN matches_players_details as mt_pl_dt ON mt_pl_dt.player_id = pl.id 
      JOIN heroes as hr ON mt_pl_dt.hero_id = hr.id
      JOIN matches as mt ON mt_pl_dt.match_id = mt.id
      JOIN ability_upgrades as ab_upg ON mt_pl_dt.id = ab_upg.match_player_detail_id
      JOIN abilities as ab ON ab_upg.ability_id = ab.id
      WHERE pl.id = 14944
      GROUP BY pl.id, hr.localized_name, mt.id, ab.name, ab_upg.level
      ORDER BY match_id ASC
    )

    SELECT id, player_nick, hero_localized_name, match_id, ability_name, upgrade_level,
    count(*)
    FROM table1
    GROUP BY id, player_nick, hero_localized_name, match_id, ability_name, upgrade_level
    ORDER BY match_id ASC
