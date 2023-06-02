import json
from flask import Flask, request, make_response
from flask_cors import CORS
import psycopg2

app = Flask(__name__)
CORS(app, origins=['http://localhost:5173'])

# Настройки соединения с базой данных PostgreSQL
DB_HOST = 'localhost'
DB_PORT = '5433'
DB_NAME = 'MyBrickVault'
DB_USER = 'postgres'
DB_PASSWORD = '123'

# Создание подключения к базе данных PostgreSQL
conn = psycopg2.connect(
    host=DB_HOST,
    port=DB_PORT,
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD
)

# Создание курсора для выполнения операций с базой данных
cur = conn.cursor()


@app.route('/', methods=['GET'])
def my_table():
    if request.method == 'GET':
        # get data from DB
        cur.execute("SELECT * FROM bricks WHERE quantity != 0")
        rows = cur.fetchall()
        return json.dumps(rows)


@app.route('/search', methods=['GET'])
def search_result():
    if request.method == 'GET':
        # get data from DB
        cur.execute("""WITH parts_needed AS (
    SELECT
        s.id,
        b.code AS part_id,
        (elems.item_object ->> 'quantity')::int AS parts_needed
    FROM
        "sets" s
        CROSS JOIN LATERAL jsonb_array_elements(s.parts) WITH ORDINALITY elems(item_object, position)
        LEFT JOIN bricks b ON b.code = elems.item_object ->> 'id'
    WHERE
        s.parts IS NOT NULL
), parts_owned AS (
    SELECT
        code AS part_id,
        quantity AS parts_owned
    FROM
        bricks
)
SELECT
    pn.id,
    pn.part_id,
    pn.parts_needed,
    po.parts_owned,
    CASE WHEN (pn.parts_needed <= po.parts_owned) THEN 'Enough' ELSE 'Not enough' END AS availability
FROM
    parts_needed pn
    JOIN parts_owned po ON pn.part_id = po.part_id
ORDER BY
    pn.id, pn.part_id;""")
        rows = cur.fetchall()
        # rows = [[0, , 1, w,e 1], []]
        # rows = [{id: 999, bricks: []}]
        # {"777": [[123, 2, 6], []], id: []}
        result = {}
        for row in rows:
            set_id = "" + row[0]
            if not set_id in result:
                result[set_id] = [row[1:-1]]
            else:
                result[set_id].append(row[1:-1])

        response = make_response(json.dumps(result))

        response.headers['Access-Control-Allow-Origin'] = '*'
        return response
