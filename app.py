from flask import Flask,jsonify,render_template,g,redirect,request,url_for,Response
from flask_mobility import Mobility
from io import StringIO
from collections.abc import Mapping, Sequence
from typing import Any
from flask_wtf import FlaskForm
from wtforms import Form #TextField,StringField,TextAreaField,ValidationError
#from wtforms.validators import Required,Length

import sqlite3
import pandas as pd
import numpy
import csv

DATABASE="StApp.db"
from flask_login import UserMixin,LoginManager,login_required,login_user,logout_user,login_required,current_user
import os
from werkzeug.security import check_password_hash, generate_password_hash

#app = Flask(__name__)
app = Flask(__name__, static_folder='./templates/image')
app.secret_key = os.urandom(24)
login_manager = LoginManager()
login_manager.init_app(app)
app.json.ensure_ascii = False

class User(UserMixin):
    def __init__(self,roster):
        self.id = roster
##ログイン
@login_manager.user_loader
def load_user(roster):
    return User(roster)

@login_manager.unauthorized_handler
def unauthorized():
    return redirect('/login')

@app.route("/logout",methods=['GET'])
def logout():
    logout_user()
    return redirect('/login')

@app.route("/signup",methods=['GET','POST'])
def signup():
    error_message =''
    if request.method == 'POST':
       roster = request.form.get('roster')
       password= request.form.get('password')
       name= request.form.get('name')
       ##pass_hash = generate_password_hash(password )  パスワード暗号化
       #pass_hash = generate_password_hash(password ,method = 'sha256')

       db = get_db()
       user_cheack = get_db().execute("select roster from user where roster=?",[roster,]).fetchall()
       if not user_cheack:       
            db.execute("insert into user (roster,name,password) values(?,?,?)",[roster,name,password])
            ##[roster,pass_hash]　パスワード暗号化
            db.commit()
            return redirect('/login')
       else:
           error_message='入力されたユーザーIDはすでに利用されています。'
    
    return render_template('signup.html',error_message=error_message)

@app.route("/login",methods=['GET','POST'])
def login():
    error_message =''
    roster=''

    if request.method == 'POST':
       roster = request.form.get('roster')
       password= request.form.get('password')
       #ロインチェック  
       user_data = get_db().execute(
           "select password from user where roster=?",[roster,]).fetchone()
       get_db().commit()
       if user_data is not None:
           ##if check_password_hash(user_data[0],password): 暗号化チェック
               roster = User(roster)
               login_user(roster)
               ##return redirect('/')
               return redirect('/store')
               ##return render_template('store.html')
          
       error_message = '入力されたIDもしくはパスワードが誤っています。'

    return render_template('login.html',roster=roster,error_message=error_message)

#店舗入力
@app.route("/store",methods=['GET','POST'])
@login_required
def store():
    if request.method == 'POST':
        #画面からの登録情報取得
        date = request.form.get('date')
        storeNo = request.form.get('storeNo')
        db = get_db()
        post = get_db().execute(
            "select id,kigyo,store from storeMst where storeNo=?",(storeNo,)
        ).fetchone()
        db.commit()
        return render_template ('storepost.html',date=date,storeNo=storeNo,post=post)
  
    ##確認後登録 追加
    return render_template('store.html')
    
#店舗入力確認 未使用
#@app.route("/storepost",methods=['GET','POST'])
#@login_required
#料金算出項目を登録
#def storepost():
    #if request.method == 'GET':
       #date = request.form.get('date')
       #storeNo = request.form.get('storeNo')
       #kigyo = request.form.get('kigyo')
       #store = request.form.get('store')
       #db = get_db()
       #post = db.execute("insert into storeDat (date,storeNo,kigyo,store) values(?,?,?,?)",[date,storeNo,kigyo,store])
       #db.commit()
       #return render_template ('chargein.html')  
    #return render_template('chargein.html')
     
