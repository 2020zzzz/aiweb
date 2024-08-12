from flask import Flask, render_template, redirect, request, session, flash, jsonify, abort, make_response
from flask_bootstrap import Bootstrap
import sqlite3
from function import hash_code,image_to_binary,toRGB,is_grayscale
import os
from task.modeldetect import predict_image

app = Flask(__name__)
app.config['SECRET_KEY'] = 'nemo'
bootstrap = Bootstrap(app)

# 需要自己设置一个文件目录
app.config['UPLOAD_FOLDER'] = 'D:\\Graduation_thesis\\bishe\\testdata'


@app.route('/')
def index():
    if session.get('is_login'):
        if session.get('name') == 'admin':
            return render_template('index.html')
        else:
            return render_template('indexuser.html')
    else:
        return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # 获取请求中的数据
        username = request.form.get('username')
        password = hash_code(request.form.get('password'))

        # 连接数据库，判断用户名+密码组合是否匹配
        conn = sqlite3.connect('db.db')
        cur = conn.cursor()
        try:
            sql = 'SELECT 1 FROM USER WHERE USERNAME=? AND PASSWORD=?'
            is_valid_user = cur.execute(sql, (username, password)).fetchone()
        except:
            flash('用户名或密码错误！')
            # flash和它的名字一样，是闪现，意思就是我们的消息只会显示一次，当我们再次刷新也面的时候，它就不存在了
            # 而正是这点，它经常被用来显示一些提示消息，比如登陆之后，显示欢迎信息等
            return render_template('login.html')
        finally:
            conn.close()
        if is_valid_user:
            session['is_login'] = True
            session['name'] = username
            if username == 'admin':
                session['is_admin'] = True
            return redirect('/')
        else:
            flash('用户名或密码错误！')
            return render_template('login.html')
    return render_template('login.html')

# @app.route('evaluation.html')


@app.route('/user/list')
def user_list():
    if session.get('is_login'):
        # 从数据库中获取用户列表信息
        conn = sqlite3.connect('db.db')
        cur = conn.cursor()
        cur.execute('SELECT id, username, password, email, total, endtime, types, P FROM USER')
        users = [{'id': row[0], 'username': row[1], 'password': row[2], 'email': row[3], 'total': row[4], 'endtime': row[5], 'types': row[6], 'P': row[7]} for row in cur.fetchall()]
        conn.close()
        return render_template('user_list.html', users=users)
    else:
        flash('请先登录！')
        return redirect('/login')


