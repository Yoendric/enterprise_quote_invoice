from flask import Flask, render_template, url_for, redirect, session, request
import webbrowser
import sqlite3
from datetime import datetime
from waitress import serve
import pyautogui as pag
from generate_document import generate_quote_pdf, generate_invoice_pdf, split_text_note

LINK_DATABASE = "database/britorepair.db"

def new_id():
    conn = sqlite3.connect(LINK_DATABASE)
    cur = conn.cursor()
    cur.execute("SELECT * FROM materials")
    rows = cur.fetchall()
    if rows:
        for row in rows:
            pass
        return row[0]+1
    return 1

def delete_materials(sql):
    conn = sqlite3.connect(LINK_DATABASE)
    cur = conn.cursor()
    cur.execute("DELETE FROM materials where id ={}".format(sql))
    conn.commit()

def insert_materials(sql_string):
    conn = sqlite3.connect(LINK_DATABASE)
    cur = conn.cursor()
    cur.execute(sql_string)
    conn.commit()

def fecth_raw():
    conn = sqlite3.connect(LINK_DATABASE)
    cur = conn.cursor()
    cur.execute("SELECT * FROM materials")
    rows = cur.fetchall()
    return rows

def data_raw(filter_1):
    conn = sqlite3.connect(LINK_DATABASE)
    cur = conn.cursor()
    cur.execute("SELECT * FROM materials where id = {}".format(filter_1))
    rows = cur.fetchall()
    return rows

def remove_elemt_request(reQ):
    adds = dict(reQ)
    try:
        del adds['raw']
    except:
        pass
    del adds['fname']
    del adds['aditional']
    temp = dict()
    for i in adds:
        if adds[i] == '0' or adds[i] == '':            
            pass
        else:
           temp[i] = adds[i]        
    return temp

def sort_DB():
    rows = fecth_raw()
    date = list()
    element = list()
    for i in rows:
        if i[1] not in element:
            element.append(i[1])
            date.append(list(i))
    element.sort()
    try:
        element.remove(element[element.index('ADDITIONAL COSTS')])
        element.append('ADDITIONAL COSTS')
    except:
        pass
    count = 1
    rows = list()
    for i in element:
        for j in date:
            if j[1] == i:
                rows.append([count, j[1],j[2],j[3]])
                count += 1
    insert_materials("""DELETE FROM materials""")
    for i in rows:
        sql_str = """INSERT INTO materials VALUES ({0},"{1}","{2}",{3})""".format(i[0],i[1],i[2],i[3])
        insert_materials(sql_str)  

def company_database():
    conn = sqlite3.connect(LINK_DATABASE)
    cur = conn.cursor()
    cur.execute("SELECT * FROM company")
    rows = cur.fetchall()
    return rows

def get_number_invoice():
    con = sqlite3.connect(LINK_DATABASE)
    cursorObj = con.cursor()
    cursorObj.execute("SELECT * from sqlite_sequence")  
    rows = cursorObj.fetchall()
    if rows:
        for row in rows:
            return row[1] + 1
    else:
        return 1

def get_database_invoice():
    con = sqlite3.connect(LINK_DATABASE)
    cursor = con.cursor()
    rowsQuery = "SELECT Count() FROM customer"
    cursor.execute(rowsQuery)
    elementAll = cursor.fetchone()[0]
    rowsQuery = "SELECT * FROM customer"
    if elementAll >= 1:
        cursor.execute(rowsQuery)
        rows = cursor.fetchall()
        return rows
    else:
        return None

def get_individual_invoice():
    con = sqlite3.connect(LINK_DATABASE)
    cursor = con.cursor()
    rowsQuery = "SELECT Count() FROM invoice"
    cursor.execute(rowsQuery)
    elementAll = cursor.fetchone()[0]
    rowsQuery = "SELECT * FROM invoice"
    if elementAll >= 1:
        cursor.execute(rowsQuery)
        rows = cursor.fetchall()
        return rows