@app.route("/<date>/<storeNo>/<kigyo>/<store>/charge",methods=['GET','POST'])
@login_required
def charge(date,storeNo,kigyo,store):
    if request.method == 'POST':
        foL = request.form.get('foL')
        siL = request.form.get('siL')
        oricon = request.form.get('oricon')
        cas = request.form.get('cas')
        sake = request.form.get('sake')
        db = get_db()
        ##確認後登録
        db.execute("insert into storeDat (date,storeNo,kigyo,store,foL,siL,oricon,cas,sake) values(?,?,?,?,?,?,?,?,?)"
                   ,[date,storeNo,kigyo,store,foL,siL,oricon,cas,sake])
        #DBに登録した情報(最新ID)を取得 
        post = db.execute("select id,date,storeNo,kigyo,store from storeDat where id = (SELECT MAX(id) FROM storeDat)" ).fetchone()
        db.commit()
        #return render_template ('chargein.html',date=date,storeNo=storeNo,kigyo=kigyo,store=store,post=post)  オリコンケース入力へ
        return render_template ('kagoin.html',date=date,storeNo=storeNo,kigyo=kigyo,store=store,post=post)
    
##料金算出入力
@app.route("/<date>/<storeNo>/<kigyo>/<store>/chargein",methods=['GET','POST'])
@login_required
def chargein(date,storeNo,kigyo,store):
    if request.method == 'POST':
        foL = request.form.get('foL')
        siL = request.form.get('siL')
        oricon = request.form.get('oricon')
        cas = request.form.get('cas')
        sake = request.form.get('sake')
        db = get_db()
        ##DBへ登録
        db.execute("insert into storeDat (date,storeNo,kigyo,store,foL,siL,oricon,cas,sake) values(?,?,?,?,?,?,?,?,?)"
                   ,[date,storeNo,kigyo,store,foL,siL,oricon,cas,sake])
        #DBに登録した情報(最新ID)を取得 
        post = db.execute("select id,date,storeNo,kigyo,store from storeDat where id = (SELECT MAX(id) FROM storeDat)" ).fetchone()
        db.commit()
        return render_template ('kagoin.html',date=date,storeNo=storeNo,kigyo=kigyo,store=store,post=post)
    
    return render_template('kagoin.html',date=date,storeNo=storeNo,kigyo=kigyo,store=store)

##カゴ入力
@app.route("/<id>/kagoin",methods=['GET','POST'])
@login_required
def kagoin(id):
    if request.method == 'POST':
        #画面からの登録情報取得
        Oric = request.form.get('Oric')
        Tape = request.form.get('Tape')
        cae = request.form.get('cae')
        Total = (int(Oric)*int(Tape))+int(cae)
        db = get_db()
        post = get_db().execute("select date,storeNo,kigyo,store from storeDat where id=?",(id,)).fetchone()
        db.execute("update storeDat set Oric=?,Tape=?,cae=?,Total=? where id=?",[Oric,Tape,cae,Total,id])
        db.commit()
        return render_template('kintai.html',id=id,post=post)
    
    return render_template('error.html')

