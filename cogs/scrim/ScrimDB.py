import mysql.connector


class ScrimDB:
    def __init__(self, client):
        self.db = client.db
        self.cursor = self.db.cursor()

    def init_scrim(self, name, lobby_count, mode, min_teams, max_teams, checkin_channel_id, checkout_channel_id,
                   lobbystatus_channel_id, lobbyannounce_channel_id, server_id, lootspots):
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
        query = "UPDATE scrims SET open = 1 WHERE server_id = {} AND scrim_name = '{}'".format(server_id, scrim_name)
        self.cursor.execute(query)
        self.db.commit()

    def close_scrims(self, server_id, scrim_name):
        query = "UPDATE scrims SET open = 0 WHERE server_id = {} AND scrim_name = '{}'".format(server_id, scrim_name)
        self.cursor.execute(query)
        self.db.commit()

    def add_team(self, role_id, name, tier, scrim_id):
        query = "SELECT team_id FROM teams WHERE role_id={} AND scrim_id={}".format(role_id, scrim_id)
        self.cursor.execute(query)
        if self.cursor.fetchone() is not None:
            return False

        query = "INSERT INTO teams (role_id, name, tier, scrim_id) VALUES(%s, %s, %s, %s)"
        self.cursor.execute(query, (role_id, name, tier, scrim_id))
        self.db.commit()
        return True

    def del_team(self, role_id, scrim_id):
        query = "SELECT team_id FROM teams WHERE role_id={} AND scrim_id={}".format(role_id, scrim_id)
        self.cursor.execute(query)
        if self.cursor.fetchone() is None:
            return False
        query = "DELETE FROM teams WHERE role_id = {} AND scrim_id = {}".format(role_id, scrim_id)
        self.cursor.execute(query)
        self.db.commit()
        return True

    def get_scrim_id(self, server_id, scrim_name=None, checkin_id=None, checkout_id=None):
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

    def get_tier_roles(self, server_id):
        query = "SELECT role_id, tier FROM tier_roles WHERE server_id = '{}'".format(server_id)
        self.cursor.execute(query)
        return self.cursor.fetchall()

    def is_scrims_open(self, server_id, checkin=None, checkout=None):
        if checkin is not None:
            query = "SELECT open FROM scrims WHERE server_id = '{}' AND checkin_channel_id = '{}'".format(server_id,
                                                                                                          checkin)
        elif checkout is not None:
            query = "SELECT open FROM scrims WHERE server_id = '{}' AND checkin_channel_id = '{}'".format(server_id,
                                                                                                          checkout)
        self.cursor.execute(query)
        result = self.cursor.fetchone()[0]
        if result == 1:
            return True
        else:
            return False

    def is_checkin_channel(self, server_id, channel_id):
        query = "SELECT id FROM scrims WHERE server_id = {} AND checkin_channel_id = {}".format(server_id, channel_id)
        self.cursor.execute(query)
        result = self.cursor.fetchone()
        if result is not None:
            return True
        else:
            return False

    def is_checkout_channel(self, server_id, channel_id):
        query = "SELECT id FROM scrims WHERE server_id = {} AND checkout_channel_id = {}".format(server_id, channel_id)
        self.cursor.execute(query)
        result = self.cursor.fetchone()
        if result is not None:
            return True
        else:
            return False
