import os
import uuid

import datetime as datetime
from flask import render_template, request, redirect, send_file
from flask_login import LoginManager, login_required, login_user, current_user, logout_user

from admin import config
from config import app, database
from database import User, save, Role, get_all, Group, Statement, find_by_id, Subject, Point, PointData, \
    PointDataStatus, Remark, \
    Program, Report
from util import get_file_extension

login_manager = LoginManager(app)
login_manager.login_view = "/login"


@login_manager.user_loader
def load_user(user_id):
    return database.session.query(User).get(user_id)


@app.get("/logout")
@login_required
def logout():
    logout_user()
    return show_login_form()


@app.route("/point_data/<point_data_id>/<file_type>/download")
def get_point_data_program_file(point_data_id, file_type):
    if file_type == "program_file":
        return send_file(
            app.config["UPLOAD_FOLDER"] + "/" + find_by_id(PointData, point_data_id).get_last_program().filename,
            as_attachment=True)
    if file_type == "report_file":
        return send_file(
            app.config["UPLOAD_FOLDER"] + "/" + find_by_id(PointData, point_data_id).get_last_report().filename,
            as_attachment=True)


@app.post("/point_data/<point_data_id>/<grade_type>/add")
@login_required
def add_grade_to_point_data(point_data_id, grade_type):
    point_data = find_by_id(PointData, point_data_id)
    grade = request.form.get("grade")
    if grade_type == "program_grade":
        point_data.program_grade = grade
        program = point_data.get_last_program()
        if grade == "-" or grade == "2":
            program.status = PointDataStatus.DECLINED
        elif grade == "+" or grade == "3" or grade == "4" or grade == "5":
            program.status = PointDataStatus.ACCEPTED
        else:
            program.status = PointDataStatus.PENDING
        save(program)
    if grade_type == "report_grade":
        point_data.report_grade = request.form.get("grade")
        report = point_data.get_last_report()
        if grade == "-" or grade == "2":
            report.status = PointDataStatus.DECLINED
        elif grade == "+" or grade == "3" or grade == "4" or grade == "5":
            report.status = PointDataStatus.ACCEPTED
        else:
            report.status = PointDataStatus.PENDING
        save(report)
    save(point_data)
    return show_statement_page(point_data.point.statement_id)




@app.post("/point_data/<point_data_id>/remarks/add")
@login_required
def add_point_data_remark(point_data_id):
    point_data = find_by_id(PointData, point_data_id)
    remark_type = request.form.get("remark_type")
    remark = Remark(text=request.form.get("text"), datetime=datetime.datetime.now(), type=remark_type,
                    author_id=current_user.id)
    point_data.remarks.append(remark)
    save(point_data)
    return show_statement_page(point_data.point.statement_id)


@app.post("/point/<point_id>/data/upload")
@login_required
def upload_file(point_id):
    program_file = request.files["program_file"]
    report_file = request.files["report_file"]
    point = find_by_id(Point, point_id)
    point_data = point.find_point_data_by_user_id(current_user.id)
    if point_data is None:
        point_data = PointData(point_id=point_id, user_id=current_user.id)
    if program_file:
        if program_file.filename == "":
            return redirect(request.url)
        filename = f"{str(uuid.uuid4())}.{get_file_extension(program_file.filename)}"
        program_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        point_data.programs.append(Program(filename=filename, datetime=datetime.datetime.now()))
    if report_file:
        if report_file.filename == "":
            return redirect(request.url)
        filename = f"{str(uuid.uuid4())}.{get_file_extension(report_file.filename)}"
        report_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        point_data.reports.append(Report(filename=filename, datetime=datetime.datetime.now()))
    save(point_data)
    return show_statement_page(point.statement_id)


@app.post("/statement/<statement_id>/groups/add")
@login_required
def add_statement_group(statement_id):
    statement = find_by_id(Statement, statement_id)
    group = find_by_id(Group, request.form.get("group_id"))
    statement.groups.append(group)
    save(statement)
    return show_statement_page(statement_id)


@app.post("/statement/<statement_id>/points/add")
@login_required
def add_statement_point(statement_id):
    statement = find_by_id(Statement, statement_id)
    point = Point(name=request.form.get("name"))
    statement.points.append(point)
    save(statement)
    return show_statement_page(statement_id)


@app.get("/statement/<statement_id>")
@login_required
def show_statement_page(statement_id):
    return render_template("statement.html", groups=get_all(Group),
                           statement=find_by_id(Statement, statement_id), subjects=get_all(Subject))


@app.post("/statement/add")
@login_required
def add_statement():
    statement = Statement(semester=request.form.get("semester"), year=request.form.get("year").split("-")[0],
                          subject_id=request.form.get("subject_id"))
    save(statement)
    return index(message="Ведомость успешно добавлена.")


@app.get("/")
@login_required
def index(message=None):
    return render_template("index.html",
                           message=message, statements=get_all(Statement), subjects=get_all(Subject))


@app.post("/login")
def login():
    if current_user.is_authenticated:
        return index()
    else:
        email = request.form.get("email")
        password = request.form.get("password")
        user = database.session.query(User).filter(User.email == email).first()
        if user and user.check_password(password):
            login_user(user, remember=True)
            return index()
        else:
            return show_login_form(message="Ошибка авторизации")


@app.post("/registration")
def registration():
    if current_user.is_authenticated:
        return index()
    else:
        email = request.form.get("email")
        if database.session.query(User).filter(User.email == email).first():
            return show_login_form(message="Пользователь с такой почтой уже зарегистрирован")
        else:
            first_name = request.form.get("first_name")
            last_name = request.form.get("last_name")
            middle_name = request.form.get("middle_name")
            group_id = request.form.get("group_id")
            password = request.form.get("password")
            password_again = request.form.get("password")
            if password_again != password:
                return show_login_form(message="Пароли не совпадают")
            role = request.form.get("role")
            user = User(email=email, first_name=first_name, last_name=last_name, middle_name=middle_name,
                        role=Role.get_role(role), group_id=group_id)
            user.set_password(password)
            save(user)
            login_user(user, remember=True)
            return index()


@app.route("/login")
def show_login_form(message=None):
    return render_template("login.html", groups=get_all(Group), message=message, roles=Role.get_roles())


if __name__ == "__main__":
    app.app_context().push()
    config()
    database.create_all()
    app.run()