#勤怠入力
@app.route("/<id>/<date>/kintai", methods=['POST','GET'])
#@login_required
def kintai(id,date):
    if request.method == 'POST':
 #表1から取得
        roster = request.form.get('roster1')
        if roster == "": 
            return render_template('kintaierror.html', id=id)
        leader = request.form.get('leader1')
        storein = request.form.get('storein1')
        storeout = request.form.get('storeout1')
        kyus = request.form.get('kyus1')
        kyue = request.form.get('kyue1')
        kotue = request.form.get('kotue1')
        if kotue == "":
            kotue = 0
        kotuk = request.form.get('kotuk1')
        if kotuk == "":
            kotuk = 0
        else:
            kotuk = int(kotuk) * 80
        biko = request.form.get('biko1')      
        db = get_db()
        #idと紐付けて実績データ(storeDat)からデータ取得
        post = db.execute("select date,storeNo,kigyo,store from storeDat where id=?",(id,)).fetchone()
        db.execute("insert into kintai (datid,roster,date,leader,storein,storeout,kyus,kyue,kotue,kotuk,biko) values(?,?,?,?,?,?,?,?,?,?,?)",[id,roster,date,leader,storein,storeout,kyus,kyue,kotue,kotuk,biko]) 
        #社員ﾏｽﾀ・実績・勤怠のデータ結合してIDを基にデータ取得
        kintai_list = db.execute("SELECT * FROM kintai JOIN user ON kintai.roster = user.roster JOIN storeDat ON kintai.datid = storeDat.id WHERE kintai.datid=?",(id,)) 
        db.commit()

 #表2から取得
        roster = request.form.get('roster2')
        if roster =="":
            pass
        else: 
            leader = request.form.get('leader2')
            storein = request.form.get('storein2')
            storeout = request.form.get('storeout2')
            kyus = request.form.get('kyus2')
            kyue = request.form.get('kyue2')
            kotue = request.form.get('kotue2')
            if kotue =="":
                kotue = 0
            kotuk = request.form.get('kotuk2')
            if kotuk == "":
                kotuk = 0
            else:
                kotuk = int(kotuk) * 80
            biko = request.form.get('biko2')
            db = get_db()
            #idと紐付けて実績データ(storeDat)からデータ取得
            post = db.execute("select date,storeNo,kigyo,store from storeDat where id=?",(id,)).fetchone()
            db.execute("insert into kintai (datid,roster,date,leader,storein,storeout,kyus,kyue,kotue,kotuk,biko) values(?,?,?,?,?,?,?,?,?,?,?)",[id,roster,date,leader,storein,storeout,kyus,kyue,kotue,kotuk,biko]) 
            #社員ﾏｽﾀ・実績・勤怠のデータ結合してIDを基にデータ取得
            kintai_list = db.execute("SELECT * FROM kintai JOIN user ON kintai.roster = user.roster JOIN storeDat ON kintai.datid = storeDat.id WHERE kintai.datid=?",(id,)) 
            db.commit()

 #表3から取得
        roster = request.form.get('roster3')
        if roster =="":
            pass
        else:
            leader = request.form.get('leader3')
            storein = request.form.get('storein3')
            storeout = request.form.get('storeout3')
            kyus = request.form.get('kyus3')
            kyue = request.form.get('kyue3')
            kotue = request.form.get('kotue3')
            if kotue == "":
                kotue = 0
            kotuk = request.form.get('kotuk3')
            if kotuk == "":
                kotuk = 0
            else:
                kotuk = int(kotuk) * 80
            biko = request.form.get('biko3')
            db = get_db()
            #idと紐付けて実績データ(storeDat)からデータ取得
            post = db.execute("select date,storeNo,kigyo,store from storeDat where id=?",(id,)).fetchone()
            db.execute("insert into kintai (datid,roster,date,leader,storein,storeout,kyus,kyue,kotue,kotuk,biko) values(?,?,?,?,?,?,?,?,?,?,?)",[id,roster,date,leader,storein,storeout,kyus,kyue,kotue,kotuk,biko]) 
            #社員ﾏｽﾀ・実績・勤怠のデータ結合してIDを基にデータ取得
            kintai_list = db.execute("SELECT * FROM kintai JOIN user ON kintai.roster = user.roster JOIN storeDat ON kintai.datid = storeDat.id WHERE kintai.datid=?",(id,)) 
            db.commit()

    #表4から取得
        roster = request.form.get('roster4')
        if roster =="":
            pass
        else:
            leader = request.form.get('leader4')
            storein = request.form.get('storein4')
            storeout = request.form.get('storeout4')
            kyus = request.form.get('kyus4')
            kyue = request.form.get('kyue4')
            kotue = request.form.get('kotue4')
            if kotue =="":
                kotue = 0
            kotuk = request.form.get('kotuk4')
            if kotuk == "":
                kotuk = 0
            else:
                kotuk = int(kotuk) * 80
            biko = request.form.get('biko4')
            db = get_db()
            #idと紐付けて実績データ(storeDat)からデータ取得
            post = db.execute("select date,storeNo,kigyo,store from storeDat where id=?",(id,)).fetchone()
            db.execute("insert into kintai (datid,roster,date,leader,storein,storeout,kyus,kyue,kotue,kotuk,biko) values(?,?,?,?,?,?,?,?,?,?,?)",[id,roster,date,leader,storein,storeout,kyus,kyue,kotue,kotuk,biko]) 
            #社員ﾏｽﾀ・実績・勤怠のデータ結合してIDを基にデータ取得
            kintai_list = db.execute("SELECT * FROM kintai JOIN user ON kintai.roster = user.roster JOIN storeDat ON kintai.datid = storeDat.id WHERE kintai.datid=?",(id,)) 
            db.commit()

    #表5から取得
        roster = request.form.get('roster5')
        if roster =="":
            pass
        else:
            leader = request.form.get('leader5')
            storein = request.form.get('storein5')
            storeout = request.form.get('storeout5')
            kyus = request.form.get('kyus5')
            kyue = request.form.get('kyue5')
            kotue = request.form.get('kotue5')
            if kotue =="":
                kotue = 0
            kotuk = request.form.get('kotuk5')
            if kotuk == "":
                kotuk = 0
            else:
                kotuk = int(kotuk)*80
            biko = request.form.get('biko5')

            db = get_db()
            #idと紐付けて実績データ(storeDat)からデータ取得
            post = db.execute("select date,storeNo,kigyo,store from storeDat where id=?",(id,)).fetchone()
            db.execute("insert into kintai (datid,roster,date,leader,storein,storeout,kyus,kyue,kotue,kotuk,biko) values(?,?,?,?,?,?,?,?,?,?,?)",[id,roster,date,leader,storein,storeout,kyus,kyue,kotue,kotuk,biko]) 
            #社員ﾏｽﾀ・実績・勤怠のデータ結合してIDを基にデータ取得
            kintai_list = db.execute("SELECT * FROM kintai JOIN user ON kintai.roster = user.roster JOIN storeDat ON kintai.datid = storeDat.id WHERE kintai.datid=?",(id,)) 
            db.commit()


        if kintai_list is None:
            return render_template('kintaierror.html', id=id)
        else:
            return render_template('kintaimain.html', id=id,post=post,kintai_list=kintai_list)

