from flask import Flask, jsonify
import psycopg2
import os
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import label

from models import *
from sqlalchemy import *
from sqlalchemy import create_engine

DBNAME = os.getenv('DBNAME')
LOG_DBS = os.getenv('LOG_DBS')
PASWD_DBS = os.getenv('PASWD_DBS')
DBPORT = os.getenv('DBPORT')
DBHOST = os.getenv('DBHOST')

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://" + LOG_DBS + ":" + PASWD_DBS + "@" + DBHOST + ":" + DBPORT + "/" + DBNAME


@app.route('/v1/health', methods=['GET'])
def get_health():

    db = psycopg2.connect(dbname=os.getenv('DBNAME'), user=os.getenv('LOG_DBS'),
                          password=os.getenv('PASWD_DBS'), host=os.getenv('DBHOST'), port=os.getenv('DBPORT'))

    cursor = db.cursor()

    cursor.execute('SELECT VERSION();')
    version = cursor.fetchall()

    cursor.execute('SELECT pg_database_size(\'dota2\')/1024/1024 as dota2_db_size;')
    db_size = cursor.fetchall()

    x = {
        "version": version[0][0],
        "dota2_db_size": db_size[0][0]
    }

    cursor.close()
    db.close()

    return jsonify(pgsql=x)


def is_patch_in_list(given_list, patch_version):
    if not given_list:
        return None

    index = 0
    while index < len(given_list):
        if given_list[index]['patch_version'] == patch_version:
            return index
        index += 1

    return None


def str_to_float(string):
    if string is None:
        return None
    else:
        return float(string)


@app.route('/v2/patches/', methods=['GET'])
def get_patches():

    db = psycopg2.connect(dbname=os.getenv('DBNAME'), user=os.getenv('LOG_DBS'),
                          password=os.getenv('PASWD_DBS'), host=os.getenv('DBHOST'), port=os.getenv('DBPORT'))

    cursor = db.cursor()

    cursor.execute('WITH table1 AS( SELECT name as patch_version, cast(extract(epoch from release_date) as integer) as patch_start_date FROM patches ORDER BY patch_version ASC ), table2 AS( SELECT patch_version, patch_start_date, LEAD(patch_start_date,1) OVER (ORDER BY patch_version) patch_end_date FROM table1 ) SELECT patch_version, patch_start_date, patch_end_date, mts.id as match_id, ROUND(mts.duration/60.00, 2) as match_duration FROM table2 LEFT JOIN matches as mts ON mts.start_time >= patch_start_date AND mts.start_time < patch_end_date;')
    result = cursor.fetchall()

    result = jsonify(result).get_json()

    cursor.close()
    db.close()

    # print(result)
    patches = []
    for match in result:
        return_value = is_patch_in_list(patches, match[0])
        if return_value is None:
            if match[3] is None:
                patches.append({"patch_version": match[0], "patch_start_date": match[1], "patch_end_date": match[2],
                                "matches": []})
            else:
                patches.append({"patch_version": match[0], "patch_start_date": match[1], "patch_end_date": match[2], "matches": [{"match_id": match[3], "duration": str_to_float(match[4])}]})
        else:
            patches[return_value]["matches"].append({"match_id": match[3], "duration": str_to_float(match[4])})

    # print(patches)

    return jsonify(patches=patches)


