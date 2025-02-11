# Importing Libraries
from flask import Flask, render_template, request
import pandas as pd, datetime, mysql.connector, random
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# creating flask app
app = Flask(__name__)

# creating connection with database to extract :
initial_mydb = mysql.connector.connect(host="localhost",user="root",password="prateek",database="fyp")
mycursor = initial_mydb.cursor()

# surpasss sql safe mode to allow deletion and updation
sql = f"SET SQL_SAFE_UPDATES = 0;"
mycursor.execute(sql)

# 1) list of brands
sql = "SELECT DISTINCT(brand) FROM home_depot;"
mycursor.execute(sql)
rows = mycursor.fetchall()
brand_names=[]
for row in rows:
    brand_names.append(list(row)[0])
brand_names.sort(key=str.lower)

# 2) list of titles, their description, image, brand name and their respective url
sql = "SELECT title,description,images,brand,url FROM home_depot;"
mycursor.execute(sql)
rows = mycursor.fetchall()
all_titles=[]
description=[]
img=[]
all_brand=[]
all_url=[]
for row in rows:
    all_titles.append(list(row)[0])
    description.append(list(row)[1])
    img.append(list(row)[2].split("~")[0])
    all_brand.append(list(row)[3])
    all_url.append(list(row)[4])

# committing the current instance of DB connection
initial_mydb.commit()

# save product title into user's history
def save_history(userx,searched):
    mydb = mysql.connector.connect(host="localhost",user="root",password="prateek",database="fyp")
    mycursor = mydb.cursor()
    sql3 = f"SET SQL_SAFE_UPDATES = 0;"
    mycursor.execute(sql3)

    sql4 = f"""delete from {userx} where last_ordered="{searched}";"""
    mycursor.execute(sql4)

    sql = f"""INSERT INTO {userx} (last_ordered) VALUES (%s)"""
    val = [searched]
    mycursor.execute(sql, val)
    mydb.commit()

# view user's history
def view_history(userx):
    mydb = mysql.connector.connect(host="localhost",user="root",password="prateek",database="fyp")
    mycursor = mydb.cursor()
    sql = f"""SELECT last_ordered FROM {userx};"""
    mycursor.execute(sql)
    rows = mycursor.fetchall()
    last_ordered=[]
    for i in rows:
        last_ordered.append(list(i)[0])

    mydb.commit()
    return last_ordered

# adding user activity
def add_user_log(userx):
    mydb = mysql.connector.connect(host="localhost",user="root",password="prateek",database="fyp")
    mycursor = mydb.cursor()
    sql3 = f"SET SQL_SAFE_UPDATES = 0;"
    mycursor.execute(sql3)
    
    sql4 = f"""delete from userlogs where username="{userx}";"""
    mycursor.execute(sql4)

    sql2 = f"""INSERT INTO userlogs (logtime, username) VALUES (%s,%s)"""
    val = [datetime.datetime.now(),userx]
    mycursor.execute(sql2, val)
    mydb.commit()

# clear user history
def clear_history(userx):
    mydb = mysql.connector.connect(host="localhost",user="root",password="prateek",database="fyp")
    mycursor = mydb.cursor()
    sql3 = f"SET SQL_SAFE_UPDATES = 0;"
    mycursor.execute(sql3)
    
    sql4 = f"""delete from {userx};"""
    mycursor.execute(sql4)

    mydb.commit()

# return current logged in user
def current_user():
    mydb = mysql.connector.connect(host="localhost",user="root",password="prateek",database="fyp")
    mycursor = mydb.cursor()
    sql = f"""SELECT logtime, username FROM userlogs;"""
    mycursor.execute(sql)
    rows = mycursor.fetchall()
    current_user=[]
    current_user_time=[]
    for i in rows:
        current_user_time.append(list(i)[0])
        current_user.append(list(i)[1])
    mydb.commit()
    return [current_user[-1], current_user_time[-1]]

# return s_no wrt product title
def get_indice_of_title(title):
    mydb = mysql.connector.connect(host="localhost",user="root",password="prateek",database="fyp")
    mycursor = mydb.cursor()
    sql = f"""SELECT s_no FROM home_depot where title="{title}";"""
    mycursor.execute(sql)
    rows = mycursor.fetchall()
    id=[]
    for row in rows:
        id.append(list(row)[0])
    if id[0] in [0,1,2]:
        id[0]=id[0]
    elif id[0]>2225:
        id[0]=id[0]-2
    else:
        id[0]=id[0]-1
    mydb.commit()
    return id[0]