#勤怠未入力エラー
@app.route("/<id>/kintaierror", methods=['POST','GET'])
@login_required
def kintaierror(id):
    if request.method == 'GET':
        db = get_db()
        post = get_db().execute("select date,storeNo,kigyo,store from storeDat where id=?",(id,)).fetchone()
        db.commit()
        return render_template('kintai.html',id=id,post=post)

#勤怠未入力戻り
@app.route("/<id>/kintaireturn", methods=['POST','GET'])
@login_required
def kintaireturn(id):
    if request.method == 'GET':
        db = get_db()
        post = get_db().execute("select date,storeNo,kigyo,store from storeDat where id=?",(id,)).fetchone()
        db.commit()
        return render_template('kintai.html',id=id,post=post)

#勤怠確認  →CSVファイル出力
@app.route("/<id>/kintaimain", methods=['POST','GET'])
#@login_required
def kintaimain(id):
    conn = sqlite3.connect(DATABASE)
    if request.method == 'POST':
        #pd.DataFrame()   pandasを使用してCSV書き込み　strat   ※pd.read_sql_query で上手くいかない
        #df = pd.DataFrame()
        #conn = sqlite3.connect('StApp.db')
        #cursor = conn.cursor()
        #df = pd.read_sql_query("SELECT kintai.date,storeNo,kigyo,store,total,user.roster,storein,storeout,kyus,kyue,kotue,kotuk,biko FROM kintai JOIN user ON kintai.roster = user.roster JOIN storeDat ON kintai.datid = storeDat.id WHERE kintai.datid=?",(id,),conn) 
        #df = pd.read_sql_query("SELECT kintai.date,user.roster,datid,storeNo,kigyo FROM kintai JOIN user ON kintai.roster = user.roster JOIN storeDat ON kintai.datid = storeDat.id WHERE kintai.datid=?" (id),conn) 
        #df = pd.read_sql_query("SELECT * FROM kintai JOIN user ON kintai.roster = user.roster JOIN storeDat ON kintai.datid = storeDat.id WHERE kintai.datid=?",(id,),conn)
        #conn.close
        #df.to_csv('./static/data/sample.csv')   pandasを使用してCSV書き込み　end

        db = get_db()
        #kintai_list = db.execute("SELECT * FROM kintai JOIN user ON kintai.roster = user.roster JOIN storeDat ON kintai.datid = storeDat.id WHERE kintai.datid=?",(id,)) 
        #kintai_list = db.execute("SELECT  kintai.date,storeNo,kigyo,store,total,user.roster,storein,storeout,kyus,kyue,kotue,kotuk,biko FROM kintai JOIN user ON kintai.roster = user.roster JOIN storeDat ON kintai.datid = storeDat.id WHERE kintai.datid=?",(id,)) 
        #store_list = db.execute("SELECT date,storecd,kigyo,store,oric,tape,cae,total FROM storeDat where=?",(id,))
        store_list = db.execute("select * from storeDat where id=?",(id,)).fetchone()
        kintai_list = db.execute("SELECT kintai.datid,kintai.roster,kintai.date,leader,storein,storeout,kyus,kyue,kotue,kotuk,biko FROM kintai JOIN user ON kintai.roster = user.roster JOIN storeDat ON kintai.datid = storeDat.id WHERE kintai.datid=?",(id,)) 
        db.commit()
        with open('//landisk01/広場/StKintaiApp_Fold/sample.csv', 'w', newline='', encoding="utf-8") as f:
            #'//landisk01/広場/StKintaiApp_Fold/sample.csv'  テスト広場
            #./static/data/sample.csv テストローカルフォルダ

            writer = csv.writer(f)
            writer.writerow(['date','storeNo','kigyo','store','total','roster','storein','storeout','kyus','kyue','kotue','kotuk','biko'])
            writer.writerow(store_list)
            writer.writerows(kintai_list)

        return render_template('upload.html')