@app.route('/v2/players/<player_id>/game_exp/', methods=['GET'])
def get_game_exp(player_id):

    db = psycopg2.connect(dbname=os.getenv('DBNAME'), user=os.getenv('LOG_DBS'),
                          password=os.getenv('PASWD_DBS'), host=os.getenv('DBHOST'), port=os.getenv('DBPORT'))

    cursor = db.cursor()

    cursor.execute('SELECT pl.id, CASE WHEN pl.nick IS null THEN \'unknown\' ELSE pl.nick END as player_nick, hr.localized_name as hero_localized_name, ROUND(mt.duration/60.00, 2) as match_duration_minutes, COALESCE(mt_pl_dt.xp_hero, 0) + COALESCE(mt_pl_dt.xp_creep, 0) + COALESCE(mt_pl_dt.xp_other, 0) + COALESCE(mt_pl_dt.xp_roshan, 0) AS experiences_gained, mt_pl_dt.level as level_gained, CASE WHEN player_slot >= 0 AND player_slot <= 4 AND radiant_win is true THEN true WHEN player_slot >= 128 AND player_slot <= 132 AND radiant_win is false THEN true ELSE false END as winner, mt.id as match_id FROM players as pl JOIN matches_players_details as mt_pl_dt ON mt_pl_dt.player_id = pl.id JOIN heroes as hr ON mt_pl_dt.hero_id = hr.id JOIN matches as mt ON mt_pl_dt.match_id = mt.id WHERE pl.id = ' + str(player_id) + ' ORDER BY match_id ASC')
    result = cursor.fetchall()

    cursor.close()
    db.close()

    result = jsonify(result).get_json()

    if not result:
        return jsonify({})

    game_exp = {
        "id": result[0][0],
        "player_nick": result[0][1],
        "matches": []
    }

    for match in result:
        game_exp["matches"].append({"match_id": match[7], "hero_localized_name": match[2], "match_duration_minutes": str_to_float(match[3]), "experiences_gained": match[4], "level_gained": match[5], "winner": match[6]})

    return jsonify(game_exp)


def is_match_in_list(given_list, match_id):
    if not given_list:
        return None

    index = 0
    while index < len(given_list):
        if given_list[index]['match_id'] == match_id:
            return index
        index += 1

    return None


@app.route('/v2/players/<player_id>/game_objectives/', methods=['GET'])
def get_game_objectives(player_id):

    db = psycopg2.connect(dbname=os.getenv('DBNAME'), user=os.getenv('LOG_DBS'),
                          password=os.getenv('PASWD_DBS'), host=os.getenv('DBHOST'), port=os.getenv('DBPORT'))

    cursor = db.cursor()

    cursor.execute('SELECT pl.id, CASE WHEN pl.nick IS null THEN \'unknown\' ELSE pl.nick END as player_nick, hr.localized_name as hero_localized_name, mt.id as match_id, COALESCE(gm_obj.subtype, \'NO_ACTION\') as hero_action, count(*) FROM players as pl JOIN matches_players_details as mt_pl_dt ON mt_pl_dt.player_id = pl.id JOIN heroes as hr ON mt_pl_dt.hero_id = hr.id JOIN matches as mt ON mt_pl_dt.match_id = mt.id LEFT JOIN game_objectives as gm_obj ON mt_pl_dt.id = gm_obj.match_player_detail_id_1 WHERE pl.id = ' + str(player_id) + ' GROUP BY pl.id, hr.localized_name, mt.id, gm_obj.subtype ORDER BY match_id ASC')
    result = cursor.fetchall()

    cursor.close()
    db.close()

    result = jsonify(result).get_json()
    # print(result)

    if not result:
        return jsonify({})

    game_objectives = {
        "id": result[0][0],
        "player_nick": result[0][1],
        "matches": []
    }

    for match in result:
        return_value = is_match_in_list(game_objectives["matches"], match[3])
        if return_value is None:
            game_objectives["matches"].append({"match_id": match[3], "hero_localized_name": match[2], "actions": [{"hero_action": match[4], "count": match[5]}]})
        else:
            game_objectives["matches"][return_value]["actions"].append({"hero_action": match[4], "count": match[5]})

    return jsonify(game_objectives)


