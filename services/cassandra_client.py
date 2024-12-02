import os
from cassandra.cluster import Cluster
from cassandra.query import SimpleStatement, dict_factory
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Cassandra environment variables
CASSANDRA_CLUSTER = os.getenv('CASSANDRA_CLUSTER')
CASSANDRA_KEYSPACE = os.getenv('CASSANDRA_KEYSPACE')

class CassandraClient:
    def __init__(self, cluster=CASSANDRA_CLUSTER, keyspace=CASSANDRA_KEYSPACE):
        self.cluster = Cluster([cluster])  # Use the IP of your Cassandra node
        self.session = self.cluster.connect()
        self._create_keyspace(keyspace)


    def _create_keyspace(self, keyspace):
        query = f"""
            CREATE KEYSPACE IF NOT EXISTS {keyspace}
            WITH replication = {{'class': 'SimpleStrategy', 'replication_factor': 1}}
        """
        
        # Execute the query
        self.session.execute(query)
        self.session.set_keyspace(keyspace)

        print(f"Keyspace '{keyspace}' created successfully.")
    
    def create_table_user(self):

        # Create the 'users' table
        query = """
        CREATE TABLE IF NOT EXISTS users (
            user_id UUID PRIMARY KEY,
            username TEXT,
            email TEXT
        );
        """
        # Execute the query
        self.session.execute(query)
        print("Users table created successfully.")

    def get_user(self, id):

        # Return a dict
        self.session.row_factory = dict_factory

        # Parameterized query to prevent SQL injection
        query = SimpleStatement("""
            SELECT * 
            FROM users 
            WHERE user_id = %s
        """)

        # Execute the query with the UUID parameter
        result = self.session.execute(query, (id,))
        
        # Fetch and return the result
        return result.one()
     
    def add_user(self, user):
        query = SimpleStatement("""
            INSERT INTO users (user_id, username, email)
            VALUES (%s, %s, %s)
        """)

        # Execute the query with the user's data
        self.session.execute(query, (user['user_id'], user['username'], user['email']))

        print(f"User {user['username']} added successfully.")        

    def shutdown(self):
        return self.cluster.shutdown()