#カメラ起動  
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    # URLでhttp://127.0.0.1:5000/uploadを指定したときはGETリクエストとなるのでこちらを使用する
    if request.method == 'GET':
        return render_template('upload.html')
    # formでsubmitボタンが押されるとPOSTリクエストとなるのでこっち
    elif request.method == 'POST':
         file = request.files['photo_data']
         #file.save(os.path.join('./static/photo_data', file.filename))
         file.save(os.path.join('//landisk01/広場/StKintaiApp_Fold', file.filename))  #テストで広場に保存
         return redirect(url_for('uploaded_file', filename=file.filename))
    
    return render_template ('upload.html')

#写真保存 
@app.route('/uploaded_file/<string:filename>')
def uploaded_file(filename):
    return render_template('uploaded_file.html', filename=filename)
       
@app.route("/")
@login_required
def top():
    storedat_list = get_db().execute("select * from storeDat").fetchall()
    kintai_list = get_db().execute("select * from kintai").fetchall()
    return render_template('index.html',storedat_list=storedat_list, kintai_list=kintai_list)

@app.route("/regist",methods=['GET','POST'])
@login_required
def regist():
    if request.method == 'POST':
        #画面からの登録情報取得
        title = request.form.get('title')
        body = request.form.get('body')
        db = get_db()
        db.execute("insert into storeDat (title,body) values(?,?)",[title,body])
        db.commit()
        return redirect('/')
    return render_template('regist.html')