@app.route('/v2/players/<player_id>/abilities/', methods=['GET'])
def get_abilities(player_id):

    db = psycopg2.connect(dbname=os.getenv('DBNAME'), user=os.getenv('LOG_DBS'),
                          password=os.getenv('PASWD_DBS'), host=os.getenv('DBHOST'), port=os.getenv('DBPORT'))

    cursor = db.cursor()

    cursor.execute('WITH table1 AS( SELECT pl.id, CASE WHEN pl.nick IS null THEN \'unknown\' ELSE pl.nick END as player_nick, hr.localized_name as hero_localized_name, mt.id as match_id, ab.name as ability_name, max(ab_upg.level) OVER (PARTITION BY mt.id, ab.name) as upgrade_level FROM players as pl JOIN matches_players_details as mt_pl_dt ON mt_pl_dt.player_id = pl.id JOIN heroes as hr ON mt_pl_dt.hero_id = hr.id JOIN matches as mt ON mt_pl_dt.match_id = mt.id JOIN ability_upgrades as ab_upg ON mt_pl_dt.id = ab_upg.match_player_detail_id JOIN abilities as ab ON ab_upg.ability_id = ab.id WHERE pl.id = ' + str(player_id) + 'GROUP BY pl.id, hr.localized_name, mt.id, ab.name, ab_upg.level ORDER BY match_id ASC ) SELECT id, player_nick, hero_localized_name, match_id, ability_name, upgrade_level, count(*) FROM table1 GROUP BY id, player_nick, hero_localized_name, match_id, ability_name, upgrade_level ORDER BY match_id ASC')
    result = cursor.fetchall()

    cursor.close()
    db.close()

    result = jsonify(result).get_json()
    # print(result)

    if not result:
        return jsonify({})

    abilities = {
        "id": result[0][0],
        "player_nick": result[0][1],
        "matches": []
    }

    for match in result:
        return_value = is_match_in_list(abilities["matches"], match[3])
        if return_value is None:
            abilities["matches"].append({"match_id": match[3], "hero_localized_name": match[2], "abilities": [{"ability_name": match[4], "count": match[6], "upgrade_level": match[5]}]})
        else:
            abilities["matches"][return_value]["abilities"].append({"ability_name": match[4], "count": match[6], "upgrade_level": match[5]})

    return jsonify(abilities)


def is_hero_in_list(given_list, hero_id):
    if not given_list:
        return None

    index = 0
    while index < len(given_list):
        if given_list[index]['id'] == hero_id:
            return index
        index += 1

    return None


@app.route('/v3/matches/<match_id>/top_purchases/', methods=['GET'])
def get_top_purchases(match_id):

    db = psycopg2.connect(dbname=os.getenv('DBNAME'), user=os.getenv('LOG_DBS'),
                          password=os.getenv('PASWD_DBS'), host=os.getenv('DBHOST'), port=os.getenv('DBPORT'))

    cursor = db.cursor()

    cursor.execute('SELECT match_id, hero_id, localized_name, item_id, item_name, count FROM (SELECT *, row_number() OVER (PARTITION BY localized_name ORDER BY hero_id ASC, count DESC, item_name ASC) as row_num FROM (SELECT m.id as match_id, m_p_d.hero_id, her.localized_name, p_log.item_id, itms.name as item_name, count(*) FROM purchase_logs as p_log JOIN matches_players_details as m_p_d ON p_log.match_player_detail_id = m_p_d.id JOIN heroes as her ON m_p_d.hero_id = her.id JOIN matches as m ON m_p_d.match_id = m.id JOIN items as itms ON p_log.item_id = itms.id WHERE ((m_p_d.player_slot >= 0 AND m_p_d.player_slot <= 4 AND m.radiant_win is true) OR (m_p_d.player_slot >= 128 AND m_p_d.player_slot <= 132 AND m.radiant_win is false)) AND m.id = ' + str(match_id) + ' GROUP BY m.id, m_p_d.hero_id, her.localized_name, p_log.item_id, itms.name) table1 ORDER BY hero_id ASC, count DESC, item_name ASC) table2 WHERE row_num <= 5')
    result = cursor.fetchall()

    cursor.close()
    db.close()

    result = jsonify(result).get_json()
    # print(result)

    if not result:
        return jsonify({})

    top_purchases = {
        "id": int(match_id),
        "heroes": []
    }

    for hero in result:
        return_value = is_hero_in_list(top_purchases["heroes"], hero[1])
        if return_value is None:
            top_purchases["heroes"].append({"id": hero[1], "name": hero[2], "top_purchases": [{"id": hero[3], "name": hero[4], "count": hero[5]}]})
        else:
            top_purchases["heroes"][return_value]["top_purchases"].append({"id": hero[3], "name": hero[4], "count": hero[5]})

    return jsonify(top_purchases)


