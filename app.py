from flask import Flask, request, jsonify
import snowflake.connector
import json
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Retrieve Snowflake connection settings from environment variables
ACCOUNT = os.getenv("SNOWFLAKE_ACCOUNT")        # e.g., "ddb43411.us-east-1"
USER = os.getenv("SNOWFLAKE_USER")              # e.g., "ROYD"
PASSWORD = os.getenv("SNOWFLAKE_PASSWORD")      # e.g., "Aa12345"
WAREHOUSE = os.getenv("SNOWFLAKE_WAREHOUSE")    # e.g., "COMPUTE_WH"
ROLE = os.getenv("SNOWFLAKE_ROLE")              # e.g., "ACCOUNTADMIN"
DATABASE = os.getenv("SNOWFLAKE_DATABASE")      # e.g., "MY_DB"
SCHEMA = os.getenv("SNOWFLAKE_SCHEMA")          # e.g., "PUBLIC"
TABLE = os.getenv("SNOWFLAKE_TABLE")            # e.g., "FRONTEGG_EVENTS"
APP_PORT = int(os.getenv("APP_PORT", 4000))     # e.g., 40000

@app.route("/", methods=["POST"])
def webhook():
    # Retrieve the JSON payload from the incoming webhook
    payload = request.get_json()
    if not payload:
        return jsonify({"error": "Invalid payload"}), 400

    # Convert the payload to a JSON string
    payload_json = json.dumps(payload)

    # Build the SQL query using the table name from the environment variable
    insert_query = f"""
        INSERT INTO {TABLE} (
            EVENT_ID,
            EVENT_KEY,
            USER_ID,
            USER_NAME,
            USER_EMAIL,
            USER_CREATED_AT,
            RAW_PAYLOAD
        )
        SELECT
            UUID_STRING() AS EVENT_ID,
            RAW_PAYLOAD['eventKey']::STRING AS EVENT_KEY,
            RAW_PAYLOAD['user']['id']::STRING AS USER_ID,
            RAW_PAYLOAD['user']['name']::STRING AS USER_NAME,
            RAW_PAYLOAD['user']['email']::STRING AS USER_EMAIL,
            TRY_TO_TIMESTAMP(RAW_PAYLOAD['user']['createdAt']::STRING) AS USER_CREATED_AT,
            RAW_PAYLOAD
        FROM (SELECT PARSE_JSON(%s) AS RAW_PAYLOAD)
    """

    conn = None
    try:
        # Establish a connection to Snowflake using environment variables
        conn = snowflake.connector.connect(
            user=USER,
            password=PASSWORD,
            account=ACCOUNT,
            warehouse=WAREHOUSE,
            role=ROLE,
            database=DATABASE,
            schema=SCHEMA
        )
        with conn.cursor() as cur:
            cur.execute(insert_query, (payload_json,))
        return jsonify({"status": "success"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    # Listen on all interfaces on the port specified by the environment variable
    app.run(host='0.0.0.0', port=APP_PORT)
