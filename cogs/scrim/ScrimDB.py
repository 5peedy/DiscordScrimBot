from cgitb import reset

import mysql.connector


class ScrimDB:
    def __init__(self, client):
        self.client = client
        self.db = client.db
        self.cursor = self.db.cursor()

    def update(self):
        self.db = self.client.db
        self.cursor = self.db.cursor()

    def init_scrim(self, name, lobby_count, mode, min_teams, max_teams, checkin_channel_id, checkout_channel_id,
                   lobbystatus_channel_id, lobbyannounce_channel_id, server_id, lootspots):
        self.update()
        query = "INSERT INTO scrims " \
                "(scrim_name, mode, lobby_count, min_teams, max_teams, checkin_channel_id, checkout_channel_id," \
                "lobbystatus_channel_id, lobbyannounce_channel_id, open, server_id) " \
                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        self.cursor.execute(query,
                            (name, mode, lobby_count, min_teams, max_teams, checkin_channel_id, checkout_channel_id,
                             lobbystatus_channel_id, lobbyannounce_channel_id, 0, server_id))

        scrim_id = self.get_scrim_id(server_id=server_id, scrim_name=name)

        for x in lootspots:
            query = "INSERT INTO lobby_channels (channel_id, scrim_id)" \
                    "VALUES (%s, %s)"
            self.cursor.execute(query, (x, scrim_id))
        self.db.commit()

    def open_scrim(self, server_id, scrim_name):
        self.update()
        query = "UPDATE scrims SET open = 1 WHERE server_id = {} AND scrim_name = '{}'".format(server_id, scrim_name)
        self.cursor.execute(query)
        self.db.commit()

    def close_scrim(self, server_id, scrim_name):
        self.update()
        query = "UPDATE scrims SET open = 0 WHERE server_id = {} AND scrim_name = '{}'".format(server_id, scrim_name)
        self.cursor.execute(query)
        self.db.commit()

    def reset_scrim(self, scrim_id):
        self.update()
        query = "DELETE FROM teams WHERE scrim_id = {}".format(scrim_id)
        self.cursor.execute(query)
        self.db.commit()

    def add_team(self, role_id, name, tier, scrim_id, mention):
        self.update()
        query = "SELECT team_id FROM teams WHERE role_id={} AND scrim_id={}".format(role_id, scrim_id)
        self.cursor.execute(query)
        if self.cursor.fetchone() is not None:
            return False

        query = "INSERT INTO teams (role_id, name, tier, mention, scrim_id) VALUES(%s, %s, %s, %s, %s)"
        self.cursor.execute(query, (role_id, name, tier, mention, scrim_id))
        self.db.commit()
        return True

    def del_team(self, role_id, scrim_id):
        self.update()
        query = "SELECT team_id FROM teams WHERE role_id={} AND scrim_id={}".format(role_id, scrim_id)
        self.cursor.execute(query)
        if self.cursor.fetchone() is None:
            return False
        query = "DELETE FROM teams WHERE role_id = {} AND scrim_id = {}".format(role_id, scrim_id)
        self.cursor.execute(query)
        self.db.commit()
        return True

    def get_scrim_id(self, server_id, scrim_name=None, checkin_id=None, checkout_id=None):
        self.update()
        if scrim_name is not None:
            query = "SELECT id FROM scrims WHERE server_id = {} AND scrim_name = '{}'".format(server_id, scrim_name)
        elif checkin_id is not None:
            query = "SELECT id FROM scrims WHERE server_id = {} AND checkin_channel_id = {}".format(server_id,
                                                                                                    checkin_id)
        elif checkout_id is not None:
            query = "SELECT id FROM scrims WHERE server_id = {} AND checkout_channel_id = {}".format(server_id,
                                                                                                     checkout_id)
        self.cursor.execute(query)
        return self.cursor.fetchone()[0]

    def get_scrim_name(self, scrim_id):
        self.update()
        query = "SELECT scrim_name FROM scrims WHERE id = {}".format(scrim_id)
        self.cursor.execute(query)
        return self.cursor.fetchone()[0]

    def get_server_from_scrim(self, scrim_id):
        self.update()
        query = "SELECT server_id FROM scrims WHERE id = {}".format(scrim_id)
        self.cursor.execute(query)
        return self.cursor.fetchone()[0]

    def get_scrims(self, server_id):
        self.update()
        query = "SELECT scrim_name, id FROM scrims WHERE server_id = {}".format(server_id)
        self.cursor.execute(query)
        fetched = self.cursor.fetchall()
        result = []
        for entry in fetched:
            result.append({
                "name": entry[0],
                "id": entry[1]
            })
        return result

    def get_scrim_channels(self, scrim_id):
        self.update()
        query = "SELECT checkin_channel_id, checkout_channel_id, lobbystatus_channel_id, lobbyannounce_channel_id " \
                "FROM scrims WHERE id = {}".format(scrim_id)
        self.cursor.execute(query)
        fetched = self.cursor.fetchone()
        result = {
            "checkin": fetched[0],
            "checkout": fetched[1],
            "status": fetched[2],
            "announce": fetched[3]
        }
        return result

    def get_lootspot_channel_ids(self, scrim_id):
        self.update()
        query = "SELECT channel_id FROM lobby_channels WHERE scrim_id = {}".format(scrim_id)
        self.cursor.execute(query)
        fetched = self.cursor.fetchall()
        result = []
        for entry in fetched:
            result.append(entry[0])
        return result

    def get_scrim_mode(self, scrim_id):
        self.update()
        query = "SELECT mode FROM scrims WHERE id = {}".format(scrim_id)
        self.cursor.execute(query)
        return self.cursor.fetchone()[0]

    def get_scrim_lobby_params(self, scrim_id):
        self.update()
        query = "SELECT lobby_count, min_teams, max_teams FROM scrims WHERE id = {}".format(scrim_id)
        self.cursor.execute(query)
        fetched = self.cursor.fetchone()
        result = {
            "lobby_count": fetched[0],
            "min_teams": fetched[1],
            "max_teams": fetched[2]
        }
        return result

    def get_scrim_teams(self, scrim_id):
        self.update()
        query = "SELECT role_id, tier, mention FROM teams WHERE scrim_id = {} ORDER BY team_id".format(scrim_id)
        self.cursor.execute(query)
        fetched = self.cursor.fetchall()
        result = []
        for team in fetched:
            entry = {
                "role_id": team[0],
                "tier": int(team[1]),
                "mention": team[2]
            }
            result.append(entry)
        return result

    def get_tier_roles(self, server_id):
        self.update()
        query = "SELECT role_id, tier, mention FROM tier_roles WHERE server_id = '{}' ORDER BY tier".format(server_id)
        self.cursor.execute(query)
        fetched = self.cursor.fetchall()
        result = []
        for entry in fetched:
            tier = {
                "id": entry[0],
                "tier": int(entry[1]),
                "mention": entry[2]
            }
            result.append(tier)
        return result

    def is_scrims_open(self, server_id, checkin=None, checkout=None):
        self.update()
        if checkin is not None:
            query = "SELECT open FROM scrims WHERE server_id = '{}' AND checkin_channel_id = '{}'".format(server_id,
                                                                                                          checkin)
        elif checkout is not None:
            query = "SELECT open FROM scrims WHERE server_id = '{}' AND checkout_channel_id = '{}'".format(server_id,
                                                                                                          checkout)
        self.cursor.execute(query)
        result = self.cursor.fetchone()[0]
        if result == 1:
            return True
        else:
            return False

    def is_checkin_channel(self, server_id, channel_id):
        self.update()
        query = "SELECT id FROM scrims WHERE server_id = {} AND checkin_channel_id = {}".format(server_id, channel_id)
        self.cursor.execute(query)
        result = self.cursor.fetchone()
        if result is not None:
            return True
        else:
            return False

    def is_checkout_channel(self, server_id, channel_id):
        self.update()
        query = "SELECT id FROM scrims WHERE server_id = {} AND checkout_channel_id = {}".format(server_id, channel_id)
        self.cursor.execute(query)
        result = self.cursor.fetchone()
        if result is not None:
            return True
        else:
            return False

    def is_tier_role(self, server_id, role_id):
        self.update()
        query = "SELECT id FROM tier_roles WHERE server_id = {} AND role_id = {}".format(server_id, role_id)
        self.cursor.execute(query)
        result = self.cursor.fetchone()
        if result is not None:
            return True
        else:
            return False

    def get_date(self, server_id, scrim_name):
        query = "SELECT date FROM scrims WHERE server_id = {} AND scrim_name = '{}'".format(server_id, scrim_name)
        self.cursor.execute(query)
        result = self.cursor.fetchone()[0]
        if result is None:
            return ""
        else:
            return result

    def set_date(self, server_id, scrim_name, scrim_date):
        query = "UPDATE scrims SET scrim_date = {} WHERE server_id = {} AND scrim_name = '{}'".format(scrim_date, server_id, scrim_name)
        self.cursor.execute(query)
        self.db.commit()
