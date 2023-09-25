from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from sqlalchemy import inspect

from config import app, database
from database import User, Group, Statement, Subject, Point, PointData, Program, Report


class UserView(ModelView):
    column_list = [c_attr.key for c_attr in inspect(User).mapper.column_attrs]


def config():
    admin = Admin(app, name=app.name, template_mode="bootstrap4")
    admin.add_view(UserView(User, database.session, "Пользователи"))
    admin.add_view(ModelView(Group, database.session, "Группы"))
    admin.add_view(ModelView(Statement, database.session, "Ведомости"))
    admin.add_view(ModelView(Subject, database.session, "Предметы"))
    admin.add_view(ModelView(Point, database.session, "КТ"))
    admin.add_view(ModelView(PointData, database.session, "Оценки"))
    admin.add_view(ModelView(Program, database.session, "Программы"))
    admin.add_view(ModelView(Report, database.session, "Отчеты"))