@app.route('/v3/abilities/<ability_id>/usage/', methods=['GET'])
def get_abilities_usage(ability_id):
    db = psycopg2.connect(dbname=os.getenv('DBNAME'), user=os.getenv('LOG_DBS'),
                          password=os.getenv('PASWD_DBS'), host=os.getenv('DBHOST'), port=os.getenv('DBPORT'))

    cursor = db.cursor()

    cursor.execute('SELECT DISTINCT ON (hero_id, winner) ability_id, name, hero_id, hero_name, winner, CONCAT(substr(percent_time, 1, length(percent_time) - 1), \'0-\', substr(percent_time, 1, length(percent_time) - 1), \'9\') as rozsah, count(*) FROM (SELECT ab_up.ability_id, ab.name, her.id as hero_id, her.localized_name as hero_name, CASE WHEN m_p_d.player_slot >= 0 AND m_p_d.player_slot <= 4 AND m.radiant_win is true THEN true WHEN m_p_d.player_slot >= 128 AND m_p_d.player_slot <= 132 AND m.radiant_win is false THEN true ELSE false END as winner, CAST((ab_up.time * 100 / m.duration) AS VARCHAR) as percent_time FROM ability_upgrades as ab_up JOIN abilities as ab ON ab.id = ab_up.ability_id JOIN matches_players_details as m_p_d ON ab_up.match_player_detail_id = m_p_d.id JOIN heroes as her ON her.id = m_p_d.hero_id JOIN matches as m ON m.id = m_p_d.match_id WHERE ab_up.ability_id = ' + str(ability_id) + ') as table1 GROUP BY ability_id, name, hero_id, hero_name, winner, rozsah ORDER BY hero_id ASC, winner DESC, count DESC')
    result = cursor.fetchall()

    cursor.close()
    db.close()

    result = jsonify(result).get_json()
    # print(result)

    if not result:
        return jsonify({})

    abilities_usage = {
        "id": int(ability_id),
        "name": result[0][1],
        "heroes": []
    }

    for hero in result:
        return_value = is_hero_in_list(abilities_usage["heroes"], hero[2])
        if return_value is None:
            to_append = {"id": hero[2], "name": hero[3]}
            if hero[4]:
                to_append["usage_winners"] = {"bucket": hero[5], "count": hero[6]}
            else:
                to_append["usage_loosers"] = {"bucket": hero[5], "count": hero[6]}
            abilities_usage["heroes"].append(to_append)
        else:
            if hero[4]:
                abilities_usage["heroes"][return_value]["usage_winners"] = {"bucket": hero[5], "count": hero[6]}
            else:
                abilities_usage["heroes"][return_value]["usage_loosers"] = {"bucket": hero[5], "count": hero[6]}

    return jsonify(abilities_usage)


@app.route('/v3/statistics/tower_kills/', methods=['GET'])
def get_tower_kills_statistics():
    db = psycopg2.connect(dbname=os.getenv('DBNAME'), user=os.getenv('LOG_DBS'),
                          password=os.getenv('PASWD_DBS'), host=os.getenv('DBHOST'), port=os.getenv('DBPORT'))

    cursor = db.cursor()

    cursor.execute('SELECT hero_id, heroes.localized_name, max FROM (SELECT hero_id, max(count) FROM (SELECT match_id, hero_id, count(*) from( SELECT row_number() OVER (ORDER BY m_p_d.match_id ASC, g_ob.time ASC) - row_number() over (partition by m_p_d.match_id, m_p_d.hero_id ORDER BY m_p_d.match_id ASC, g_ob.time ASC) as row_num, m_p_d.match_id, m_p_d.hero_id, g_ob.time FROM game_objectives as g_ob JOIN matches_players_details as m_p_d ON g_ob.match_player_detail_id_1 = m_p_d.id WHERE g_ob.subtype = \'CHAT_MESSAGE_TOWER_KILL\' AND match_player_detail_id_1 IS not NULL ORDER BY m_p_d.match_id ASC, g_ob.time ASC ) table1 GROUP BY row_num, match_id, hero_id) table2 GROUP BY hero_id) table3 JOIN heroes ON hero_id = heroes.id ORDER BY max DESC, localized_name ASC')
    result = cursor.fetchall()

    cursor.close()
    db.close()

    result = jsonify(result).get_json()
    # print(result)

    if not result:
        return jsonify({})

    statistics = {
        "heroes": []
    }

    for hero in result:
        statistics["heroes"].append({"id": hero[0], "name": hero[1], "tower_kills": hero[2]})

    return jsonify(statistics)


