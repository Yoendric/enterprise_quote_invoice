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
    print(element)
    print(date)
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

def get_data_database():
    rows = get_database_invoice()
    if rows:
        pay = 0
        no_pay = 0
        total_mon = 0
        total_pen = 0
        msg_no_cob = list()
        msg = list()
        elementAll = len(rows)
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
        return elementAll,no_pay,pay,no_pay/(pay+no_pay)*100,total_mon,total_pen,msg,msg_no_cob
    else:        
        return 0,0,0,0,0,0,None,None

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
            elif i == 'deposito':
                money[3] = float(date.get(i))
    if new_invoice == True:
        insert_date(date_client,money,work_contract,comment)
    else:
        update_date(date.get('numero_invoice'),money)
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
    return render_template("index.html")
#####################################################################################
################### QUOTE ###########################################################
@app.route("/estimation", methods=['GET', 'POST'])
def estimation():
    rows = fecth_raw()
    if request.method == 'GET':  
        return render_template("estimation.html", materiales = rows)
    if request.method == 'POST':
        adds = remove_elemt_request(request.form)
        name = request.form.get('fname')
        data_expande = list()
        for i in adds:
            data_expande.append(data_raw(i)[0]+tuple([int(adds[i])]))
        if request.form.get('raw'):
            filter_mat = [data_raw(request.form.get('raw'))[0]+tuple([None])]
            if request.form.get('raw') in adds:
                #pag.alert(text="Item already selected", title="Warning")
                pass
            else:
                data_expande.append(filter_mat[0]) 
        total = 0
        for i in data_expande:
            if i[4]:
                total += i[3]*i[4]
            else: 
                total += i[3]             
        return render_template("estimation.html", materiales = rows, nombre=name, add_element = data_expande, total = total)

@app.route('/quote', methods=['GET','POST'])
def quote(): 
    if request.form.get('fname'):
        pdf=dict(request.form)
        if 'raw' in pdf:
            del pdf['raw']
        rows = company_database()
        company_data = [rows[0][1],rows[0][2],rows[0][4]+', '+rows[0][5]+' '+rows[0][3],rows[0][6],rows[0][7]]
        generate_quote_pdf(pdf,data_raw,company_data)
        return render_template("quote.html",nombre=request.form.get('fname'))
    else:
        return """{"Error":"NO Name in yo quote"}"""
        
@app.route('/materials', methods=['GET','POST'])
def materials():
    if request.method == 'POST':
        if request.form.get('submit_button'):
            if request.form['submit_button'] == 'add':
                if (request.form.get('name_item') and request.form.get('unit_item') and request.form.get('cost_item')):
                    sql_string = """INSERT INTO materials VALUES ({0},"{1}","{2}",{3})""".format(new_id(),request.form.get('name_item'),
                                      request.form.get('unit_item'),request.form.get('cost_item'))  
                    insert_materials(sql_string)
                    sort_DB()                    
            if request.form['submit_button'] == 'delete':                    
                if request.form.get('delete'): 
                    if 'confirmacion' in dict(request.form): 
                        delete_materials(request.form.get('delete'))
                        sort_DB()
            if  request.form['submit_button'] == 'update': 
                if request.form.get('update'): 
                    if 'confirmacion_update' in dict(request.form):  
                        update = data_raw(request.form.get('update'))
                        return render_template("database.html", row=update, page_principal = False)                        
                else:
                    if (request.form.get('id') and request.form.get('name_item') and request.form.get('unit_item') and request.form.get('cost_item')):
                        sql_string =""" UPDATE materials SET element="{}",medida="{}",prize={} WHERE id={}""".format(request.form.get('name_item'),
                                                  request.form.get('unit_item'),request.form.get('cost_item'),request.form.get('id')) 
                        insert_materials(sql_string)  
                        sort_DB()                        
    rows = fecth_raw()
    return render_template("database.html", row=rows, page_principal = True)