# It is used to transform a given text into a vector on the basis of the frequency (count) of each word that occurs in the entire text. This is helpful when we have multiple such texts, and we wish to convert each word in each text into vectors (for using in further text analysis)
# inhi ke basis bas count variable me entries aayenging taking usse baad me transform karenge based on need ( we are using description for that )
count = CountVectorizer(stop_words='english')

# kiske basis ham products ko chaatke recommend karenge
count_matrix = count.fit_transform(pd.Series(description))

# this function will return recommendated product's details based on input product title
def get_recommendations(title):
    # cosine similarity used to find similar products
    cosine_sim = cosine_similarity(count_matrix, count_matrix) 
    
    # extracting index no. to then used to display similar products's indices
    idx = get_indice_of_title(title)

    # similarity value wrt input title
    sim_scores = list(enumerate(cosine_sim[idx]))

    # sort in descending order
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)

    # return top [ 1 + 15 ] results including the searched item
    sim_scores = sim_scores[0:16]
    product_indices = [i[0] for i in sim_scores]
    
    mydb = mysql.connector.connect(host="localhost",user="root",password="prateek",database="fyp")
    mycursor = mydb.cursor()
    res_price=[]
    res_title=[]
    res_image=[]
    res_url=[]
    res_brand=[]
    sql = f"""SELECT title,price,url,images,brand FROM home_depot where title="{title}";"""
    mycursor.execute(sql)
    rows2 = mycursor.fetchall()
    for row in rows2:
        res_title.append(list(row)[0])
        res_price.append(list(row)[1])
        res_url.append(list(row)[2])
        res_image.append(list(row)[3].split("~")[0])
        res_brand.append(list(row)[4])
    for i in product_indices:
        sql = f"""SELECT title,price,url,images,brand FROM home_depot where s_no={i+1};"""
        mycursor.execute(sql)
        rows = mycursor.fetchall()
        for row in rows:
            res_title.append(list(row)[0])
            res_price.append(list(row)[1])
            res_url.append(list(row)[2])
            res_image.append(list(row)[3].split("~")[0])
            res_brand.append(list(row)[4])
    res_title.pop(1)
    res_price.pop(1)
    res_url.pop(1)
    res_image.pop(1)
    res_brand.pop(1)
    res_price=list(map(lambda x : float(x),res_price))
    mydb.commit()

    return [res_brand, res_title, res_price, res_image, res_url]

# return list of brand names, titles, images and url
def get_suggestions():
    return [all_brand, all_titles, img, all_url]

# defining statup route
@app.route('/')
def landing_page_to_search_page():
    return render_template('login.html')

# action for /login path request
@app.route('/login')
def login():
    return render_template('login.html')

# action for /search path request
@app.route('/search', methods=['GET', 'POST'])
def search():
    global user_name
    if request.method == 'POST':
        
        # grapping selected user's name
        user_name = request.form['user_name']
    history = view_history(user_name)
    sugs = get_suggestions()
    
    based_on_history_brand = []
    based_on_history_prod = []
    based_on_history_image = []
    based_on_history_url = []
    
    brand = []
    prod = []
    image = []
    url = []
    
    for i in range(8): # any 8 products
        z=random.randint(0,2400)
        y=random.randint(0,15)
        try:
            if((i in range(0,3)) and (len(history)>0) ):
                based_on_history_brand.append(get_recommendations(history[-i-1])[0][y])
                based_on_history_prod.append(get_recommendations(history[-i-1])[1][y])
                based_on_history_image.append(get_recommendations(history[-i-1])[3][y])
                based_on_history_url.append(get_recommendations(history[-i-1])[4][y])
        finally:
            pass

        brand.append(sugs[0][z])
        prod.append(sugs[1][z])
        image.append(sugs[2][z])
        url.append(sugs[3][z])

    # note user's arrival
    add_user_log(user_name)        

    # for showing in search bar
    if current_user()[0] == "prateek":
        last_search=view_history("prateek")
    elif current_user()[0] == "aadarsh":
        last_search=view_history("aadarsh")
    elif current_user()[0] == "guest_user":
        last_search=view_history("guest_user")

    return render_template('home.html', based_on_history=[based_on_history_brand,based_on_history_prod,based_on_history_image,based_on_history_url], len_based_on_history=len(based_on_history_brand), url=url, brand=brand , prod=prod, image=image, user=current_user()[0], last_search=last_search)