@app.route('/user/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        # 处理提交新增用户信息的逻辑
        username = request.form.get('username', '').strip()
        password = request.form.get('password')
        email = request.form.get('email')
        if username and password:
            # 连接数据库，插入新增用户信息
            conn = sqlite3.connect('db.db')
            cur = conn.cursor()
            cur.execute('INSERT INTO USER(USERNAME, PASSWORD, EMAIL) VALUES (?, ?, ?)', (username, hash_code(password),email))
            conn.commit()
            conn.close()
            flash('用户添加成功！')
            return redirect('/user/list')
        else:
            flash('用户名和密码不能为空！')
            return redirect('/user/add')  # 返回新增用户页面，重新填写信息
    else:
        # 渲染新增用户表单页面
        return render_template('add_user.html')


@app.route('/user/delete/<int:user_id>')
def delete_user(user_id):
    if session.get('is_login'):
        conn = sqlite3.connect('db.db')
        cur = conn.cursor()
        cur.execute('DELETE FROM USER WHERE id = ?', (user_id,))
        conn.commit()
        conn.close()
        flash('用户删除成功！')
        return redirect('/user/list')
    else:
        flash('请先登录！')
        return redirect('/login')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password')
        email = request.form.get('email')
        confirm_password = request.form.get('confirm')
        if username and password and confirm_password:
            if password != confirm_password:
                flash('两次输入的密码不一致！')
                return render_template('register.html', username=username)
            # 连接数据库
            conn = sqlite3.connect('db.db')
            cur = conn.cursor()
            # 查询输入的用户名是否已经存在
            sql_same_user = 'SELECT 1 FROM USER WHERE USERNAME=?'
            same_user = cur.execute(sql_same_user, (username,)).fetchone()
            if same_user:
                flash('用户名已存在！')
                return render_template('register.html', username=username)
            # 通过检查的数据，插入数据库表中
            sql_insert_user = 'INSERT INTO USER(USERNAME, PASSWORD, EMAIL) VALUES (?,?,?)'
            cur.execute(sql_insert_user, (username, hash_code(password), email))
            conn.commit()
            conn.close()
            # 重定向到登录页面
            return redirect('/login')
        else:
            flash('所有字段都必须输入！')
            if username:
                return render_template('register.html', username=username)
            return render_template('register.html')
    return render_template('register.html')


@app.route('/logout')
def logout():
    # 退出登录，清空session
    if session.get('is_login'):
        session.clear()
        return redirect('/')
    return redirect('/')


@app.route('/api/adduser', methods=['GET', 'POST'])
def add_user():
    if request.json:
        username = request.json.get('username', '').strip()
        password = request.json.get('password')
        email = request.json.get('email')
        confirm_password = request.json.get('confirm')
        # 判断所有输入都不为空
        if username and password and confirm_password:
            if password != confirm_password:
                return jsonify({'code': '400', 'msg': '两次密码不匹配！'}), 400
            # 连接数据  库
            conn = sqlite3.connect('db.db')
            cur = conn.cursor()
            # 查询输入的用户名是否已经存在
            sql_same_user = 'SELECT 1 FROM USER WHERE USERNAME=?'
            same_user = cur.execute(sql_same_user, (username,)).fetchone()
            if same_user:
                return jsonify({'code': '400', 'msg': '用户名已存在'}), 400
            # 通过检查的数据，插入数据库表中
            sql_insert_user = 'INSERT INTO USER(USERNAME, PASSWORD, EMAIL) VALUES (?,?,?)'
            cur.execute(sql_insert_user, (username, hash_code(password),email))
            conn.commit()
            sql_new_user = 'SELECT id,username FROM USER WHERE USERNAME=?'
            user_id, user = cur.execute(sql_new_user, (username,)).fetchone()
            conn.close()
            return jsonify({'code': '200', 'msg': '账号生成成功！', 'newUser': {'id': user_id, 'user': user}})
        else:

            return jsonify({'code': '404', 'msg': '请求参数不全!'})
    else:
        abort(400)


@app.route('/api/testjson', methods=['GET', 'POST'])
def test_json():
    if 'x' in request.json:
        print(request.json)
        return jsonify(request.json)
    else:
        abort(400)


@app.route('/api/mock', methods=['GET', 'POST'])
def mock():
    if request.method == 'GET':
        res = []
        for arg in request.args.items():
            res.append(arg)
        res = dict(res)
        return jsonify(res)
    elif request.method == 'POST':
        return jsonify(request.json)


@app.route('/profile', methods=['GET'])
def profile():
    if session.get('is_login'):
        return render_template('profile.html')
    else:
        flash('请先登录！')
        return redirect('/login')

@app.route('/evaluation')
def evaluation():
    if session.get('is_login'):
        return render_template('evaluation.html')
    else:
        flash('请先登录！')
        return redirect('/login')


@app.route('/profile/update', methods=['POST'])
def update_profile():
    if session.get('is_login'):
        username = session['name']
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        new_email = request.form.get('new_email')

        if new_password != confirm_password:
            flash('两次输入的密码不一致！')
            return redirect('/profile')

        # 连接数据库，更新密码
        conn = sqlite3.connect('db.db')
        cur = conn.cursor()
        try:
            sql_update_password = 'UPDATE USER SET PASSWORD=?, `EMAIL`=? WHERE USERNAME=?'
            cur.execute(sql_update_password, (hash_code(new_password), new_email, username))
            conn.commit()
            flash('个人资料更新成功！')
        except Exception as e:
            flash('个人资料更新失败！')
            print(e)  # 可以将异常信息记录到日志中
        finally:
            conn.close()
            return redirect('/profile')
    else:
        flash('请先登录！')
        return redirect('/login')

import datetime
@app.route('/upload', methods=['POST'])
def upload_file():
    if session.get('is_login'):
        if 'file' not in request.files:
            flash('没有文件被上传')
            return redirect(request.url)

        file = request.files['file']

        if file.filename == '':
            flash('未选择文件')
            return redirect(request.url)

        if file.filename.endswith('.txt'):
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(file_path)
            upp = predict_image(toRGB(file_path))
            flash('已生成 RGB 图像文件：rgb.png')
            if len(upp) == 0:
                flash('这是一个非恶意文件')
            else:
                sstr = '这是一个恶意文件，恶意类型是：' + str(upp[0]) +'。恶意的概率为：'+ str(upp[1])
                flash(sstr)
                conn = sqlite3.connect('db.db')
                cur = conn.cursor()
                try:
                    cur.execute('UPDATE USER SET total = total + 1 WHERE USERNAME = ?', (session['name'],))
                    cur.execute('UPDATE USER SET endtime = ? WHERE USERNAME = ?', (datetime.datetime.now(), session['name']))
                    cur.execute('UPDATE USER SET types = ? WHERE USERNAME = ?', (str(upp[0]), session['name']))
                    cur.execute('UPDATE USER SET P = ? WHERE USERNAME = ?', (str(upp[1]), session['name']))
                    conn.commit()
                except Exception as e:
                    # Handle exceptions
                    flash('更新数据库时出现错误')
                    print(e)  # Log the exception
                finally:
                    conn.close()
        elif file.filename.endswith(('.jpg', '.png')):
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(file_path)
            if is_grayscale(file_path):
                patth = image_to_binary(file_path)
                upp = predict_image(toRGB(patth))
                if len(upp) == 0:
                    flash('这是一个非恶意文件')
                    conn = sqlite3.connect('db.db')
                    cur = conn.cursor()
                    try:
                        cur.execute('UPDATE USER SET total = total + 1 WHERE USERNAME = ?', (session['name'],))
                        cur.execute('UPDATE USER SET endtime = ? WHERE USERNAME = ?', (datetime.datetime.now(), session['name']))
                        cur.execute('UPDATE USER SET types = ? WHERE USERNAME = ?', ("非恶意", session['name']))
                        cur.execute('UPDATE USER SET P = ? WHERE USERNAME = ?', (None, session['name']))
                        conn.commit()
                    except Exception as e:
                        # Handle exceptions
                        flash('更新数据库时出现错误')
                        print(e)  # Log the exception
                    finally:
                        conn.close()
                else:
                    sstr = '这是一个恶意文件，恶意类型是：' + str(upp[0]) + '。恶意的概率为：' + str(upp[1])
                    flash(sstr)
                    conn = sqlite3.connect('db.db')
                    cur = conn.cursor()
                    try:
                        cur.execute('UPDATE USER SET total = total + 1 WHERE USERNAME = ?', (session['name'],))
                        cur.execute('UPDATE USER SET endtime = ? WHERE USERNAME = ?', (datetime.datetime.now(), session['name']))
                        cur.execute('UPDATE USER SET types = ? WHERE USERNAME = ?', (str(upp[0]), session['name']))
                        cur.execute('UPDATE USER SET P = ? WHERE USERNAME = ?', (str(upp[1]), session['name']))
                        conn.commit()
                    except Exception as e:
                        # Handle exceptions
                        flash('更新数据库时出现错误')
                        print(e)  # Log the exception
                    finally:
                        conn.close()
            else:
                upp = predict_image(file_path)
                if len(upp) == 0:
                    flash('这是一个非恶意文件')
                    conn = sqlite3.connect('db.db')
                    cur = conn.cursor()
                    try:
                        cur.execute('UPDATE USER SET total = total + 1 WHERE USERNAME = ?', (session['name'],))
                        cur.execute('UPDATE USER SET endtime = ? WHERE USERNAME = ?', (datetime.datetime.now(), session['name']))
                        cur.execute('UPDATE USER SET types = ? WHERE USERNAME = ?', ("非恶意", session['name']))
                        cur.execute('UPDATE USER SET P = ? WHERE USERNAME = ?', (None, session['name']))
                        conn.commit()
                    except Exception as e:
                        # Handle exceptions
                        flash('更新数据库时出现错误')
                        print(e)  # Log the exception
                    finally:
                        conn.close()
                else:
                    sstr = '这是一个恶意文件，恶意类型是：' + str(upp[0]) + '。恶意的概率为：' + str(upp[1])
                    flash(sstr)
                    conn = sqlite3.connect('db.db')
                    cur = conn.cursor()
                    try:
                        cur.execute('UPDATE USER SET total = total + 1 WHERE USERNAME = ?', (session['name'],))
                        cur.execute('UPDATE USER SET endtime = ? WHERE USERNAME = ?', (datetime.datetime.now(), session['name']))
                        cur.execute('UPDATE USER SET types = ? WHERE USERNAME = ?', (str(upp[0]), session['name']))
                        cur.execute('UPDATE USER SET P = ? WHERE USERNAME = ?', (str(upp[1]), session['name']))
                        conn.commit()
                    except Exception as e:
                        # Handle exceptions
                        flash('更新数据库时出现错误')
                        print(e)  # Log the exception
                    finally:
                        conn.close()
        else:
            flash('不支持的文件类型')
            return redirect(request.url)

        flash('文件上传成功')
        return redirect('/')
    else:
        flash('请先登录！')
        return redirect('/login')


if __name__ == '__main__':
    app.run(debug=True)