def data_invoice_month(row,canceled):
    date = dict()
    for i in row:
        if i[1] in canceled:
            pass
        else:
            mult = 0
            if i[4] == 'TRUE':
                mult = 0.075
            if not i[3][0:3]+i[3][-4:len(i[3])] in date:
                date[i[3][0:3]+i[3][-4:len(i[3])]] = {1:round(i[2]/(1+mult),2),2:1}
            else:
                date[i[3][0:3]+i[3][-4:len(i[3])]][1] = round(round(i[2]/(1+mult),2) + date[i[3][0:3]+i[3][-4:len(i[3])]][1],2)
                date[i[3][0:3]+i[3][-4:len(i[3])]][2] += 1
    if date:
        ventas_por_mes = list()
        mes = list()
        cant_inv = list()
        for i in date:
            mes.append(i)
            ventas_por_mes.append(date[i][1])
            cant_inv.append(date[i][2])
        return ventas_por_mes,mes,cant_inv
    else:
        return None, None, None

def get_data_database():
    rows = get_database_invoice()
    if rows:
        f = get_individual_invoice()
        pay = 0
        no_pay = 0
        total_mon = 0
        total_pen = 0
        msg_no_cob = list()
        msg = list()
        elementAll = len(rows)
        canceled = list()
        for row in rows:
            if ((row[15] == 1) and (row[17] != 'TRUE')):
                pay += 1
                total_mon += row[13]
                msg.append((row[0],"Fully Charged"))
            elif (row[17] != 'TRUE'):
                no_pay += 1
                total_pen += row[14]
                msg_no_cob.append(row)
                total_mon += row[13] 
                msg.append((row[0],"Pending Charged"))
            else:
                msg.append((row[0],"Invoice Canceled"))
                if not row[0] in canceled:
                    canceled.append(row[0])
        gan,mes,ci = data_invoice_month(f,canceled)
        return elementAll,no_pay,pay,no_pay/(pay+no_pay)*100,total_mon,total_pen,msg,msg_no_cob,[gan,ci,mes]
    else:        
        return 0,0,0,0,0,0,None,None,None

def insert_individual(a,b,c):
    con = sqlite3.connect(LINK_DATABASE)
    cursorObj = con.cursor()
    value = str(a) + ',' + str(b) + ',\'' + datetime.today().strftime('%m/%d/%Y') + '\',' + '\'' + c + '\''    
    sql_sintaxis = """INSERT INTO invoice (number_invoice,pay,fecha,tax) VALUES({})""".format(value)
    cursorObj.execute(sql_sintaxis)
    con.commit()
    con.close()

def insert_date(a,b,c,d):
    con = sqlite3.connect(LINK_DATABASE)
    cursorObj = con.cursor()
    w=''
    for i in c:
        if c[i] == True:
            w = w + '1'
        else:
            w = w + '0'
    a.update(b)
    a['working'] = w
    column =''
    value =''
    for i in a:
        if ((i == 'feet') or (i == 1)):
            if i==1:
                column =  column + 'total,'
            else:
                column =  column + i +','
            value =  value + str(a[i]) +','
        elif (i == 2):
            column =  column + 'balance, pay_all,'
            if (a[i] == False):
                value =  value + str(a[1]-a[3]) +','
                if (a[1]-a[3] <= 0):
                    value =  value + 'TRUE,'
                else:
                    value =  value + 'FALSE,'            
            else:
                value =  value + str(a[1]-round(a[3]/1.075,2)) +','
                if (a[1]-round(a[3]/1.075,2) <= 0):
                    value =  value + 'TRUE,'
                else:
                    value =  value + 'FALSE,' 
        elif (i==3):
            pass
        else:
            column =  column + i +','
            value = value +'\''+ a[i] +'\','
    column = column + 'fecha'
    value = value +'\'' + datetime.today().strftime('%m/%d/%Y') +'\''
    if d != None:
        column = column + ', notes'
        value = value + ',\'' + d + '\''
    sql_sintaxis = """INSERT INTO customer({}) VALUES({})""".format(column,value)
    cursorObj.execute(sql_sintaxis)
    con.commit()
    con.close()
    
