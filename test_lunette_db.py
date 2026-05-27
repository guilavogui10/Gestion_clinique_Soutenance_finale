import pymysql

conn = pymysql.connect(host='localhost', user='root', password='', database='soutenance')
cursor = conn.cursor(pymysql.cursors.DictCursor)
cursor.execute("SELECT code_visite, statut_patient FROM visite")
visits = cursor.fetchall()
print('Visites:', visits)

cursor.execute("SELECT * FROM acte_medical")
actes = cursor.fetchall()
print('Actes:', actes)