@app.route('/v4/patches/', methods=['GET'])
def get_patches_orm():

    engine = create_engine("postgresql://" + LOG_DBS + ":" + PASWD_DBS + "@" + DBHOST + ":" + DBPORT + "/" + DBNAME, echo=True)
    Session = sessionmaker(bind=engine)

    session = Session()
    table1 = session.query(
        Patch.name.label("patch_version"),
        func.cast(func.extract('epoch', Patch.release_date), Integer).label("patch_start_date")).subquery()

    table2 = session.query(
        table1,
        func.lead(table1.c.patch_start_date, 1).over(order_by=table1.c.patch_version).label("patch_end_date")).subquery()

    result = session.query(
        table2,
        Match.id.label("match_id"),
        func.round(Match.duration/60.00, 2).label("match_duration")).join(Match, and_(Match.start_time >= table2.c.patch_start_date, Match.start_time < table2.c.patch_end_date), isouter=True).all()

    if not result:
        return jsonify({})
    # for record in result:
    #     print(record)

    # result = Player.geteve
    # result = jsonify(results).get_json()

    # print(result)
    patches = []
    for match in result:
        return_value = is_patch_in_list(patches, match.patch_version)
        if return_value is None:
            if match.match_id is None:
                patches.append({"patch_version": match.patch_version, "patch_start_date": match.patch_start_date, "patch_end_date": match.patch_end_date,
                                "matches": []})
            else:
                patches.append({"patch_version": match.patch_version, "patch_start_date": match.patch_start_date, "patch_end_date": match.patch_end_date, "matches": [{"match_id": match.match_id, "duration": str_to_float(match.match_duration)}]})
        else:
            patches[return_value]["matches"].append({"match_id": match.match_id, "duration": str_to_float(match.match_duration)})

    # print(patches)

    return jsonify(patches=patches)


@app.route('/v4/players/<player_id>/game_exp/', methods=['GET'])
def get_game_exp_orm(player_id):

    engine = create_engine("postgresql://" + LOG_DBS + ":" + PASWD_DBS + "@" + DBHOST + ":" + DBPORT + "/" + DBNAME, echo=True)
    Session = sessionmaker(bind=engine)

    session = Session()

    result = session.query(
        Player.id,
        case((Player.nick == null(), 'unknown'), else_=Player.nick).label("player_nick"),
        Hero.localized_name.label("hero_localized_name"),
        func.round(Match.duration/60.00, 2).label("match_duration_minutes"),
        (func.coalesce(MatchesPlayersDetail.xp_hero, 0) + func.coalesce(MatchesPlayersDetail.xp_creep, 0) + func.coalesce(MatchesPlayersDetail.xp_other, 0) + func.coalesce(MatchesPlayersDetail.xp_roshan, 0)).label("experiences_gained"),
        MatchesPlayersDetail.level.label("level_gained"),
        case(
            (and_(MatchesPlayersDetail.player_slot >= 0, MatchesPlayersDetail.player_slot <= 4, Match.radiant_win == true()), true()),
            (and_(MatchesPlayersDetail.player_slot >= 128, MatchesPlayersDetail.player_slot <= 132, Match.radiant_win == false()), true()),
            else_=false()
            ).label("winner"),
        Match.id.label("match_id")
        ).join(MatchesPlayersDetail, MatchesPlayersDetail.player_id == Player.id)\
        .join(Hero, MatchesPlayersDetail.hero_id == Hero.id)\
        .join(Match, MatchesPlayersDetail.match_id == Match.id)\
        .filter(Player.id == int(player_id))\
        .order_by(Match.id.asc()).all()

    # for record in result:
    #     print(record)

    if not result:
        return jsonify({})

    game_exp = {
        "id": result[0].id,
        "player_nick": result[0].player_nick,
        "matches": []
    }

    for match in result:
        game_exp["matches"].append({"match_id": match.match_id, "hero_localized_name": match.hero_localized_name, "match_duration_minutes": str_to_float(match.match_duration_minutes), "experiences_gained": match.experiences_gained, "level_gained": match.level_gained, "winner": match.winner})

    return jsonify(game_exp)


