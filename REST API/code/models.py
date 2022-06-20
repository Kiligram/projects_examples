# coding: utf-8
from sqlalchemy import BigInteger, Boolean, CheckConstraint, Column, DateTime, ForeignKey, Index, Integer, Numeric, SmallInteger, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
metadata = Base.metadata


class Ability(Base):
    __tablename__ = 'abilities'

    id = Column(Integer, primary_key=True)
    name = Column(Text)


class AuthGroup(Base):
    __tablename__ = 'auth_group'

    id = Column(Integer, primary_key=True, server_default=text("nextval('auth_group_id_seq'::regclass)"))
    name = Column(String(150), nullable=False, unique=True)


class AuthUser(Base):
    __tablename__ = 'auth_user'

    id = Column(Integer, primary_key=True, server_default=text("nextval('auth_user_id_seq'::regclass)"))
    password = Column(String(128), nullable=False)
    last_login = Column(DateTime(True))
    is_superuser = Column(Boolean, nullable=False)
    username = Column(String(150), nullable=False, unique=True)
    first_name = Column(String(150), nullable=False)
    last_name = Column(String(150), nullable=False)
    email = Column(String(254), nullable=False)
    is_staff = Column(Boolean, nullable=False)
    is_active = Column(Boolean, nullable=False)
    date_joined = Column(DateTime(True), nullable=False)


class ClusterRegion(Base):
    __tablename__ = 'cluster_regions'

    id = Column(Integer, primary_key=True)
    name = Column(Text)


class DjangoContentType(Base):
    __tablename__ = 'django_content_type'
    __table_args__ = (
        UniqueConstraint('app_label', 'model'),
    )

    id = Column(Integer, primary_key=True, server_default=text("nextval('django_content_type_id_seq'::regclass)"))
    app_label = Column(String(100), nullable=False)
    model = Column(String(100), nullable=False)


class DjangoMigration(Base):
    __tablename__ = 'django_migrations'

    id = Column(BigInteger, primary_key=True, server_default=text("nextval('django_migrations_id_seq'::regclass)"))
    app = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    applied = Column(DateTime(True), nullable=False)


class DjangoSession(Base):
    __tablename__ = 'django_session'

    session_key = Column(String(40), primary_key=True, index=True)
    session_data = Column(Text, nullable=False)
    expire_date = Column(DateTime(True), nullable=False, index=True)


class DoctrineMigrationVersion(Base):
    __tablename__ = 'doctrine_migration_versions'

    version = Column(String(191), primary_key=True)
    executed_at = Column(TIMESTAMP(precision=0), server_default=text("NULL::timestamp without time zone"))
    execution_time = Column(Integer)


class Hero(Base):
    __tablename__ = 'heroes'

    id = Column(Integer, primary_key=True)
    name = Column(Text)
    localized_name = Column(Text)


class Item(Base):
    __tablename__ = 'items'

    id = Column(Integer, primary_key=True)
    name = Column(Text)


class Patch(Base):
    __tablename__ = 'patches'

    id = Column(Integer, primary_key=True, server_default=text("nextval('patches_id_seq'::regclass)"))
    name = Column(Text, nullable=False)
    release_date = Column(DateTime, nullable=False)


class Player(Base):
    __tablename__ = 'players'

    id = Column(Integer, primary_key=True)
    name = Column(Text)
    nick = Column(Text)


