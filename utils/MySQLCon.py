import mysql.connector


class MySQLCon:
    def __init__(self, host, user, password):
        print("Connecting to database...")
        self.db = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database="ScrimBot"
        )
        self.cursor = self.db.cursor()
        print("Connected to database")

    def init_server(self, server_ip, server_name):
        init_server = "INSERT INTO servers(server_id, server_name, prefix) VALUES (%s,%s,%s)"
        self.cursor.execute(init_server, (server_ip, server_name, "!"))
        self.db.commit()

    def add_admin_role(self, role_name, role_id, server_ip):
        query = "INSERT INTO admin_role(role_id, role_name, server_ip) VALUES (%s,%s,%s)"
        self.cursor.execute(query, (role_id, role_name, server_ip))
