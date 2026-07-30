import sqlite3

connection = sqlite3.connect("arkagents.db")

cursor = connection.cursor()

cursor.execute("""
SELECT BOOKING_ID, TOTAL_PRICE FROM CUSTOMER WHERE DESTINATION = "Dubai"
""")

ans = cursor.fetchall()

for row in ans:
    print(row)

connection.close()