@app.route('/v4/players/<player_id>/game_objectives/', methods=['GET'])
def get_game_objectives_orm(player_id):
    engine = create_engine("postgresql://" + LOG_DBS + ":" + PASWD_DBS + "@" + DBHOST + ":" + DBPORT + "/" + DBNAME, echo=True)
    Session = sessionmaker(bind=engine)

    session = Session()

    result = session.query(
        Player.id,
        case((Player.nick == null(), 'unknown'), else_=Player.nick).label("player_nick"),
        Hero.localized_name.label("hero_localized_name"),
        Match.id.label("match_id"),
        func.coalesce(GameObjective.subtype, 'NO_ACTION').label("hero_action"),
        func.count().label("count")
        ).join(MatchesPlayersDetail, MatchesPlayersDetail.player_id == Player.id)\
        .join(Hero, MatchesPlayersDetail.hero_id == Hero.id)\
        .join(Match, MatchesPlayersDetail.match_id == Match.id)\
        .join(GameObjective, MatchesPlayersDetail.id == GameObjective.match_player_detail_id_1, isouter=True)\
        .filter(Player.id == int(player_id))\
        .group_by(Player.id, Hero.localized_name, Match.id, GameObjective.subtype)\
        .order_by(Match.id.asc()).all()

    # for record in result:
    #     print(record)

    if not result:
        return jsonify({})

    game_objectives = {
        "id": result[0].id,
        "player_nick": result[0].player_nick,
        "matches": []
    }

    for match in result:
        return_value = is_match_in_list(game_objectives["matches"], match.match_id)
        if return_value is None:
            game_objectives["matches"].append({"match_id": match.match_id, "hero_localized_name": match.hero_localized_name, "actions": [{"hero_action": match.hero_action, "count": match.count}]})
        else:
            game_objectives["matches"][return_value]["actions"].append({"hero_action": match.hero_action, "count": match.count})

    return jsonify(game_objectives)


@app.route('/v4/players/<player_id>/abilities/', methods=['GET'])
def get_abilities_orm(player_id):
    engine = create_engine("postgresql://" + LOG_DBS + ":" + PASWD_DBS + "@" + DBHOST + ":" + DBPORT + "/" + DBNAME, echo=True)
    Session = sessionmaker(bind=engine)

    session = Session()

    table1 = session.query(
        Player.id,
        case((Player.nick == null(), 'unknown'), else_=Player.nick).label("player_nick"),
        Hero.localized_name.label("hero_localized_name"),
        Match.id.label("match_id"),
        Ability.name.label("ability_name"),
        func.max(AbilityUpgrade.level).over(partition_by=(Match.id, Ability.name)).label("upgrade_level")
        ).join(MatchesPlayersDetail, MatchesPlayersDetail.player_id == Player.id)\
        .join(Hero, MatchesPlayersDetail.hero_id == Hero.id)\
        .join(Match, MatchesPlayersDetail.match_id == Match.id)\
        .join(AbilityUpgrade, MatchesPlayersDetail.id == AbilityUpgrade.match_player_detail_id)\
        .join(Ability, AbilityUpgrade.ability_id == Ability.id)\
        .filter(Player.id == int(player_id))\
        .group_by(Player.id, Hero.localized_name, Match.id, Ability.name, AbilityUpgrade.level)\
        .order_by(Match.id.asc()).subquery()

    result = session.query(
        table1,
        func.count().label("count")
        ).group_by(table1.c.id, table1.c.player_nick, table1.c.hero_localized_name, table1.c.match_id, table1.c.ability_name, table1.c.upgrade_level)\
        .order_by(table1.c.match_id.asc()).all()

    # for record in result:
    #     print(record)

    if not result:
        return jsonify({})

    abilities = {
        "id": result[0][0],
        "player_nick": result[0][1],
        "matches": []
    }

    for match in result:
        return_value = is_match_in_list(abilities["matches"], match[3])
        if return_value is None:
            abilities["matches"].append({"match_id": match[3], "hero_localized_name": match[2], "abilities": [{"ability_name": match[4], "count": match[6], "upgrade_level": match[5]}]})
        else:
            abilities["matches"][return_value]["abilities"].append({"ability_name": match[4], "count": match[6], "upgrade_level": match[5]})

    return jsonify(abilities)