class AuthPermission(Base):
    __tablename__ = 'auth_permission'
    __table_args__ = (
        UniqueConstraint('content_type_id', 'codename'),
    )

    id = Column(Integer, primary_key=True, server_default=text("nextval('auth_permission_id_seq'::regclass)"))
    name = Column(String(255), nullable=False)
    content_type_id = Column(ForeignKey('django_content_type.id', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    codename = Column(String(100), nullable=False)

    content_type = relationship('DjangoContentType')


class AuthUserGroup(Base):
    __tablename__ = 'auth_user_groups'
    __table_args__ = (
        UniqueConstraint('user_id', 'group_id'),
    )

    id = Column(BigInteger, primary_key=True, server_default=text("nextval('auth_user_groups_id_seq'::regclass)"))
    user_id = Column(ForeignKey('auth_user.id', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    group_id = Column(ForeignKey('auth_group.id', deferrable=True, initially='DEFERRED'), nullable=False, index=True)

    group = relationship('AuthGroup')
    user = relationship('AuthUser')


class DjangoAdminLog(Base):
    __tablename__ = 'django_admin_log'
    __table_args__ = (
        CheckConstraint('action_flag >= 0'),
    )

    id = Column(Integer, primary_key=True, server_default=text("nextval('django_admin_log_id_seq'::regclass)"))
    action_time = Column(DateTime(True), nullable=False)
    object_id = Column(Text)
    object_repr = Column(String(200), nullable=False)
    action_flag = Column(SmallInteger, nullable=False)
    change_message = Column(Text, nullable=False)
    content_type_id = Column(ForeignKey('django_content_type.id', deferrable=True, initially='DEFERRED'), index=True)
    user_id = Column(ForeignKey('auth_user.id', deferrable=True, initially='DEFERRED'), nullable=False, index=True)

    content_type = relationship('DjangoContentType')
    user = relationship('AuthUser')


class Match(Base):
    __tablename__ = 'matches'

    id = Column(Integer, primary_key=True)
    cluster_region_id = Column(ForeignKey('cluster_regions.id'))
    start_time = Column(Integer)
    duration = Column(Integer)
    tower_status_radiant = Column(Integer)
    tower_status_dire = Column(Integer)
    barracks_status_radiant = Column(Integer)
    barracks_status_dire = Column(Integer)
    first_blood_time = Column(Integer)
    game_mode = Column(Integer)
    radiant_win = Column(Boolean)
    negative_votes = Column(Integer)
    positive_votes = Column(Integer)

    cluster_region = relationship('ClusterRegion')


class PlayerRating(Base):
    __tablename__ = 'player_ratings'

    id = Column(Integer, primary_key=True, server_default=text("nextval('player_ratings_id_seq'::regclass)"))
    player_id = Column(ForeignKey('players.id'))
    total_wins = Column(Integer)
    total_matches = Column(Integer)
    trueskill_mu = Column(Numeric)
    trueskill_sigma = Column(Numeric)

    player = relationship('Player')


class AuthGroupPermission(Base):
    __tablename__ = 'auth_group_permissions'
    __table_args__ = (
        UniqueConstraint('group_id', 'permission_id'),
    )

    id = Column(BigInteger, primary_key=True, server_default=text("nextval('auth_group_permissions_id_seq'::regclass)"))
    group_id = Column(ForeignKey('auth_group.id', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    permission_id = Column(ForeignKey('auth_permission.id', deferrable=True, initially='DEFERRED'), nullable=False, index=True)

    group = relationship('AuthGroup')
    permission = relationship('AuthPermission')


class AuthUserUserPermission(Base):
    __tablename__ = 'auth_user_user_permissions'
    __table_args__ = (
        UniqueConstraint('user_id', 'permission_id'),
    )

    id = Column(BigInteger, primary_key=True, server_default=text("nextval('auth_user_user_permissions_id_seq'::regclass)"))
    user_id = Column(ForeignKey('auth_user.id', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    permission_id = Column(ForeignKey('auth_permission.id', deferrable=True, initially='DEFERRED'), nullable=False, index=True)

    permission = relationship('AuthPermission')
    user = relationship('AuthUser')


class MatchesPlayersDetail(Base):
    __tablename__ = 'matches_players_details'
    __table_args__ = (
        Index('idx_match_id_player_id', 'match_id', 'player_slot', 'id'),
    )

    id = Column(Integer, primary_key=True, server_default=text("nextval('matches_players_details_id_seq'::regclass)"))
    match_id = Column(ForeignKey('matches.id'))
    player_id = Column(ForeignKey('players.id'))
    hero_id = Column(ForeignKey('heroes.id'))
    player_slot = Column(Integer)
    gold = Column(Integer)
    gold_spent = Column(Integer)
    gold_per_min = Column(Integer)
    xp_per_min = Column(Integer)
    kills = Column(Integer)
    deaths = Column(Integer)
    assists = Column(Integer)
    denies = Column(Integer)
    last_hits = Column(Integer)
    stuns = Column(Integer)
    hero_damage = Column(Integer)
    hero_healing = Column(Integer)
    tower_damage = Column(Integer)
    item_id_1 = Column(ForeignKey('items.id'))
    item_id_2 = Column(ForeignKey('items.id'))
    item_id_3 = Column(ForeignKey('items.id'))
    item_id_4 = Column(ForeignKey('items.id'))
    item_id_5 = Column(ForeignKey('items.id'))
    item_id_6 = Column(ForeignKey('items.id'))
    level = Column(Integer)
    leaver_status = Column(Integer)
    xp_hero = Column(Integer)
    xp_creep = Column(Integer)
    xp_roshan = Column(Integer)
    xp_other = Column(Integer)
    gold_other = Column(Integer)
    gold_death = Column(Integer)
    gold_buyback = Column(Integer)
    gold_abandon = Column(Integer)
    gold_sell = Column(Integer)
    gold_destroying_structure = Column(Integer)
    gold_killing_heroes = Column(Integer)
    gold_killing_creeps = Column(Integer)
    gold_killing_roshan = Column(Integer)
    gold_killing_couriers = Column(Integer)

    hero = relationship('Hero')
    item = relationship('Item', primaryjoin='MatchesPlayersDetail.item_id_1 == Item.id')
    item1 = relationship('Item', primaryjoin='MatchesPlayersDetail.item_id_2 == Item.id')
    item2 = relationship('Item', primaryjoin='MatchesPlayersDetail.item_id_3 == Item.id')
    item3 = relationship('Item', primaryjoin='MatchesPlayersDetail.item_id_4 == Item.id')
    item4 = relationship('Item', primaryjoin='MatchesPlayersDetail.item_id_5 == Item.id')
    item5 = relationship('Item', primaryjoin='MatchesPlayersDetail.item_id_6 == Item.id')
    match = relationship('Match')
    player = relationship('Player')


class Teamfight(Base):
    __tablename__ = 'teamfights'
    __table_args__ = (
        Index('teamfights_match_id_start_teamfight_id_idx', 'match_id', 'start_teamfight', 'id'),
    )

    id = Column(Integer, primary_key=True, server_default=text("nextval('teamfights_id_seq'::regclass)"))
    match_id = Column(ForeignKey('matches.id'))
    start_teamfight = Column(Integer)
    end_teamfight = Column(Integer)
    last_death = Column(Integer)
    deaths = Column(Integer)

    match = relationship('Match')


class AbilityUpgrade(Base):
    __tablename__ = 'ability_upgrades'

    id = Column(Integer, primary_key=True, server_default=text("nextval('ability_upgrades_id_seq'::regclass)"))
    ability_id = Column(ForeignKey('abilities.id'))
    match_player_detail_id = Column(ForeignKey('matches_players_details.id'))
    level = Column(Integer)
    time = Column(Integer)

    ability = relationship('Ability')
    match_player_detail = relationship('MatchesPlayersDetail')


class Chat(Base):
    __tablename__ = 'chats'

    id = Column(Integer, primary_key=True, server_default=text("nextval('chats_id_seq'::regclass)"))
    match_player_detail_id = Column(ForeignKey('matches_players_details.id'))
    message = Column(Text)
    time = Column(Integer)
    nick = Column(Text)

    match_player_detail = relationship('MatchesPlayersDetail')


class GameObjective(Base):
    __tablename__ = 'game_objectives'

    id = Column(Integer, primary_key=True, server_default=text("nextval('game_objectives_id_seq'::regclass)"))
    match_player_detail_id_1 = Column(ForeignKey('matches_players_details.id'))
    match_player_detail_id_2 = Column(ForeignKey('matches_players_details.id'))
    key = Column(Integer)
    subtype = Column(Text)
    team = Column(Integer)
    time = Column(Integer)
    value = Column(Integer)
    slot = Column(Integer)

    matches_players_detail = relationship('MatchesPlayersDetail', primaryjoin='GameObjective.match_player_detail_id_1 == MatchesPlayersDetail.id')
    matches_players_detail1 = relationship('MatchesPlayersDetail', primaryjoin='GameObjective.match_player_detail_id_2 == MatchesPlayersDetail.id')


class PlayerAction(Base):
    __tablename__ = 'player_actions'

    id = Column(Integer, primary_key=True, server_default=text("nextval('player_actions_id_seq'::regclass)"))
    unit_order_none = Column(Integer)
    unit_order_move_to_position = Column(Integer)
    unit_order_move_to_target = Column(Integer)
    unit_order_attack_move = Column(Integer)
    unit_order_attack_target = Column(Integer)
    unit_order_cast_position = Column(Integer)
    unit_order_cast_target = Column(Integer)
    unit_order_cast_target_tree = Column(Integer)
    unit_order_cast_no_target = Column(Integer)
    unit_order_cast_toggle = Column(Integer)
    unit_order_hold_position = Column(Integer)
    unit_order_train_ability = Column(Integer)
    unit_order_drop_item = Column(Integer)
    unit_order_give_item = Column(Integer)
    unit_order_pickup_item = Column(Integer)
    unit_order_pickup_rune = Column(Integer)
    unit_order_purchase_item = Column(Integer)
    unit_order_sell_item = Column(Integer)
    unit_order_disassemble_item = Column(Integer)
    unit_order_move_item = Column(Integer)
    unit_order_cast_toggle_auto = Column(Integer)
    unit_order_stop = Column(Integer)
    unit_order_buyback = Column(Integer)
    unit_order_glyph = Column(Integer)
    unit_order_eject_item_from_stash = Column(Integer)
    unit_order_cast_rune = Column(Integer)
    unit_order_ping_ability = Column(Integer)
    unit_order_move_to_direction = Column(Integer)
    match_player_detail_id = Column(ForeignKey('matches_players_details.id'))

    match_player_detail = relationship('MatchesPlayersDetail')


class PlayerTime(Base):
    __tablename__ = 'player_times'

    id = Column(Integer, primary_key=True, server_default=text("nextval('player_times_id_seq'::regclass)"))
    match_player_detail_id = Column(ForeignKey('matches_players_details.id'))
    time = Column(Integer)
    gold = Column(Integer)
    lh = Column(Integer)
    xp = Column(Integer)

    match_player_detail = relationship('MatchesPlayersDetail')


class PurchaseLog(Base):
    __tablename__ = 'purchase_logs'

    id = Column(Integer, primary_key=True, server_default=text("nextval('purchase_logs_id_seq'::regclass)"))
    match_player_detail_id = Column(ForeignKey('matches_players_details.id'))
    item_id = Column(ForeignKey('items.id'))
    time = Column(Integer)

    item = relationship('Item')
    match_player_detail = relationship('MatchesPlayersDetail')


class TeamfightsPlayer(Base):
    __tablename__ = 'teamfights_players'

    id = Column(Integer, primary_key=True, server_default=text("nextval('teamfights_players_id_seq'::regclass)"))
    teamfight_id = Column(ForeignKey('teamfights.id'))
    match_player_detail_id = Column(ForeignKey('matches_players_details.id'))
    buyback = Column(Integer)
    damage = Column(Integer)
    deaths = Column(Integer)
    gold_delta = Column(Integer)
    xp_start = Column(Integer)
    xp_end = Column(Integer)

    match_player_detail = relationship('MatchesPlayersDetail')
    teamfight = relationship('Teamfight')
