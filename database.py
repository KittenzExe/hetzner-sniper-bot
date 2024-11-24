import sqlite3
import requests

# Connect to the SQLite database
conn = sqlite3.connect('servers.db')
c = conn.cursor()

# Function to set up the database
def setup_database():
    c.execute('''
        CREATE TABLE IF NOT EXISTS live_servers (
            id INTEGER PRIMARY KEY,
            cpu TEXT,
            cpu_count INTEGER,
            traffic TEXT,
            bandwidth TEXT,
            ram TEXT,
            ram_size INTEGER,
            price REAL,
            setup_price REAL,
            hourly_price REAL,
            hdd_arr TEXT,
            hdd_size INTEGER,
            hdd_count INTEGER,
            datacenter TEXT,
            specials TEXT,
            next_reduce_timestamp TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS update_servers (
            id INTEGER PRIMARY KEY,
            cpu TEXT,
            cpu_count INTEGER,
            traffic TEXT,
            bandwidth TEXT,
            ram TEXT,
            ram_size INTEGER,
            price REAL,
            setup_price REAL,
            hourly_price REAL,
            hdd_arr TEXT,
            hdd_size INTEGER,
            hdd_count INTEGER,
            datacenter TEXT,
            specials TEXT,
            next_reduce_timestamp TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS snipes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            min_price REAL,
            max_price REAL
        )
    ''')
    conn.commit()

# Function to get a server by ID
def get_server_by_id(server_id):
    c.execute('SELECT * FROM update_servers WHERE id = ?', (server_id,))
    return c.fetchone()

# Function to get servers by criteria
def get_servers_by_criteria(criteria):
    criteria_dict = {}
    for criterion in criteria.split():
        key, value = criterion.split("=")
        criteria_dict[key] = value

    query = 'SELECT * FROM update_servers WHERE '
    query_conditions = []
    query_params = []

    for key, value in criteria_dict.items():
        if key == "price":
            min_price, max_price = map(float, value.split("-"))
            query_conditions.append('price BETWEEN ? AND ?')
            query_params.extend([min_price, max_price])
        else:
            query_conditions.append(f'{key} = ?')
            query_params.append(value)

    query += ' AND '.join(query_conditions)
    c.execute(query, query_params)
    return c.fetchall()

# Function to insert a snipe
def insert_snipe(user_id, min_price, max_price):
    c.execute('INSERT INTO snipes (user_id, min_price, max_price) VALUES (?, ?, ?)', (user_id, min_price, max_price))
    conn.commit()

# Function to fetch JSON data and modify prices
def fetch_json_data(url):
    response = requests.get(url)
    data = response.json()
    for server in data.get("server", []):
        server["price"] *= 1.234
        server["setup_price"] *= 1.234
        server["hourly_price"] *= 1.234
    return data

# Function to store JSON data in the live SQLite database
def store_data_in_live_db(data):
    c.execute('DELETE FROM live_servers')
    for server in data.get("server", []):
        c.execute('''
            INSERT INTO live_servers (id, cpu, cpu_count, traffic, bandwidth, ram, ram_size, price, setup_price, hourly_price, hdd_arr, hdd_size, hdd_count, datacenter, specials, next_reduce_timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            server["id"],
            str(server["cpu"]),
            server["cpu_count"],
            str(server["traffic"]),
            str(server["bandwidth"]),
            str(server["ram"]),
            server["ram_size"],
            server["price"],
            server["setup_price"],
            server["hourly_price"],
            ", ".join(map(str, server["hdd_arr"])),
            server["hdd_size"],
            server["hdd_count"],
            str(server["datacenter"]),
            str(server["specials"]),
            str(server["next_reduce_timestamp"])
        ))
    conn.commit()

# Function to update the update_servers table with changes from live_servers
def update_servers_db():
    # Fetch all live servers
    c.execute('SELECT * FROM live_servers')
    live_servers = c.fetchall()

    # Create a set of live server IDs
    live_server_ids = {server[0] for server in live_servers}

    # Fetch all update servers
    c.execute('SELECT * FROM update_servers')
    update_servers = c.fetchall()

    # Create a set of update server IDs
    update_server_ids = {server[0] for server in update_servers}

    # Determine which servers need to be removed from update_servers
    servers_to_remove = update_server_ids - live_server_ids

    # Remove servers that are no longer in live_servers
    for server_id in servers_to_remove:
        c.execute('DELETE FROM update_servers WHERE id = ?', (server_id,))

    # Update or insert servers from live_servers into update_servers
    for live_server in live_servers:
        c.execute('SELECT * FROM update_servers WHERE id = ?', (live_server[0],))
        update_server = c.fetchone()

        if update_server:
            # Update the existing record if there are changes
            if live_server != update_server:
                c.execute('''
                    UPDATE update_servers
                    SET cpu = ?, cpu_count = ?, traffic = ?, bandwidth = ?, ram = ?, ram_size = ?, price = ?, setup_price = ?, hourly_price = ?, hdd_arr = ?, hdd_size = ?, hdd_count = ?, datacenter = ?, specials = ?, next_reduce_timestamp = ?
                    WHERE id = ?
                ''', (
                    str(live_server[1]),
                    live_server[2],
                    str(live_server[3]),
                    str(live_server[4]),
                    str(live_server[5]),
                    live_server[6],
                    live_server[7],
                    live_server[8],
                    live_server[9],
                    str(live_server[10]),
                    live_server[11],
                    live_server[12],
                    str(live_server[13]),
                    str(live_server[14]),
                    str(live_server[15]),
                    live_server[0]
                ))
        else:
            # Insert the new record if it doesn't exist
            c.execute('''
                INSERT INTO update_servers (id, cpu, cpu_count, traffic, bandwidth, ram, ram_size, price, setup_price, hourly_price, hdd_arr, hdd_size, hdd_count, datacenter, specials, next_reduce_timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                live_server[0],
                str(live_server[1]),
                live_server[2],
                str(live_server[3]),
                str(live_server[4]),
                str(live_server[5]),
                live_server[6],
                live_server[7],
                live_server[8],
                str(live_server[9]),
                live_server[10],
                live_server[11],
                str(live_server[12]),
                str(live_server[13]),
                str(live_server[14]),
                str(live_server[15])
            ))
    conn.commit()

# Function to check for new snipes
def check_for_snipes():
    c.execute('SELECT * FROM snipes')
    snipes = c.fetchall()
    new_entries = []
    for snipe in snipes:
        user_id, min_price, max_price = snipe[1], snipe[2], snipe[3]
        c.execute('SELECT * FROM update_servers WHERE price BETWEEN ? AND ?', (min_price, max_price))
        servers = c.fetchall()
        for server in servers:
            c.execute('SELECT * FROM snipes WHERE user_id = ? AND min_price = ? AND max_price = ? AND id = ?', (user_id, min_price, max_price, server[0]))
            if not c.fetchone():
                new_entries.append((user_id, server))
                c.execute('INSERT OR IGNORE INTO snipes (user_id, min_price, max_price, id) VALUES (?, ?, ?, ?)', (user_id, min_price, max_price, server[0]))
    conn.commit()
    return new_entries

# Function to get the server count from the database
def get_server_count():
    c.execute('SELECT COUNT(*) FROM update_servers')
    return c.fetchone()[0]