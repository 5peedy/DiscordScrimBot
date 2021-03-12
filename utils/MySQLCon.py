import mysql.connector


class MySQLCon:
    def __init__(self, host, user, password, database):
        print("Connecting to database...")
        self.db = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )
        self.cursor = self.db.cursor()
        print("Connected to database")

    def init_server(self, server_ip, server_name):
        init_server = "INSERT INTO servers(server_id, server_name, prefix) VALUES (%s,%s,%s)"
        self.cursor.execute(init_server, (server_ip, server_name, "!"))
        self.db.commit()

    def add_admin_role(self, role_name, role_id, server_id):
        query = "INSERT INTO admin_role(role_id, role_name, server_id) VALUES (%s,%s,%s)"
        self.cursor.execute(query, (role_id, role_name, server_id))
        self.db.commit()

    def remove_admin_role(self, role_id, server_id):
        query = "DELETE FROM admin_role WHERE role_id=" + str(role_id) + " AND server_id=" + str(server_id)
        self.cursor.execute(query)
        self.db.commit()

    def is_admin_role(self, server_id, role_id):
        query = "SELECT * FROM admin_role WHERE server_id=" + str(server_id) + " AND role_id=" + str(role_id)
        self.cursor.execute(query)
        if len(self.cursor.fetchall()) != 0:
            return True
        else:
            return False