# action for /home path request
# for activating navigation on brand logo
@app.route('/home')
def home():
    global user_name
    history = view_history(current_user()[0])
    sugs = get_suggestions()
    
    based_on_history_brand = []
    based_on_history_prod = []
    based_on_history_image = []
    based_on_history_url = []
    
    brand = []
    prod = []
    image = []
    url = []
    
    for i in range(8): # any 8 products
        z=random.randint(0,2400)
        y=random.randint(0,15)
        try:
            if((i in range(0,3)) and (len(history)>2) ):
                based_on_history_brand.append(get_recommendations(history[-i-1])[0][y])
                based_on_history_prod.append(get_recommendations(history[-i-1])[1][y])
                based_on_history_image.append(get_recommendations(history[-i-1])[3][y])
                based_on_history_url.append(get_recommendations(history[-i-1])[4][y])
        finally:
            pass

        brand.append(sugs[0][z])
        prod.append(sugs[1][z])
        image.append(sugs[2][z])
        url.append(sugs[3][z])

    # for showing in search bar
    if current_user()[0] == "prateek":
        last_search=view_history("prateek")
    elif current_user()[0] == "aadarsh":
        last_search=view_history("aadarsh")
    elif current_user()[0] == "guest_user":
        last_search=view_history("guest_user")

    return render_template('home.html', based_on_history=[based_on_history_brand,based_on_history_prod,based_on_history_image,based_on_history_url], len_based_on_history=len(based_on_history_brand), url=url, brand=brand , prod=prod, image=image, user=current_user()[0], last_search=last_search)

# action for /index path request
@app.route('/index', methods=['GET', 'POST'])
def index():
    suggestions = get_suggestions()
    return render_template('home.html',suggestions=suggestions)

# action for /shop_by_brand path request
@app.route('/shop_by_brand')
def shop_by_brand():
    
    # for showing in search bar
    if current_user()[0] == "prateek":
        last_search=view_history("prateek")
    elif current_user()[0] == "aadarsh":
        last_search=view_history("aadarsh")
    elif current_user()[0] == "guest_user":
        last_search=view_history("guest_user")

    # for managing the length of list ( for for loop in jinja code)
    total_brands = len(brand_names)

    return render_template('shop_by_brand.html',total_brands=total_brands,brand_names=brand_names, last_search=last_search)

# action for /shopping_from_brand path request
@app.route('/shopping_from_brand', methods=['GET', 'POST'])
def shopping_from_brand():
    if request.method == 'POST':

        # grapping the selected brand name
        selected_brand_name = request.form['brand_name']
        mydb = mysql.connector.connect(host="localhost",user="root",password="prateek",database="fyp")
        mycursor = mydb.cursor()

        sql = f"""SELECT brand,title,price,url,images FROM home_depot where brand="{selected_brand_name}";"""
        mycursor.execute(sql)
        rows = mycursor.fetchall()
        brand=[]
        title=[]
        price=[]
        url=[]
        img=[]
        for row in rows:
            brand.append(list(row)[0])
            title.append(list(row)[1])
            price.append(list(row)[2])
            url.append(list(row)[3])
            img.append(list(row)[4].split("~")[0])
        price=list(map(lambda x : float(x),price))

        mydb.commit()

    # for showing in search bar
    if current_user()[0] == "prateek":
        last_search=view_history("prateek")
    elif current_user()[0] == "aadarsh":
        last_search=view_history("aadarsh")
    elif current_user()[0] == "guest_user":
        last_search=view_history("guest_user")
    
    return render_template('result.html', prod_name=f"Brand: {selected_brand_name}", brand=brand, title=title, price=price, url=url, img=img, user=current_user()[0], last_search=last_search)

# action for /about_user path request
@app.route('/about_user', methods=['GET', 'POST'])

# for showing user profile
def about_user():

    # for showing in search bar
    if current_user()[0] == "prateek":
        last_search=view_history("prateek")
    if current_user()[0] == "aadarsh":
        last_search=view_history("aadarsh")
    if current_user()[0] == "guest_user":
        last_search=view_history("guest_user")
    
    return render_template('user.html', user=current_user()[0], last_search=last_search, login_time=current_user()[1])