def update_date(numB, a):
    con = sqlite3.connect(LINK_DATABASE)
    cursorObj = con.cursor()
    sql_sintaxis = """UPDATE customer SET """
    if (a[2] == False):
        if (a[1]-a[3] <= 0):
            sql_sintaxis += 'balance = ' + str(a[1]-a[3]) + ', pay_all = TRUE'
        else:
            sql_sintaxis += 'balance = ' + str(a[1]-a[3]) + ', pay_all = FALSE'
    else:
        if (a[1]-round(a[3]/1.075,2) <= 0):
            sql_sintaxis += 'balance = ' + str(a[1]-round(a[3]/1.075,2)) + ', pay_all = TRUE'
        else:
            sql_sintaxis += 'balance = ' + str(a[1]-round(a[3]/1.075,2)) + ', pay_all = FALSE'
    sql_sintaxis += ' where id =' + numB
    cursorObj.execute(sql_sintaxis)
    con.commit()
    con.close()

def parser_date(date,new_invoice):
    date_client = dict()
    list_client = ["name","last","phone","email","street","city","cp","boat","feet","vin"]
    work_contract = {1:False,2:False,3:False,4:False,5:False,6:False,7:False,8:False,9:False,10:False,
11:False,12:False,13:False,14:False,15:False,16:False,17:False,18:False,19:False,20:False,21:False,22:False}
    money = {1:0,2:True,3:2}
    TAX = 'TRUE'
    for i in date:
        if i in list_client:
            if date.get(i)!='':
                date_client[i] = date.get(i)
        elif i.split('_')[0] == 'check':
            work_contract[int(i.split('_')[1])] = True
        elif i == 'aditional':
            if date.get(i)!='':
                comment = date.get(i)
            else:
                comment = None
        else:
            if i == 'total':
                money[1] = float(date.get(i))
            elif i == 'cash':
                money[2] = False
                TAX = 'FALSE'
            elif i == 'deposito':
                money[3] = float(date.get(i))
    if new_invoice == True:
        a = get_number_invoice()
        insert_date(date_client,money,work_contract,comment)
    else:
        a = date.get('numero_invoice')
        update_date(date.get('numero_invoice'),money)
    insert_individual(a,money[3],TAX)
    date_client['address'] = '{},{},{}'.format(date_client['street'],date_client['city'],date_client['cp'])
    del date_client['street']
    del date_client['city']
    del date_client['cp']
    date_client['name'] = '{} {}'.format(date_client['name'],date_client['last'])
    del date_client['last']
    return date_client,work_contract,money,comment  

def find_datos(date):
    number = date["Invoice"]
    name = date["name"]
    con = sqlite3.connect(LINK_DATABASE)
    cursorObj = con.cursor()
    if number:
        sql_sintaxis = """SELECT * from customer where id = {}""".format(number)
    elif name:
        name = name.split(' ')
        if len(name) < 2:
            sql_sintaxis = """SELECT * from customer where name = '{}'""".format(name[0])
        else:
            sql_sintaxis = """SELECT * from customer where name = '{}' and last = '{}'""".format(name[0],name[1])
    else:
        return None
    cursorObj.execute(sql_sintaxis)  
    rows = cursorObj.fetchall()
    if rows:
        for row in rows:
            pass
        return list(row)
    else:
        return None

def find_invoice_no_canceled():
    rows = get_database_invoice()
    if rows:
        element = list()
        for row in rows:
            if row[17] != 'TRUE':
                element.append(row[0])
        return element
    else:
        return rows
    
app = Flask(__name__)

################### PRINCIPAL #######################################################
@app.route("/", methods=['GET', 'POST'])
def index():
    return """    <style>
        section{text-align: center;}
        #maintable{width: 80%; text-align: center;margin: auto 10%;}
        .mitabla{width: 100%; padding:20px;}
        .mitabla thead{background-color: gray;}
        .mitabla tfoot{background-color: antiquewhite;}
    </style>
<form>	
    <section>
        <div>
            <h1>Software update required</h1>
        </div>
		<p>Keeping your Python environment up-to-date is a vital part of the 
		development process, yet it's often the most overlooked due to cost, 
		time, and sometimes a general fear of what might break. However, 
		your favorite version of Python has a shelf-life.</p>
    </section>
</form>
    """

###############################################################################################################
    
if __name__ == "__main__":
    serve(app, host='0.0.0.0', port=8080, threads=1) #WAITRESS!