@app.route('/v4/matches/<match_id>/top_purchases/', methods=['GET'])
def get_top_purchases_orm(match_id):
    engine = create_engine("postgresql://" + LOG_DBS + ":" + PASWD_DBS + "@" + DBHOST + ":" + DBPORT + "/" + DBNAME, echo=True)
    Session = sessionmaker(bind=engine)

    session = Session()

    table1 = session.query(
        Match.id.label("match_id"),
        MatchesPlayersDetail.hero_id,
        Hero.localized_name,
        PurchaseLog.item_id,
        Item.name.label("item_name"),
        func.count().label("count")
        ).join(MatchesPlayersDetail, PurchaseLog.match_player_detail_id == MatchesPlayersDetail.id)\
        .join(Hero, MatchesPlayersDetail.hero_id == Hero.id)\
        .join(Match, MatchesPlayersDetail.match_id == Match.id)\
        .join(Item, PurchaseLog.item_id == Item.id)\
        .filter(and_(
                    or_(
                        and_(MatchesPlayersDetail.player_slot >= 0, MatchesPlayersDetail.player_slot <= 4, Match.radiant_win == true()),
                        and_(MatchesPlayersDetail.player_slot >= 128, MatchesPlayersDetail.player_slot <= 132, Match.radiant_win == false())
                    ),
                    Match.id == int(match_id)
                ))\
        .group_by(Match.id, MatchesPlayersDetail.hero_id, Hero.localized_name, PurchaseLog.item_id, Item.name)\
        .subquery()

    table2 = session.query(
        table1,
        func.row_number().over(partition_by=table1.c.localized_name, order_by=(table1.c.hero_id.asc(), table1.c.count.desc(), table1.c.item_name.asc())).label("row_num"))\
        .order_by(table1.c.hero_id.asc(), table1.c.count.desc(), table1.c.item_name.asc())\
        .subquery()

    result = session.query(
        table2).filter(table2.c.row_num <= 5).all()

    # for record in result:
    #     print(record)

    if not result:
        return jsonify({})

    top_purchases = {
        "id": int(match_id),
        "heroes": []
    }

    for hero in result:
        return_value = is_hero_in_list(top_purchases["heroes"], hero[1])
        if return_value is None:
            top_purchases["heroes"].append({"id": hero[1], "name": hero[2], "top_purchases": [{"id": hero[3], "name": hero[4], "count": hero[5]}]})
        else:
            top_purchases["heroes"][return_value]["top_purchases"].append({"id": hero[3], "name": hero[4], "count": hero[5]})

    return jsonify(top_purchases)