#修正
@app.route("/<id>/edit",methods=['GET','POST'])
@login_required
def edit(id):
    if request.method == 'POST':
        #画面からの登録情報取得
        title = request.form.get('title')
        body = request.form.get('body')
        db = get_db()
        db.execute("update memo set title=?,body=? where id=?",[title,body,id])
        db.commit()
        return redirect('/')
    
    post = get_db().execute("select id,title,body from memo where id=?",(id,)).fetchone()
    return render_template('edit.html',post=post)

#勤怠入力　修正　
@app.route("/<id>/<Unum>/editk",methods=['GET','POST'])
@login_required
def editk(id,Unum):
    if request.method == 'POST':
        #画面からの登録情報取得
        roster = request.form.get('roster')
        leader = request.form.get('leader')
        storein = request.form.get('storein')
        storeout = request.form.get('storeout')
        kyus = request.form.get('kyus')
        kyue = request.form.get('kyue')
        kotue = request.form.get('kotue')
        if kotue =="":
            kotue = 0
        kotuk = request.form.get('kotuk')
        if kotuk =="":
            kotuk = 0
        else:
            kotuk = int(kotuk)*80
        biko = request.form.get('biko')
        db = get_db()
        #idと紐付けて実績データ(storeDat)からデータ取得
        post = db.execute("select date,storeNo,kigyo,store from storeDat where id=?",(id,)).fetchone()
        #勤怠テーブルを更新
        db.execute("update kintai set roster=?,leader=?,storein=?,storeout=?,kyus=?,kyue=?,kotue=?,kotuk=?,biko=?  where Unum=?",[roster,leader,storein,storeout,kyus,kyue,kotue,kotuk,biko,Unum])
         #社員ﾏｽﾀ・実績・勤怠のデータ結合してIDを基にデータ取得
        kintai_list = db.execute("SELECT * FROM kintai JOIN user ON kintai.roster = user.roster JOIN storeDat ON kintai.datid = storeDat.id WHERE kintai.datid=?",(id,)) 
        db.commit()
        
        return render_template('kintaimain.html', id=id,post=post,kintai_list=kintai_list)
    
    #idと紐付けて実績データ(storeDat)からデータ取得
    post = get_db().execute("select date,storeNo,kigyo,store from storeDat where id=?",(id,)).fetchone()
    #社員ﾏｽﾀ・実績・勤怠のデータ結合してIDを基にデータ取得
    kintai_list = get_db().execute("SELECT * FROM kintai JOIN user ON kintai.roster = user.roster JOIN storeDat ON kintai.datid = storeDat.id WHERE kintai.datid=? and kintai.Unum=?",(id,Unum,)) 
    get_db().commit()
    return render_template('editk.html',kintai_list=kintai_list,post=post,id=id)

#削除
@app.route("/<id>/delete",methods=['GET','POST'])
@login_required
def delete(id):
    if request.method == 'POST':
        #画面からの登録情報取得
        db = get_db()
        db.execute("delete from  storeDat where id=?",[id])
        db.commit()
        return redirect('/')
    
    post = get_db().execute("select id,date,storeNo,kigyo,store from storeDat where id=?",(id,)).fetchone()
    return render_template('delete.html',post=post)

#削除　勤怠入力　未使用
@app.route("/<unum>/deletek",methods=['GET','POST'])
@login_required
def deletek(unum):
    if request.method == 'POST':
        #画面からの登録情報取得
        db = get_db()
        db.execute("delete from  kintai where unum=?",[unum])
        db.commit()
        return redirect('/')
    
    post = get_db().execute("select * from kintai where unum=?",(unum,)).fetchone()
    return render_template('deletek.html',post=post)

if __name__ == "__main__":
    app.run()

#database
def connect_db():
    rv = sqlite3.connect(DATABASE)
    rv.row_factory = sqlite3.Row
    return rv
def get_db():
    if not hasattr(g,'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db