# action for /admin path request
@app.route('/admin', methods=['GET', 'POST'])

# showing admin dashboard
def admin():
    if request.method == 'GET':
        return render_template('login.html')
    if request.method == 'POST':
        password = request.form['admin_password']
        
        # validating admin password
        if password=="finalyearproject":
            mydb = mysql.connector.connect(host="localhost",user="root",password="prateek",database="fyp")
            mycursor = mydb.cursor()
            sql = f"""SELECT logtime,username FROM userlogs;"""
            mycursor.execute(sql)
            rows = mycursor.fetchall()
            users=[]
            login_time=[]
            for row in rows:
                login_time.append(list(row)[0])
                users.append(list(row)[1])
            users=users[::-1]
            login_time=login_time[::-1]
            return render_template('admin_home.html',total_users=len(users),users=users,login_time=login_time)
        else:
            m="Wrong Password Entered"
            return render_template('login.html',message=m)

# action for /user_details path request
@app.route('/user_details', methods=['GET', 'POST'])

# display customer profile
def user_details():
    if request.method == 'GET':
        return render_template('admin_user_details.html')
    if request.method == 'POST':

        # user selected by admin
        user = request.form['user_profile']

        # for showing in search bar
        if user == "prateek":
            last_search=view_history("prateek")
        if user == "aadarsh":
            last_search=view_history("aadarsh")
        if user == "guest_user":
            last_search=view_history("guest_user")

        return render_template('admin_user_details.html',last_search=last_search, user=user)

# action for /result path request
@app.route('/result', methods=['GET', 'POST'])
def result():
    if request.method == 'GET':
        return render_template('home.html')
    if request.method == 'POST':

        # grapping the searched product title
        prod_name = request.form['product_name']

        # for showing in search bar
        if current_user()[0] == "prateek":
            last_search=view_history("prateek")
        elif current_user()[0] == "aadarsh":
            last_search=view_history("aadarsh")
        elif current_user()[0] == "guest_user":
            last_search=view_history("guest_user")

        if prod_name not in all_titles:
            return render_template('error.html', last_search=last_search)
        
        if prod_name in all_titles:

            # save searches in user'search history
            if current_user()[0] == "prateek":
                if len(view_history("prateek"))==0:
                    save_history("prateek", prod_name)
                # to eliminate redundacy i.e. showing a searched product multiple times
                elif view_history("prateek")[-1]!=prod_name:
                    save_history("prateek", prod_name)
            if current_user()[0] == "aadarsh":
                if len(view_history("aadarsh"))==0:
                    save_history("aadarsh", prod_name)
                # to eliminate redundacy i.e. showing a searched product multiple times
                elif view_history("aadarsh")[-1]!=prod_name:
                    save_history("aadarsh", prod_name)
            if current_user()[0] == "guest_user":
                if len(view_history("guest_user"))==0:
                    save_history("guest_user", prod_name)
                # to eliminate redundacy i.e. showing a searched product multiple times
                elif view_history("guest_user")[-1]!=prod_name:
                    save_history("guest_user", prod_name)
            result_final = get_recommendations(prod_name)

            return render_template('result.html', prod_name=prod_name, brand=result_final[0], title=result_final[1], price=result_final[2], img=result_final[3], url=result_final[4], user=current_user()[0], last_search=last_search)

# action for /delete path request
@app.route('/delete', methods=['GET', 'POST'])

# delete user history
def delete():
    if request.method == 'POST':
        
        # grapping user for whom we want history to be deleted
        user_name = request.form['user_name']
        
        # clearing history
        if user_name == "prateek":
            clear_history("prateek")
        elif user_name == "aadarsh":
            clear_history("aadarsh")
        elif user_name == "guest_user":
            clear_history("guest_user")
        
        mydb = mysql.connector.connect(host="localhost",user="root",password="prateek",database="fyp")
        mycursor = mydb.cursor()
        sql = f"""SELECT logtime,username FROM userlogs;"""
        mycursor.execute(sql)
        rows = mycursor.fetchall()
        users=[]
        login_time=[]
        for row in rows:
            login_time.append(list(row)[0])
            users.append(list(row)[1])

        return render_template('admin_home.html',total_users=len(users),users=users,login_time=login_time,user_history_deleted=user_name, deletion_done=1)

if __name__ == "__main__":

    # debug true helps us to resolve and read the error/bugs on the web screen
    app.run(debug=True)