@app.route('/v4/abilities/<ability_id>/usage/', methods=['GET'])
def get_abilities_usage_orm(ability_id):
    engine = create_engine("postgresql://" + LOG_DBS + ":" + PASWD_DBS + "@" + DBHOST + ":" + DBPORT + "/" + DBNAME, echo=True)
    Session = sessionmaker(bind=engine)

    session = Session()

    table1 = session.query(
        AbilityUpgrade.ability_id,
        Ability.name,
        Hero.id.label("hero_id"),
        Hero.localized_name.label("hero_name"),
        case(
            (and_(MatchesPlayersDetail.player_slot >= 0, MatchesPlayersDetail.player_slot <= 4, Match.radiant_win == true()), true()),
            (and_(MatchesPlayersDetail.player_slot >= 128, MatchesPlayersDetail.player_slot <= 132, Match.radiant_win == false()), true()),
            else_=false()
            ).label("winner"),
        func.cast((AbilityUpgrade.time * 100 / Match.duration), String).label("percent_time")
        ).join(Ability, Ability.id == AbilityUpgrade.ability_id)\
        .join(MatchesPlayersDetail, AbilityUpgrade.match_player_detail_id == MatchesPlayersDetail.id)\
        .join(Hero, Hero.id == MatchesPlayersDetail.hero_id)\
        .join(Match, Match.id == MatchesPlayersDetail.match_id)\
        .filter(AbilityUpgrade.ability_id == int(ability_id))\
        .subquery()

    count = func.count().label("count")

    result = session.query(
        table1.c.ability_id,
        table1.c.name,
        table1.c.hero_id,
        table1.c.hero_name,
        table1.c.winner,
        func.concat(func.substr(table1.c.percent_time, 1, func.length(table1.c.percent_time) - 1), "0-", func.substr(table1.c.percent_time, 1, func.length(table1.c.percent_time) - 1), "9").label("rozsah"),
        func.count().label("count")
        )\
        .distinct(table1.c.hero_id, table1.c.winner)\
        .group_by(table1.c.ability_id, table1.c.name, table1.c.hero_id, table1.c.hero_name, table1.c.winner, 'rozsah')\
        .order_by(table1.c.hero_id.asc(), table1.c.winner.desc(), count.desc())\
        .all()

    if not result:
        return jsonify({})
    # for record in result:
    #     print(record)

    abilities_usage = {
        "id": int(ability_id),
        "name": result[0][1],
        "heroes": []
    }

    for hero in result:
        return_value = is_hero_in_list(abilities_usage["heroes"], hero[2])
        if return_value is None:
            to_append = {"id": hero[2], "name": hero[3]}
            if hero[4]:
                to_append["usage_winners"] = {"bucket": hero[5], "count": hero[6]}
            else:
                to_append["usage_loosers"] = {"bucket": hero[5], "count": hero[6]}
            abilities_usage["heroes"].append(to_append)
        else:
            if hero[4]:
                abilities_usage["heroes"][return_value]["usage_winners"] = {"bucket": hero[5], "count": hero[6]}
            else:
                abilities_usage["heroes"][return_value]["usage_loosers"] = {"bucket": hero[5], "count": hero[6]}

    return jsonify(abilities_usage)


@app.route('/v4/statistics/tower_kills/', methods=['GET'])
def get_tower_kills_statistics_orm():
    engine = create_engine("postgresql://" + LOG_DBS + ":" + PASWD_DBS + "@" + DBHOST + ":" + DBPORT + "/" + DBNAME, echo=True)
    Session = sessionmaker(bind=engine)

    session = Session()

    table1 = session.query(
        (func.row_number().over(order_by=(MatchesPlayersDetail.match_id.asc(), GameObjective.time.asc())) - func.row_number().over(partition_by=(MatchesPlayersDetail.match_id, MatchesPlayersDetail.hero_id), order_by=(MatchesPlayersDetail.match_id.asc(), GameObjective.time.asc()))).label("row_num"),
        MatchesPlayersDetail.match_id,
        MatchesPlayersDetail.hero_id,
        GameObjective.time
        ).join(MatchesPlayersDetail, GameObjective.match_player_detail_id_1 == MatchesPlayersDetail.id)\
        .filter(and_(GameObjective.subtype == 'CHAT_MESSAGE_TOWER_KILL', GameObjective.match_player_detail_id_1 != null()))\
        .order_by(MatchesPlayersDetail.match_id.asc(), GameObjective.time.asc())\
        .subquery()

    table2 = session.query(
        table1.c.match_id,
        table1.c.hero_id,
        func.count().label("count")
        ).group_by(table1.c.row_num, table1.c.match_id, table1.c.hero_id)\
        .subquery()

    table3 = session.query(
        table2.c.hero_id,
        func.max(table2.c.count)
        ).group_by(table2.c.hero_id)\
        .subquery()

    result = session.query(
        table3.c.hero_id,
        Hero.localized_name,
        table3.c.max
        )\
        .join(Hero, table3.c.hero_id == Hero.id)\
        .order_by(table3.c.max.desc(), Hero.localized_name.asc())\
        .all()

    if not result:
        return jsonify({})

    # for record in result:
    #     print(record)

    statistics = {
        "heroes": []
    }

    for hero in result:
        statistics["heroes"].append({"id": hero[0], "name": hero[1], "tower_kills": hero[2]})

    return jsonify(statistics)


if __name__ == '__main__':
    app.run(debug=True)