################################################################################################################
########################### COMPANY DATE #######################################################################
@app.route('/company', methods=['GET','POST'])
def company(): 
    rows = None
    if (request.method == 'POST'):
        sql_string = """UPDATE company SET name="{}",address="{}",zipcode="{}",city="{}",estado="{}",phone="{}",email="{}" WHERE id=1""".format(request.form.get('name_company'),
                           request.form.get('address_company'),request.form.get('zip'),request.form.get('city_company'),request.form.get('estado'),
                           "+1"+request.form.get('phone'),request.form.get('email'))
        insert_materials(sql_string)
    rows = company_database()
    return render_template("company.html", data = rows[0])

###############################################################################################################
########################### INVOICE ###########################################################################
@app.route('/find', methods=['GET','POST'])    
def find():
    return render_template("find.html")
    
@app.route('/dashboard')    
def dashboard():
    a,b,c,d,e,g,msg,msg_no_cob = get_data_database()
    return render_template("datos.html",total=a,pending=b,complete=c,porc=round(d,2),tot_mon=e,pend_mon=g,msg_no_cob=msg_no_cob,msg=msg)

@app.route("/invoice", methods=['GET','POST'])
def invoice():
    if request.method == 'GET':
        return render_template("invoice.html")
    if request.method == 'POST':
        if request.form:
            date_fact = find_datos(request.form)
            if date_fact:
                date_fact = ['' if x==None else x for x in date_fact]
                if date_fact[15] == 1:
                    texto="Invoices Payment Complete"
                    return render_template("mostrar.html",text=texto, nombre=request.form.get('name'), number = request.form.get('Invoice').zfill(4))
                check_his = list()
                for i in list(date_fact[11]):
                    if i == '1':
                        check_his.append('checked')
                    else:
                        check_his.append('')
                return render_template("refacturar.html", number = date_fact[0],name=date_fact[1],
                last=date_fact[2],phone=date_fact[3],email=date_fact[4],
                street=date_fact[5],city=date_fact[6],cp=date_fact[7],
                boat=date_fact[8],feet=date_fact[9],vin=date_fact[10],
                comment=date_fact[12],pending=date_fact[14],check=check_his)
            else:
                texto="Invoices no Found or not Exist"
                return render_template("mostrar.html",text=texto, nombre=request.form.get('name'), number = request.form.get('Invoice').zfill(4))
        else:
            return render_template("invoice.html")

@app.route('/procesar', methods=['POST'])
def procesar():
    number_invoice = request.form.get("numero_invoice")
    if number_invoice == None:
        number_invoice = get_number_invoice()
        new_invoice = True
    else:
        number_invoice = int(number_invoice)
        new_invoice = False
    date_client,work_contract,money,comment = parser_date(request.form, new_invoice)
    if comment:
        aditional = split_text_note(comment)
    else:
        aditional = comment
    rows = company_database()
    company_data = [rows[0][1],rows[0][2],rows[0][4]+', '+rows[0][5]+' '+rows[0][3],rows[0][6],rows[0][7]]
    generate_invoice_pdf(number_invoice,date_client,work_contract,aditional,money,company_data)
    #webbrowser.open_new(r'file://C:\Users\DELL\Desktop\Eduyn\Invoice\flask_invoice\invoice\invoice_{}_fecha_{}.pdf'.format(str(number_invoice).zfill(4),datetime.today().strftime('%m_%d_%Y_%H_%M')))
    nombre = request.form.get("name") +' '+request.form.get("last")
    texto = "Invoices Generated and Date Client Save OK"
    return render_template("mostrar.html", text =texto, nombre=nombre, number=str(number_invoice).zfill(4))     

@app.route('/delete', methods=['GET','POST'])
def delete():
    invoices = find_invoice_no_canceled() 
    mensaje = None    
    if request.method == 'POST':
        if request.form.get('cancel'): 
            sql_sintaxis = """UPDATE customer SET cancel = 'TRUE' where id = {}""".format(request.form.get('cancel'))  
            insert_materials(sql_sintaxis)            
            mensaje = "Successful invoice cancellation # "+str(request.form.get('cancel'))
            invoices = find_invoice_no_canceled() 
    return render_template("delete.html", msg = mensaje, invoices = invoices) 
###############################################################################################################
    
if __name__ == "__main__":
    app.run(debug=True)
    #serve(app, host='0.0.0.0', port=8080, threads=1) #WAITRESS!